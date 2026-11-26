"""Post-save overlay audit for CMYK G-code sets."""

import dataclasses
import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


class GcodeOverlayTests(unittest.TestCase):
    def settings(self):
        return dataclasses.replace(
            converter.default_settings(),
            theta_mode="fixed",
            flip_y=False,
            frame_center_mm=(0.0, 0.0),
            pen_diameter_mm=0.9,
        )

    def write_programs(self, folder):
        settings = self.settings()
        paths = {}
        for index, channel in enumerate(converter.CHANNELS):
            offset = index * 2.0
            contours = [
                [
                    (-20.0 + offset, -10.0),
                    (20.0 + offset, -10.0),
                    (20.0 + offset, 10.0),
                    (-20.0 + offset, 10.0),
                    (-20.0 + offset, -10.0),
                ]
            ]
            path = Path(folder) / f"set-{channel}.gcode"
            path.write_text(
                converter.contours_to_gcode(contours, settings),
                encoding="utf-8",
            )
            paths[channel] = path
        return paths, settings

    def test_overlay_and_report_are_written_for_a_matching_set(self):
        with tempfile.TemporaryDirectory(prefix="cmyk-overlay-") as folder:
            paths, settings = self.write_programs(folder)
            output_stem = Path(folder) / "set-overlay"

            report = converter.write_cmyk_gcode_overlay(
                paths,
                output_stem,
                settings,
            )

            self.assertTrue(report["passed"], report["errors"])
            self.assertEqual(
                set(report["inks"]),
                set(converter.CHANNELS),
            )
            self.assertEqual(
                report["identity"]["profile_fingerprint"],
                "f85ec410dbac",
            )
            image_path = Path(report["overlay_png"])
            self.assertTrue(image_path.is_file())
            with Image.open(image_path) as image:
                self.assertEqual(image.size, (1400, 1400))
                self.assertGreater(len(image.getcolors(200000)), 10)
            saved = json.loads(
                Path(report["overlay_json"]).read_text(encoding="utf-8")
            )
            self.assertTrue(saved["passed"])
            self.assertEqual(saved["overlay_png"], str(image_path))

    def test_mismatched_frame_still_renders_but_marks_audit_blocked(self):
        with tempfile.TemporaryDirectory(prefix="cmyk-overlay-fail-") as folder:
            paths, settings = self.write_programs(folder)
            text = paths["m"].read_text(encoding="utf-8")
            paths["m"].write_text(
                text.replace(
                    "(frame center 0.000,0.000 mm",
                    "(frame center 0.500,0.000 mm",
                    1,
                ),
                encoding="utf-8",
            )

            report = converter.write_cmyk_gcode_overlay(
                paths,
                Path(folder) / "set-overlay",
                settings,
            )

            self.assertFalse(report["passed"])
            self.assertTrue(
                any("frame center" in error for error in report["errors"]),
                report["errors"],
            )
            self.assertTrue(Path(report["overlay_png"]).is_file())

    def test_subset_overlay_checks_only_selected_inks(self):
        with tempfile.TemporaryDirectory(prefix="cmyk-overlay-subset-") as folder:
            settings = dataclasses.replace(
                self.settings(),
                row_locked_compensation=True,
                row_lock_screen_angle_deg=45.0,
            )
            path = Path(folder) / "subset-black.gcode"
            path.write_text(
                converter.contours_to_gcode(
                    [[(-20.0, 0.0), (20.0, 0.0)]],
                    settings,
                ),
                encoding="utf-8",
            )

            report = converter.write_cmyk_gcode_overlay(
                {"k": path},
                Path(folder) / "subset-overlay",
                settings,
            )

            self.assertTrue(report["passed"], report["errors"])
            self.assertEqual(set(report["inks"]), {"k"})
            self.assertEqual(
                report["identity"]["row_angles_deg"],
                {"k": 45.0},
            )


if __name__ == "__main__":
    unittest.main()
