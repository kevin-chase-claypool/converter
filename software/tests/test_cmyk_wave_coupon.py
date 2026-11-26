"""The compact black-pen CMYK wave comparison coupon."""

import importlib.util
import math
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))


def load_generator():
    path = ROOT / "tools" / "make_cmyk_wave_coupon.py"
    spec = importlib.util.spec_from_file_location("make_cmyk_wave_coupon", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CmykWaveCouponTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_generator()

    def test_coupon_is_one_file_with_all_angles_and_motions(self):
        self.assertEqual(
            tuple(angle for _ink, angle in self.module.COUPON_ANGLES),
            tuple(
                self.module.converter.SCREEN_ANGLES_DEG[ink]
                for ink in self.module.converter.CHANNELS
            ),
        )
        gcode, settings, marks = self.module.build_coupon()
        self.assertIn("single file", gcode)
        self.assertIn("upper 8 patches: A parked", gcode)
        self.assertIn("lower 8 patches: Xtheta-Ytheta", gcode)
        self.assertIn("columns left-to-right: C15 M75 Y0 K45", gcode)
        self.assertIn("first row of each set: phase-locked depth", gcode)
        self.assertIn("effective pitch 3.360 mm", gcode)
        self.assertIn("(feed 700.0 mm/min", gcode)
        self.assertEqual(settings.theta_mode, "optimized")
        self.assertEqual(gcode.count("\nM2\n"), 1)
        self.assertNotRegex(gcode, r"(?m)^M0\s*$")
        self.assertGreaterEqual(len(marks), 140)
        self.assertLess(len(marks), 320)
        xs = [x for mark in marks for x, _ in mark]
        ys = [y for mark in marks for _, y in mark]
        self.assertGreaterEqual(min(xs), -119.0)
        self.assertLessEqual(max(xs), 119.0)
        self.assertGreaterEqual(min(ys), -74.0)
        self.assertLessEqual(max(ys), 74.0)

    def test_coupon_passes_motion_guards(self):
        gcode, settings, _marks = self.module.build_coupon()
        with tempfile.TemporaryDirectory(
            prefix="cmyk-wave-coupon-"
        ) as folder:
            path = Path(folder) / "coupon.gcode"
            path.write_text(gcode, encoding="utf-8")
            checks = self.module.converter.analyse_file(path, settings)
        self.assertEqual(checks["rapids_with_rotation"], 0)
        self.assertLessEqual(checks["step"], checks["cap"])
        self.assertLessEqual(checks["rate"], checks["rate_cap"] * 1.01)
        self.assertIn("fixed", checks["strategies"])
        self.assertIn("x_theta", checks["strategies"])
        self.assertIn("y_theta", checks["strategies"])

    def test_coupon_exposes_phase_locked_depth_difference(self):
        for _ink, angle_deg in self.module.COUPON_ANGLES:
            with self.subTest(angle_deg=angle_deg):
                variable = self.module.coupon_patch(
                    "waves_zero",
                    -60.0,
                    -30.0,
                    angle_deg=angle_deg,
                )
                equidistant = self.module.coupon_patch(
                    "waves_even",
                    0.0,
                    -30.0,
                    angle_deg=angle_deg,
                )
                phase_spread = self._amplitude_spread(
                    variable, angle_deg
                )
                control_spread = self._amplitude_spread(
                    equidistant, angle_deg
                )
                self.assertGreater(phase_spread, 0.1)
                self.assertGreater(phase_spread, control_spread)

    def test_multi_pitch_coupon_is_one_rotating_bed_program(self):
        gcode, settings, marks = self.module.build_pitch_coupon()
        self.assertIn("single file; 12 patches", gcode)
        self.assertIn("2.800 / 3.360 / 4.200 mm pitch", gcode)
        self.assertIn("columns left-to-right: C15 M75 Y0 K45", gcode)
        self.assertEqual(settings.theta_mode, "optimized")
        self.assertEqual(gcode.count("\nM2\n"), 1)
        self.assertNotRegex(gcode, r"(?m)^M0\s*$")
        self.assertGreaterEqual(len(marks), 120)
        xs = [x for mark in marks for x, _y in mark]
        ys = [y for mark in marks for _x, y in mark]
        self.assertGreaterEqual(min(xs), -100.0)
        self.assertLessEqual(max(xs), 100.0)
        self.assertGreaterEqual(min(ys), -75.0)
        self.assertLessEqual(max(ys), 75.0)

        with tempfile.TemporaryDirectory(
            prefix="cmyk-wave-pitch-coupon-"
        ) as folder:
            path = Path(folder) / "pitch-coupon.gcode"
            path.write_text(gcode, encoding="utf-8")
            checks = self.module.converter.analyse_file(path, settings)
        self.assertEqual(checks["rapids_with_rotation"], 0)
        self.assertLessEqual(checks["step"], checks["cap"])
        self.assertLessEqual(checks["rate"], checks["rate_cap"] * 1.01)
        self.assertIn("x_theta", checks["strategies"])
        self.assertIn("y_theta", checks["strategies"])

    def test_letter_test_is_one_parked_implementation_check(self):
        gcode, settings, marks = self.module.build_letter_test()
        self.assertIn("8.5 x 11 paper; 16 patches", gcode)
        self.assertIn(
            "phase-locked 2.800 / 3.360 / 4.200 mm",
            gcode,
        )
        self.assertIn("equidistant 3.360 mm control", gcode)
        self.assertEqual(settings.theta_mode, "fixed")
        self.assertEqual(gcode.count("\nM2\n"), 1)
        self.assertNotRegex(gcode, r"(?m)^M0\s*$")

        xs = [x for mark in marks for x, _y in mark]
        ys = [y for mark in marks for _x, y in mark]
        self.assertGreaterEqual(min(xs), -103.0)
        self.assertLessEqual(max(xs), 103.0)
        self.assertGreaterEqual(min(ys), -104.0)
        self.assertLessEqual(max(ys), 104.0)

        for _ink, angle_deg in self.module.COUPON_ANGLES:
            phase_locked = self.module.coupon_patch(
                "waves_zero",
                -50.0,
                -50.0,
                width_mm=self.module.LETTER_PATCH_WIDTH_MM,
                height_mm=self.module.LETTER_PATCH_HEIGHT_MM,
                angle_deg=angle_deg,
                spacing_mm=2.80,
            )
            control = self.module.coupon_patch(
                "waves_even",
                -50.0,
                -50.0,
                width_mm=self.module.LETTER_PATCH_WIDTH_MM,
                height_mm=self.module.LETTER_PATCH_HEIGHT_MM,
                angle_deg=angle_deg,
                spacing_mm=2.80,
            )
            self.assertGreater(
                self._amplitude_spread(phase_locked, angle_deg),
                self._amplitude_spread(control, angle_deg),
            )

        with tempfile.TemporaryDirectory(
            prefix="cmyk-wave-letter-test-"
        ) as folder:
            path = Path(folder) / "letter.gcode"
            path.write_text(gcode, encoding="utf-8")
            checks = self.module.converter.analyse_file(path, settings)
        self.assertEqual(checks["rapids_with_rotation"], 0)
        self.assertLessEqual(checks["step"], checks["cap"])
        self.assertLessEqual(checks["rate"], checks["rate_cap"] * 1.01)
        self.assertEqual(checks["over_tolerance"], 0)
        self.assertIn("fixed", checks["strategies"])

    @staticmethod
    def _amplitude_spread(marks, angle_deg):
        angle = math.radians(angle_deg)
        cosine = math.cos(angle)
        sine = math.sin(angle)
        ranges = []
        for mark in marks:
            if len(mark) < 10:
                continue
            local_v = [-x * sine + y * cosine for x, y in mark]
            ranges.append(max(local_v) - min(local_v))
        return max(ranges) - min(ranges)


if __name__ == "__main__":
    unittest.main()
