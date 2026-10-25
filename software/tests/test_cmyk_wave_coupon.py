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

    def test_coupon_is_small_black_pen_and_uses_both_modes(self):
        gcode, settings, marks = self.module.build_coupon()
        self.assertIn("left 28x20 mm: Wave screen - zero-anchored depth", gcode)
        self.assertIn("right 28x20 mm: Wave screen - equidistant rows", gcode)
        self.assertIn("effective pitch 3.360 mm", gcode)
        self.assertIn("(feed 700.0 mm/min", gcode)
        self.assertEqual(settings.theta_mode, "fixed")
        self.assertGreaterEqual(len(marks), 10)
        self.assertLess(len(marks), 30)
        xs = [x for mark in marks for x, _ in mark]
        self.assertGreaterEqual(min(xs), -35.0)
        self.assertLessEqual(max(xs), 35.0)

    def test_coupon_passes_motion_guards(self):
        gcode, settings, _marks = self.module.build_coupon()
        with tempfile.TemporaryDirectory(prefix="cmyk-wave-coupon-") as folder:
            path = Path(folder) / "coupon.gcode"
            path.write_text(gcode, encoding="utf-8")
            checks = self.module.converter.analyse_file(path, settings)
        self.assertEqual(checks["rapids_with_rotation"], 0)
        self.assertLessEqual(checks["step"], checks["cap"])
        self.assertLessEqual(checks["rate"], checks["rate_cap"] * 1.01)

    def test_coupon_exposes_the_spacing_difference(self):
        def gap_spread(marks):
            angle = math.radians(75.0)
            cosine = math.cos(angle)
            sine = math.sin(angle)
            local = [
                [
                    (
                        x * cosine + y * sine,
                        -x * sine + y * cosine,
                    )
                    for x, y in mark
                ]
                for mark in marks
            ]

            def value_at(row, u_value):
                ordered = sorted(row)
                for first, second in zip(ordered, ordered[1:]):
                    if first[0] <= u_value <= second[0]:
                        fraction = (u_value - first[0]) / max(
                            second[0] - first[0], 1e-9
                        )
                        return first[1] + fraction * (second[1] - first[1])
                return None

            gaps = []
            for u_value in range(-30, 21):
                ys = sorted(
                    value
                    for row in local
                    if (value := value_at(row, u_value)) is not None
                )
                gaps.extend(
                    second - first
                    for first, second in zip(ys, ys[1:])
                    if 2.5 < second - first < 4.2
                )
            return max(gaps) - min(gaps)

        variable = self.module.coupon_patch("waves_zero", -34.0, -10.0)
        equidistant = self.module.coupon_patch(
            "waves_even", 6.0, -10.0
        )
        self.assertGreater(gap_spread(variable), 0.15)
        self.assertLess(gap_spread(equidistant), 1e-6)


if __name__ == "__main__":
    unittest.main()
