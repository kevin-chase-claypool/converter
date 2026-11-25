"""Plotterfun CMYK SVG layers convert to four registered G-code programs."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter
from generator_tabs._plotterfun_cmyk import write_cmyk_svg_set
from generator_tabs._plotterfun_gcode import (
    planned_gcode_paths,
    write_plotterfun_gcode_set,
)


def _cmyk_svg():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="8in" '
        'height="6in" viewBox="0 0 800 600">'
        '<g id="cyan"><path d="M 100,100 L 180,120" '
        'stroke="#00ffff" stroke-width="2" fill="none"/></g>'
        '<g id="magenta"><path d="M 200,140 L 280,180" '
        'stroke="#ff00ff" stroke-width="2" fill="none"/></g>'
        '<g id="yellow"><path d="M 300,220 L 380,240" '
        'stroke="#ffff00" stroke-width="2" fill="none"/></g>'
        '<g id="black"><path d="M 410,280 L 390,300" '
        'stroke="#000000" stroke-width="2" fill="none"/></g>'
        "</svg>"
    )


class PlotterfunGcodeExportTests(unittest.TestCase):
    def test_writer_creates_four_runnable_files_in_print_order(self):
        def analyze_program(svg_path, settings, cancel_check):
            del svg_path, settings
            if cancel_check is not None and cancel_check():
                raise converter.OperationCancelled()
            return {
                "gcode": "G21\nG90\nM3\nG1 X0 Y0 F700\nM5\nM2\n",
                "contours": [[(0.0, 0.0), (1.0, 1.0)]],
            }

        with tempfile.TemporaryDirectory(prefix="plotterfun-gcode-") as folder:
            root = Path(folder)
            svg_export = write_cmyk_svg_set(
                _cmyk_svg(),
                root / "internal",
                base_name="Golden Sunset",
                source_artwork=r"C:\art\Golden Sunset.png",
                algorithm="contours.js",
                created_utc="2026-11-25T12:00:00+00:00",
            )
            settings = converter.Settings(
                fit_mode="inside",
                scale=1.0,
            )
            exported = write_plotterfun_gcode_set(
                svg_export,
                root / "output",
                settings,
                analyze_program=analyze_program,
                source_artwork=r"C:\art\Golden Sunset.png",
                algorithm="contours.js",
                created_utc="2026-11-25T12:00:00+00:00",
            )
            self.assertEqual(
                [layer.path.name for layer in exported.layers],
                [
                    "Golden Sunset-01-yellow.gcode",
                    "Golden Sunset-02-magenta.gcode",
                    "Golden Sunset-03-cyan.gcode",
                    "Golden Sunset-04-black.gcode",
                ],
            )
            self.assertEqual(
                [layer.ink for layer in exported.layers],
                ["yellow", "magenta", "cyan", "black"],
            )
            self.assertTrue(all(layer.path.exists() for layer in exported.layers))
            self.assertTrue(
                all(
                    "G1 " in layer.path.read_text(encoding="utf-8")
                    for layer in exported.layers
                )
            )
            self.assertEqual(
                set((root / "output").iterdir()),
                set(planned_gcode_paths(root / "output", "Golden Sunset")),
            )

            manifest = json.loads(
                exported.manifest_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                manifest["kind"],
                "theta-plotterfun-cmyk-gcode-set",
            )
            self.assertEqual(
                manifest["print_order"],
                ["yellow", "magenta", "cyan", "black"],
            )
            self.assertIn("numeric order", manifest["print_instruction"])
            for layer, record in zip(exported.layers, manifest["layers"]):
                payload = layer.path.read_bytes()
                self.assertEqual(
                    record["sha256"],
                    hashlib.sha256(payload).hexdigest(),
                )
                self.assertEqual(record["file"], layer.path.name)
                self.assertEqual(
                    record["svg_sha256"],
                    layer.svg_sha256,
                )
                self.assertGreater(record["gcode_lines"], 0)
                self.assertGreater(record["contour_count"], 0)

    def test_public_plan_stays_in_selected_folder(self):
        paths = planned_gcode_paths(Path("C:/one-folder"), "portrait")
        self.assertEqual(
            [path.name for path in paths],
            [
                "portrait-01-yellow.gcode",
                "portrait-02-magenta.gcode",
                "portrait-03-cyan.gcode",
                "portrait-04-black.gcode",
                "portrait-cmyk-set.json",
            ],
        )


if __name__ == "__main__":
    unittest.main()
