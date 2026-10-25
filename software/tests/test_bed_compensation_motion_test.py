"""Regression checks for the compensated XY/A motion diagnostic."""

import importlib.util
import math
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_generator():
    path = ROOT / "tools" / "make_bed_compensation_motion_test.py"
    spec = importlib.util.spec_from_file_location(
        "make_bed_compensation_motion_test", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inverse_machine_point(
    machine: tuple[float, float],
    theta_deg: float,
    profile,
) -> tuple[float, float]:
    angle = math.radians(theta_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    bed_x, bed_y = machine
    for _ in range(12):
        correction_x, correction_y = profile.correction(
            theta_deg, bed_x, bed_y
        )
        unrotated_x = machine[0] - correction_x
        unrotated_y = machine[1] - correction_y
        bed_x = cosine * unrotated_x + sine * unrotated_y
        bed_y = -sine * unrotated_x + cosine * unrotated_y
    return bed_x, bed_y


class BedCompensationMotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_generator()
        cls.profile = cls.module.load_profile()
        cls.gcode = cls.module.build_program(cls.profile)
        cls.module.check_comments(cls.gcode)

    def test_program_is_one_pause_free_run(self):
        self.assertEqual(self.gcode.count("\nM2\n"), 1)
        self.assertNotRegex(self.gcode, r"(?m)^M0\s*$")
        self.assertIn("one file and one Cycle Start", self.gcode)
        for case in self.module.CASES:
            self.assertIn(f"(case {case['id']}:", self.gcode)
        self.assertIn("$123=6000 and $701=0", self.gcode)

    def test_all_cases_share_one_bed_space_path_and_angle_schedule(self):
        sections = self._case_sections()
        reference_case = dict(
            self.module.CASES[0], y_mm=0.0, rotate=True
        )
        expected_points = self.module.path_points(reference_case)
        for case in self.module.CASES:
            with self.subTest(case=case["id"]):
                expected_angles = [
                    round(
                        self.module.theta_for_fraction(
                            case, index / (len(expected_points) - 1)
                        ),
                        9,
                    )
                    for index in range(len(expected_points))
                ]
                commands = self._trace_commands(sections[case["id"]])
                self.assertEqual(len(commands), 2 * (len(expected_points) - 1))
                decoded = [
                    (
                        inverse_machine_point(
                            (x_mm, y_mm),
                            a_deg / self.module.THETA_RATIO,
                            self.profile,
                        )
                        if case["compensate"]
                        else self._rotate_back(
                            (x_mm, y_mm),
                            a_deg / self.module.THETA_RATIO,
                        ),
                        a_deg,
                    )
                    for x_mm, y_mm, a_deg in commands
                ]
                forward = decoded[: len(expected_points) - 1]
                reverse = decoded[len(expected_points) - 1 :]

                for index, (point, angle) in enumerate(
                    forward, start=1
                ):
                    self.assertLess(
                        math.hypot(
                            point[0] - expected_points[index][0],
                            point[1]
                            - case["y_mm"]
                            - expected_points[index][1],
                        ),
                        0.002,
                    )
                    self.assertAlmostEqual(
                        angle,
                        expected_angles[index]
                        * self.module.THETA_RATIO,
                        places=4,
                    )
                for offset, (point, angle) in enumerate(
                    reverse, start=0
                ):
                    expected_index = len(expected_points) - 2 - offset
                    self.assertLess(
                        math.hypot(
                            point[0] - expected_points[expected_index][0],
                            point[1]
                            - case["y_mm"]
                            - expected_points[expected_index][1],
                        ),
                        0.002,
                    )
                    self.assertAlmostEqual(
                        angle,
                        expected_angles[expected_index]
                        * self.module.THETA_RATIO,
                        places=4,
                    )

    def test_each_case_has_rotating_pen_up_and_two_witnesses(self):
        sections = self._case_sections()
        for case in self.module.CASES:
            with self.subTest(case=case["id"]):
                section = sections[case["id"]]
                self.assertEqual(section.count("(initial witness)"), 6)
                self.assertEqual(section.count("(return witness)"), 6)
                self.assertEqual(
                    section.count("(rotating pen-up to path)"), 1
                )
                self.assertEqual(
                    section.count("(rotating pen-up return to witness)"), 1
                )
                self.assertGreaterEqual(section.count("\nM3\n"), 3)
                self.assertGreaterEqual(section.count("\nM5\n"), 3)

    def test_compensation_changes_the_machine_path(self):
        for case_id in (3, 5):
            with self.subTest(case=case_id):
                case = next(
                    item
                    for item in self.module.CASES
                    if item["id"] == case_id
                )
                points = self.module.path_points(case)
                differences = []
                for index, point in enumerate(points):
                    theta = self.module.theta_for_fraction(
                        case, index / (len(points) - 1)
                    )
                    compensated = self.module.machine_point(
                        point, theta, self.profile, True
                    )
                    nominal = self.module.machine_point(
                        point, theta, self.profile, False
                    )
                    differences.append(
                        math.hypot(
                            compensated[0] - nominal[0],
                            compensated[1] - nominal[1],
                        )
                    )
                self.assertGreater(max(differences), 0.04)

    def test_program_passes_existing_motion_guards(self):
        with tempfile.TemporaryDirectory(
            prefix="bed-compensation-motion-test-"
        ) as folder:
            path = Path(folder) / "motion-test.gcode"
            path.write_text(self.gcode, encoding="utf-8")
            checks = self.module.converter.analyse_file(
                path, self.module.converter.Settings()
            )
        self.assertEqual(checks["rapids_with_rotation"], 0)
        self.assertLessEqual(checks["step"], checks["cap"])
        self.assertLessEqual(checks["rate"], checks["rate_cap"] * 1.01)
        self.assertEqual(checks["over_tolerance"], 0)

    def _case_sections(self):
        starts = list(
            re.finditer(r"^\(case (\d+):", self.gcode, re.MULTILINE)
        )
        sections = {}
        for index, match in enumerate(starts):
            end = (
                starts[index + 1].start()
                if index + 1 < len(starts)
                else self.gcode.index("\nM65 P0", match.end())
            )
            sections[int(match.group(1))] = self.gcode[match.start() : end]
        return sections

    def _trace_commands(self, section):
        commands = []
        pen_down = False
        word = re.compile(r"([XYAF])([-+]?\d+(?:\.\d+)?)")
        for line in section.splitlines():
            if line == "M3":
                pen_down = True
            elif line == "M5":
                pen_down = False
            elif pen_down and (
                "(forward trace)" in line or "(reverse trace)" in line
            ):
                values = {
                    key: float(value)
                    for key, value in word.findall(line.split("(", 1)[0])
                }
                commands.append((values["X"], values["Y"], values["A"]))
        return commands

    @staticmethod
    def _rotate_back(
        machine: tuple[float, float], theta_deg: float
    ) -> tuple[float, float]:
        angle = math.radians(theta_deg)
        cosine = math.cos(angle)
        sine = math.sin(angle)
        return (
            cosine * machine[0] + sine * machine[1],
            -sine * machine[0] + cosine * machine[1],
        )


if __name__ == "__main__":
    unittest.main()
