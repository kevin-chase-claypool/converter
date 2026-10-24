"""One-sheet diagnostic for bed rotation during a pen-down wave screen."""

import math
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


class WaveRotationIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = converter.BedCompensationProfile.from_json(
            (
                ROOT
                / "samples"
                / "gcode"
                / "bed-error-compensation-2026-10-23-13p5in-extrapolated.json"
            ).read_text(encoding="utf-8")
        )

    def generate(self, directory):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "make_wave_rotation_isolation_test.py"),
                "--out-dir",
                directory,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return (
            Path(directory) / "wave-rotation-isolation-base.gcode",
            Path(directory) / "wave-rotation-isolation-low-a-accel.gcode",
        )

    def test_generator_writes_both_single_sheet_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            base, low_accel = self.generate(temporary)
            self.assertTrue(base.exists())
            self.assertTrue(low_accel.exists())

            base_text = base.read_text(encoding="utf-8")
            low_text = low_accel.read_text(encoding="utf-8")
            for case in range(1, 7):
                self.assertIn(f"(case {case}:", base_text)
            self.assertIn("(case 7:", low_text)
            self.assertIn("(case 8:", low_text)
            self.assertIn("$123=3000", low_text)

            for text in (base_text, low_text):
                for line in text.splitlines():
                    if "(" in line:
                        self.assertTrue(
                            line.rstrip().endswith(")"),
                            f"ioSender-unsafe comment: {line!r}",
                        )

            base_checks = converter.analyse_file(base, converter.Settings())
            low_checks = converter.analyse_file(
                low_accel, converter.Settings()
            )
            for checks in (base_checks, low_checks):
                self.assertEqual(checks["rapids_with_rotation"], 0)
                self.assertLessEqual(checks["step"], checks["cap"])
                self.assertLessEqual(checks["rate"], checks["rate_cap"] * 1.01)

    def test_every_case_traces_the_same_bed_space_wave(self):
        with tempfile.TemporaryDirectory() as temporary:
            base, low_accel = self.generate(temporary)
            all_cases = {}
            for path in (base, low_accel):
                text = path.read_text(encoding="utf-8")
                starts = list(re.finditer(r"^\(case (\d+):", text, re.MULTILINE))
                for index, match in enumerate(starts):
                    end = (
                        starts[index + 1].start()
                        if index + 1 < len(starts)
                        else len(text)
                    )
                    all_cases[int(match.group(1))] = text[match.start() : end]

            self.assertEqual(sorted(all_cases), list(range(1, 9)))
            shapes = {
                case_id: self._normalized_case_points(section)
                for case_id, section in all_cases.items()
            }
            reference = shapes[1]
            for case_id, points in shapes.items():
                self.assertEqual(len(points), len(reference), case_id)
                error = max(
                    math.hypot(x0 - x1, y0 - y1)
                    for (x0, y0), (x1, y1) in zip(points, reference)
                )
                self.assertLess(error, 0.03, case_id)

    def _normalized_case_points(self, text):
        match = re.search(
            r"center\s+([-+]?\d+(?:\.\d+)?),([-+]?\d+(?:\.\d+)?)",
            text,
        )
        self.assertIsNotNone(match)
        center_x, center_y = (float(value) for value in match.groups())
        return [
            (x_mm - center_x, y_mm - center_y)
            for x_mm, y_mm in self._pen_down_bed_points(text)
        ]

    def _pen_down_bed_points(self, text):
        word = re.compile(r"([XYZAF])([-+]?\d+(?:\.\d+)?)")
        x = y = a = 0.0
        pen_down = False
        points = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped == "M3":
                pen_down = True
                continue
            if stripped == "M5":
                pen_down = False
                continue
            if not (pen_down and line.startswith("G1 ")):
                continue
            values = {
                key: float(value)
                for key, value in word.findall(line.split("(", 1)[0])
            }
            if "X" not in values and "Y" not in values:
                continue
            next_x = values.get("X", x)
            next_y = values.get("Y", y)
            next_a = values.get("A", a)
            points.append(
                self._inverse_machine_point(next_x, next_y, next_a / 12.03324)
            )
            x, y, a = next_x, next_y, next_a
        return points

    def _inverse_machine_point(self, machine_x, machine_y, theta_deg):
        radians = math.radians(theta_deg)
        cosine = math.cos(radians)
        sine = math.sin(radians)
        bed_x, bed_y = machine_x, machine_y
        limit = self.profile.coverage_radius_mm * 0.999999
        radius = math.hypot(bed_x, bed_y)
        if radius > limit:
            bed_x *= limit / radius
            bed_y *= limit / radius
        for _ in range(12):
            correction_x, correction_y = self.profile.correction(
                theta_deg, bed_x, bed_y
            )
            unrotated_x = machine_x - correction_x
            unrotated_y = machine_y - correction_y
            bed_x = cosine * unrotated_x + sine * unrotated_y
            bed_y = -sine * unrotated_x + cosine * unrotated_y
            radius = math.hypot(bed_x, bed_y)
            if radius > limit:
                bed_x *= limit / radius
                bed_y *= limit / radius
        return bed_x, bed_y


if __name__ == "__main__":
    unittest.main()
