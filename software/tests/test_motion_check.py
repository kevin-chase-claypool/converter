"""Motion preflight metrics shared by the CLI and CMYK save path."""

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


class MotionCheckTests(unittest.TestCase):
    def test_clean_program_passes(self):
        settings = converter.Settings(theta_mode="fixed")
        text = "G1 X0 Y0 A0 F700\nG1 X10 Y0 A0 F700\n"
        result = converter.analyse_gcode(text, settings)
        self.assertEqual(converter.preflight_problems(result), [])
        self.assertEqual(result["step"], 0.0)
        self.assertEqual(result["over_tolerance"], 0)
        self.assertEqual(result["drawing"], 1)

    def test_large_bed_step_is_reported(self):
        settings = converter.Settings(theta_max_step_deg=15.0)
        text = "G1 X0 Y0 A0 F700\nG1 X1 Y0 A360 F700\n"
        result = converter.analyse_gcode(text, settings)
        self.assertGreater(result["step"], 15.0)
        self.assertTrue(
            any("deg cap" in problem for problem in converter.preflight_problems(result))
        )

    def test_bare_g0_rotation_is_reported(self):
        settings = converter.Settings()
        text = "G0 X0 Y0 A0\nG0 X10 Y0 A360\n"
        result = converter.analyse_gcode(text, settings)
        self.assertEqual(result["rapids_with_rotation"], 1)
        self.assertTrue(
            any("bare G0" in problem for problem in converter.preflight_problems(result))
        )

    def test_moves_over_tolerance_are_counted(self):
        settings = converter.Settings(tolerance=0.001, theta_max_step_deg=180.0)
        text = "G1 X10 Y0 A0 F700\nG1 X10.1 Y0 A100 F700\n"
        result = converter.analyse_gcode(text, settings)
        self.assertGreater(result["over_tolerance"], 0)

    def test_file_wrapper_reads_the_same_text(self):
        settings = converter.Settings(theta_mode="fixed")
        text = "G1 X0 Y0 A0 F700\nG1 X10 Y0 A0 F700\n"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "program.gcode"
            path.write_text(text, encoding="utf-8")
            result = converter.analyse_file(path, settings)
        self.assertEqual(result["drawing"], 1)
        self.assertEqual(result["over_tolerance"], 0)


if __name__ == "__main__":
    unittest.main()
