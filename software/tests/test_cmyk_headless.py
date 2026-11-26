"""Headless CMYK export through the real tab and application host."""

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


def _load_headless_module():
    path = ROOT / "tools" / "export_cmyk_headless.py"
    spec = importlib.util.spec_from_file_location(
        "export_cmyk_headless_test",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class CmykHeadlessExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PIL import Image

        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_headless_module()
        cls.temp_dir = tempfile.TemporaryDirectory(prefix="cmyk-headless-test-")
        root = Path(cls.temp_dir.name)
        cls.source = root / "fixture.png"
        image = Image.new("RGB", (96, 96), (236, 185, 108))
        for x in range(12, 84):
            for y in range(10, 55):
                image.putpixel((x, y), (76, 42, 28))
        for x in range(18, 78):
            for y in range(60, 88):
                image.putpixel((x, y), (42, 116, 174))
        image.save(cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_export_uses_cmyk_tab_and_publishes_the_complete_set(self):
        from PIL import Image

        with tempfile.TemporaryDirectory(prefix="cmyk-set-output-") as folder:
            output = Path(folder)
            options = self.module.ExportOptions(
                source=self.source,
                output_dir=output,
                base_name="fixture-cmyk",
                recipe="process_area",
                page_mm=50.0,
                margin_mm=2.0,
                scale_pct=100.0,
                pen_width_mm=0.9,
                pitch_mm=0.35,
                path_tolerance_mm=0.05,
                max_marks=20_000,
                seed=7,
                timeout_seconds=180.0,
                determinism_repeat=False,
                preview=True,
                reference_image=None,
            )
            report = self.module.run_headless_export(options)

            expected = [
                output / "fixture-cmyk-01-yellow.gcode",
                output / "fixture-cmyk-02-magenta.gcode",
                output / "fixture-cmyk-03-cyan.gcode",
                output / "fixture-cmyk-04-black.gcode",
                output / "fixture-cmyk-set.json",
                output / "fixture-cmyk-comparison.jpg",
                output / "fixture-cmyk-verification.json",
            ]
            self.assertTrue(all(path.is_file() for path in expected))
            manifest = json.loads(
                (output / "fixture-cmyk-set.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["version"], 8)
            self.assertEqual(
                manifest["print_order"],
                ["01-yellow", "02-magenta", "03-cyan", "04-black"],
            )
            self.assertTrue(manifest["set_verification"]["complete"])
            self.assertTrue(
                manifest["set_verification"]["whole_set_transaction"]
            )
            self.assertEqual(
                report["status"],
                "passed",
            )
            self.assertEqual(
                report["comparison"]["process_style"],
                "process_area",
            )
            self.assertEqual(
                report["comparison"]["coherent_style"],
                "edge_flow_coherent",
            )
            self.assertTrue(report["comparison"]["matching_controls"])
            controls = report["comparison"]["contract"]
            self.assertEqual(controls["page_mm"], [50.0, 50.0])
            self.assertEqual(controls["margin_mm"], 2.0)
            self.assertEqual(controls["artwork_placement_mm"], [0.0, 0.0])
            self.assertTrue(controls["registration_marks"])
            self.assertTrue(controls["bed_compensation_path"].endswith(".json"))
            self.assertEqual(
                controls["write_order"],
                ["01-yellow", "02-magenta", "03-cyan", "04-black"],
            )
            self.assertEqual(
                controls["image_controls"]["weights_pct"],
                {"c": 100.0, "m": 100.0, "y": 100.0, "k": 100.0},
            )
            self.assertFalse(controls["image_controls"]["auto_levels"])
            self.assertGreater(
                report["recipe"]["effective_pitch_mm"],
                report["recipe"]["requested_pitch_mm"],
            )
            for channel in ("y", "m", "c", "k"):
                self.assertGreater(report["programs"][channel]["mark_count"], 0)
                self.assertLessEqual(
                    report["programs"][channel]["max_xy_radius_mm"],
                    manifest["preflight"][channel][
                        "machine_reach_radius_mm"
                    ],
                )
            with Image.open(output / "fixture-cmyk-comparison.jpg") as preview:
                self.assertEqual(preview.format, "JPEG")
            self.assertLessEqual(
                (output / "fixture-cmyk-comparison.jpg").stat().st_size,
                self.module.MAX_PREVIEW_BYTES,
            )

    def test_page_bounds_reject_overflow(self):
        layers = {
            channel: [[(10.0, 10.0), (40.0, 40.0)]]
            for channel in ("y", "m", "c", "k")
        }
        layers["m"] = [[(-0.01, 10.0), (40.0, 40.0)]]
        with self.assertRaisesRegex(
            self.module.HeadlessExportError,
            "exceeds the 50 x 50 mm page",
        ):
            self.module._layer_bounds(layers, 50.0, 50.0)

    def test_machine_bounds_ignore_the_final_g53_park(self):
        gcode = (
            "G21\nG90\nG54\n"
            "G1 X3 Y4 A0 F700\n"
            "G1 X-3 Y10 A0 F700\n"
            "G53 G1 X-10 Y-436 F3000\n"
            "M2\n"
        )
        bounds = self.module._machine_bounds(gcode)
        self.assertAlmostEqual(bounds["max_radius_mm"], 10.4403065089)
        self.assertEqual(bounds["xy_moves"], 2)

    def test_render_layers_uses_cmyk_ink_identities_not_print_order(self):
        factors = self.module.converter.ink_transmittance_matrix()
        for index, channel in enumerate(self.module.converter.CHANNELS):
            layers = {
                name: (
                    [[(0.0, 50.0), (100.0, 50.0)]]
                    if name == channel
                    else []
                )
                for name in self.module.converter.CHANNELS
            }
            rendered = self.module._render_layers(
                layers,
                100.0,
                100.0,
                10.0,
                None,
                pixels=100,
            )
            expected = tuple(
                round(float(component) * 255.0)
                for component in factors[index]
            )
            actual = rendered.getpixel((50, 50))
            for observed, wanted in zip(actual, expected):
                self.assertLessEqual(abs(observed - wanted), 1)

    def test_source_comparison_panel_uses_the_gcode_page_margin(self):
        from PIL import Image

        source = Image.new("RGB", (100, 100), (220, 120, 60))
        panel = self.module._page_source_panel(
            source,
            page_width_mm=100.0,
            page_height_mm=100.0,
            margin_mm=10.0,
            size=100,
        )
        self.assertEqual(panel.getpixel((2, 50)), (255, 255, 255))
        center = panel.getpixel((50, 50))
        for observed, expected in zip(center, (220, 120, 60)):
            self.assertLessEqual(abs(observed - expected), 1)


if __name__ == "__main__":
    unittest.main()
