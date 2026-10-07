"""CMYK separation, screening, layer SVGs, and per-ink cost analysis."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover - the core tests do not need Qt
    HAVE_QT = False


def svg_groups(root):
    """Return the data-ink groups (the SVG root also ends in 'g')."""
    return [
        element.get("data-ink")
        for element in root.iter()
        if element.tag.split("}")[-1] == "g"
    ]


class SeparationTests(unittest.TestCase):
    def test_white_needs_no_ink(self):
        import numpy as np

        tones = converter.rgb_to_cmyk_tone(np.ones((2, 2, 3), dtype="float32"))
        for channel in converter.CHANNELS:
            self.assertLess(float(tones[channel].max()), 1e-6)

    def test_black_moves_into_k_with_gcr(self):
        import numpy as np

        tones = converter.rgb_to_cmyk_tone(
            np.zeros((1, 1, 3), dtype="float32"), weights=(1, 1, 1, 1)
        )
        self.assertAlmostEqual(float(tones["k"][0, 0]), 1.0, places=5)
        for channel in ("c", "m", "y"):
            self.assertAlmostEqual(float(tones[channel][0, 0]), 0.0, places=5)

    def test_pure_cyan_stays_in_c(self):
        import numpy as np

        pixel = np.array([[[0.0, 1.0, 1.0]]], dtype="float32")
        tones = converter.rgb_to_cmyk_tone(pixel)
        self.assertAlmostEqual(float(tones["c"][0, 0]), 1.0, places=5)
        self.assertAlmostEqual(float(tones["k"][0, 0]), 0.0, places=5)

    def test_gcr_zero_keeps_the_gray_in_cmy(self):
        import numpy as np

        gray = np.full((1, 1, 3), 0.5, dtype="float32")
        tones = converter.rgb_to_cmyk_tone(gray, gcr=0.0, weights=(1, 1, 1, 1))
        self.assertAlmostEqual(float(tones["k"][0, 0]), 0.0, places=5)
        for channel in ("c", "m", "y"):
            self.assertAlmostEqual(float(tones[channel][0, 0]), 0.5, places=5)

    def test_weights_and_gamma_shape_the_ink(self):
        import numpy as np

        gray = np.full((1, 1, 3), 0.5, dtype="float32")
        tones = converter.rgb_to_cmyk_tone(
            gray, gcr=0.0, weights=(0.0, 1.0, 1.0, 1.0), gamma=2.0
        )
        self.assertAlmostEqual(float(tones["c"][0, 0]), 0.0, places=6)
        self.assertAlmostEqual(float(tones["m"][0, 0]), 0.25, places=5)


class ScreeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np

        cls.np = np

    def geometry(self, width=100.0, height=100.0):
        return {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": width,
            "height_mm": height,
            "pixels_w": 32,
            "pixels_h": 32,
        }

    def test_halftone_marks_follow_tone(self):
        white = self.np.zeros((32, 32), dtype="float32")
        self.assertEqual(
            converter.screen_channel(white, self.geometry(), spacing_mm=4.0), []
        )
        gray = self.np.full((32, 32), 0.6, dtype="float32")
        marks = converter.screen_channel(gray, self.geometry(), spacing_mm=4.0)
        self.assertGreater(len(marks), 100)
        self.assertEqual(len(marks[0]), 9)  # closed 8-step circle

    def test_mark_cap_grows_the_pitch(self):
        dark = self.np.full((32, 32), 0.9, dtype="float32")
        marks = converter.screen_channel(
            dark, self.geometry(), spacing_mm=1.0, max_marks=300
        )
        self.assertLessEqual(len(marks), 360)
        self.assertGreater(len(marks), 100)

    def test_stipple_style_drops_marks_on_paper(self):
        half = self.np.full((32, 32), 0.5, dtype="float32")
        stipple = converter.screen_channel(
            half, self.geometry(), style="stipple", spacing_mm=5.0, seed=3
        )
        blank = converter.screen_channel(
            self.np.zeros((32, 32), dtype="float32"),
            self.geometry(),
            style="stipple",
            spacing_mm=5.0,
            seed=3,
        )
        self.assertEqual(blank, [])
        self.assertGreater(len(stipple), 20)

    def test_line_screen_breaks_in_white(self):
        dark = self.np.full((32, 32), 0.7, dtype="float32")
        lines = converter.screen_channel(
            dark, self.geometry(), style="lines", spacing_mm=4.0
        )
        self.assertGreater(len(lines), 5)
        self.assertTrue(all(len(line) > 2 for line in lines))
        self.assertEqual(
            converter.screen_channel(
                self.np.zeros((32, 32), dtype="float32"),
                self.geometry(),
                style="lines",
                spacing_mm=4.0,
            ),
            [],
        )

    def test_crosshatch_levels_and_overdraw(self):
        dark = self.np.full((32, 32), 0.8, dtype="float32")
        two = converter.screen_channel(
            dark, self.geometry(), style="crosshatch", spacing_mm=4.0, levels=2
        )
        four = converter.screen_channel(
            dark, self.geometry(), style="crosshatch", spacing_mm=4.0, levels=4
        )
        self.assertGreater(len(four), len(two))
        doubled = converter.screen_channel(
            dark,
            self.geometry(),
            style="crosshatch",
            spacing_mm=4.0,
            levels=4,
            overdraw=2,
        )
        self.assertEqual(len(doubled), 2 * len(four))

    def test_wave_gyroid_and_tsp_styles(self):
        dark = self.np.full((32, 32), 0.6, dtype="float32")
        waves = converter.screen_channel(
            dark, self.geometry(), style="waves", spacing_mm=4.0
        )
        self.assertGreater(len(waves), 3)
        gyroid = converter.screen_channel(
            dark, self.geometry(), style="gyroid", spacing_mm=4.0
        )
        self.assertGreater(len(gyroid), 3)
        tsp = converter.screen_channel(
            dark, self.geometry(), style="tsp", spacing_mm=4.0, seed=1
        )
        self.assertEqual(len(tsp), 1)
        self.assertGreater(len(tsp[0]), 10)

    def test_contours_need_a_gradient(self):
        ramp = self.np.tile(
            self.np.linspace(0.0, 1.0, 32, dtype="float32"), (32, 1)
        )
        contours = converter.screen_channel(
            ramp, self.geometry(), style="contours", spacing_mm=4.0
        )
        self.assertGreater(len(contours), 3)
        flat = self.np.full((32, 32), 0.8, dtype="float32")
        self.assertEqual(
            converter.screen_channel(
                flat, self.geometry(), style="contours", spacing_mm=4.0
            ),
            [],
        )

    def test_svg_document_groups_and_order(self):
        polyline = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
        document = converter.svg_document(
            {"c": [polyline], "k": [polyline]}, 50.0, 50.0, order=["c", "k"]
        )
        root = ET.fromstring(document)
        groups = [
            element
            for element in root.iter()
            if element.tag.split("}")[-1] == "g"
        ]
        self.assertEqual([group.get("data-ink") for group in groups], ["c", "k"])
        self.assertEqual(
            [group.get("stroke") for group in groups],
            [converter.CHANNEL_COLORS["c"], converter.CHANNEL_COLORS["k"]],
        )

    def test_ink_tags_survive_the_geometry_pipeline(self):
        tagged = converter.tag_ink(
            [[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]], "c"
        )
        moved = converter.apply_geometry_settings(tagged, converter.Settings())
        self.assertEqual(getattr(moved[0], "ink", None), "c")
        clipped = converter.clip_contours_to_bed(moved, (10.0, 0.0), 3.0)
        self.assertTrue(clipped)
        self.assertTrue(all(getattr(c, "ink", None) == "c" for c in clipped))

    def test_cost_table_names_both_strategies(self):
        from generator_tabs.cmyk_tab import format_seconds, format_cost_table

        rows = {
            "c": {
                "marks": 10,
                "moves": 42,
                "x_count": 30,
                "y_count": 12,
                "draw_mm": 100.0,
                "seconds": 61.0,
            }
        }
        table = format_cost_table(rows)
        self.assertIn("x_theta", table)
        self.assertIn("y_theta", table)
        self.assertIn("Cyan", table)
        self.assertEqual(format_seconds(61.0), "1m01s")
        self.assertEqual(format_seconds(3600.0), "1h00m")


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class CmykTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from generator_tabs.cmyk_tab import CmykTab

        cls.CmykTab = CmykTab
        cls.app = QApplication.instance() or QApplication([])
        folder = tempfile.mkdtemp(prefix="cmyk-tab-")
        cls.folder = folder
        from PIL import Image

        image = Image.new("RGB", (48, 48), (255, 255, 255))
        for x in range(12, 36):
            for y in range(12, 36):
                image.putpixel((x, y), (0, 0, 0))
        cls.image_path = str(Path(folder) / "art.png")
        image.save(cls.image_path)

    def make_tab(self, host=None):
        host = host or FakeHost(self.image_path)
        tab = self.CmykTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(60)
        tab.page_h.setValue(60)
        tab.margin.setValue(4)
        tab.pitch.setValue(4.0)
        tab.max_marks.setValue(400)
        return tab

    def test_build_svg_writes_the_visible_layers(self):
        tab = self.make_tab()
        path = tab.build_svg()
        root = ET.parse(path).getroot()
        self.assertEqual(svg_groups(root), list(converter.CHANNELS))
        tab.preview_boxes["k"].setChecked(False)
        path = tab.build_svg()
        root = ET.parse(path).getroot()
        self.assertEqual(svg_groups(root), ["c", "m", "y"])

    def test_preview_requires_one_layer(self):
        tab = self.make_tab()
        for box in tab.preview_boxes.values():
            box.setChecked(False)
        with self.assertRaises(ValueError):
            tab.build_svg()

    def test_every_screen_style_builds_all_four_layers(self):
        tab = self.make_tab()
        tab.levels.setValue(3)
        tab.overdraw.setValue(2)
        for style in ("halftone", "stipple", "lines", "crosshatch", "waves", "gyroid", "tsp", "contours"):
            tab.style.setCurrentIndex(tab.style.findData(style))
            root = ET.parse(tab.build_svg()).getroot()
            self.assertEqual(svg_groups(root), list(converter.CHANNELS), style)

    def test_analysis_worker_reports_strategy_split(self):
        from generator_tabs.cmyk_tab import ProgramAnalysisWorker

        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._ensure_layers()
        results = {}
        worker = ProgramAnalysisWorker(
            host,
            converter.Settings(),
            converter.DEFAULT_MOTION_ESTIMATE_SCALE,
            [("k", tab._layer_files["k"])],
        )
        worker.finished.connect(results.update)
        worker.run()
        record = results["k"]
        self.assertEqual(record["x_count"], 2)
        self.assertEqual(record["y_count"], 1)
        self.assertEqual(record["marks"], 2)
        self.assertGreater(record["seconds"], 0.0)

    def test_save_writes_one_file_per_ink(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._ensure_layers()
        results = {
            channel: {
                "marks": 1,
                "moves": 3,
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "x_count": 1,
                "y_count": 0,
                "x_mm": 1.0,
                "y_mm": 0.0,
                "draw_mm": 1.0,
                "seconds": 1.0,
            }
            for channel in converter.CHANNELS
        }
        tab._analysis = results
        tab._analysis_key = tab._control_key()
        tab._write_files(results)
        self.assertEqual(host.saved_labels, ["cyan", "magenta", "yellow", "black"])
        for channel in converter.CHANNELS:
            self.assertTrue(
                Path(host.saved_paths[converter.CHANNEL_LABELS[channel].lower()]).exists()
            )

    def test_preview_layers_match_the_visible_checkboxes(self):
        tab = self.make_tab()
        tab.build_svg()
        self.assertEqual(
            [ink for ink, _path in tab.preview_layers()], list(converter.CHANNELS)
        )
        tab.preview_boxes["m"].setChecked(False)
        tab.build_svg()
        self.assertEqual(
            [ink for ink, _path in tab.preview_layers()], ["c", "y", "k"]
        )


class FakeHost:
    """Minimal host: analysis is synthetic, saving writes real temp files."""

    def __init__(self, artwork):
        self._artwork = artwork
        self.status = []
        self.log = []
        self.saved_labels = []
        self.saved_paths = {}
        self._folder = tempfile.mkdtemp(prefix="cmyk-save-")

    def artwork_path(self):
        return self._artwork

    def generator_status(self, message):
        self.status.append(message)

    def settings_for_source(self, _tab):
        return converter.Settings()

    def motion_estimate_scale(self):
        return converter.DEFAULT_MOTION_ESTIMATE_SCALE

    def analyze_program(self, _path, _settings, cancel_check=None):
        moves = [
            {
                "type": "draw",
                "strategy": "x_theta",
                "motion_length": 2.0,
                "duration_ms": 1000.0,
            },
            {
                "type": "draw",
                "strategy": "x_theta",
                "motion_length": 2.0,
                "duration_ms": 1000.0,
            },
            {
                "type": "draw",
                "strategy": "y_theta",
                "motion_length": 1.0,
                "duration_ms": 500.0,
            },
            {"type": "pen_down", "duration_ms": 600.0},
        ]
        return {
            "contours": [[(0.0, 0.0), (1.0, 1.0)], [(1.0, 1.0), (2.0, 2.0)]],
            "moves": moves,
            "gcode": "; synthetic\nG1 X0 Y0\n",
            "stats": {},
        }

    def export_program_set(self, entries, base_path=None, default_base=""):
        del base_path, default_base
        written = []
        for label, gcode in entries:
            path = str(Path(self._folder) / f"art-cmyk-{label}.gcode")
            Path(path).write_text(gcode, encoding="utf-8")
            self.saved_labels.append(label)
            self.saved_paths[label] = path
            written.append(path)
        return written


if __name__ == "__main__":
    unittest.main()
