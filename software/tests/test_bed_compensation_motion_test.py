"""Regression checks for the comprehensive compensated XY/A diagnostic."""

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


class BedCompensationMotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_generator()
        cls.profile = cls.module.load_profile()
        cls.gcode = cls.module.build_program(cls.profile)
        cls.module.check_comments(cls.gcode)
        cls.cases = {
            case["id"]: case for case in cls.module.CASES
        }
        cls.sections = cls._case_sections(cls.gcode)

    def test_program_is_one_pause_free_comprehensive_run(self):
        self.assertEqual(self.gcode.count("\nM2\n"), 1)
        self.assertNotRegex(self.gcode, r"(?m)^M0\s*$")
        self.assertIn("one file, one Cycle Start, no M0 pauses", self.gcode)
        self.assertIn("feed ladder 350/700/1200 mm/min", self.gcode)
        self.assertEqual(len(self.cases), 11)
        self.assertEqual(
            set(self.sections),
            set(self.cases),
        )

    def test_each_case_repeats_three_feeds_in_both_directions(self):
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                section = self.sections[case_id]
                feed_sections = self._feed_sections(section)
                self.assertEqual(
                    tuple(feed for feed, _section in feed_sections),
                    self.module.FEED_LADDER_MM_MIN,
                )
                expected_count = len(self.module.path_points(case)) - 1
                all_feed_values = []
                for _feed, feed_section in feed_sections:
                    forward = self._trace_commands(
                        feed_section, "forward trace"
                    )
                    reverse = self._trace_commands(
                        feed_section, "reverse trace"
                    )
                    self.assertEqual(len(forward), expected_count)
                    self.assertEqual(len(reverse), expected_count)
                    all_feed_values.append(
                        sum(item["feed"] for item in forward + reverse)
                        / len(forward + reverse)
                    )
                self.assertLess(all_feed_values[0], all_feed_values[1])
                self.assertLess(all_feed_values[1], all_feed_values[2])

    def test_every_case_traces_its_bed_space_path(self):
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                expected_points = self.module.path_points(case)
                for _feed, feed_section in self._feed_sections(
                    self.sections[case_id]
                ):
                    commands = (
                        self._trace_commands(
                            feed_section, "forward trace"
                        )
                        + self._trace_commands(
                            feed_section, "reverse trace"
                        )
                    )
                    forward = commands[: len(expected_points) - 1]
                    reverse = commands[len(expected_points) - 1 :]
                    for index, command in enumerate(
                        forward, start=1
                    ):
                        self._assert_machine_point_and_angle(
                            case,
                            command,
                            expected_points[index],
                            index / (len(expected_points) - 1),
                        )
                    for offset, command in enumerate(reverse):
                        expected_index = len(expected_points) - 2 - offset
                        self._assert_machine_point_and_angle(
                            case,
                            command,
                            expected_points[expected_index],
                            expected_index / (len(expected_points) - 1),
                        )

    def test_controls_horizontal_vertical_normal_and_reverse_sweeps(self):
        for case_id in (1, 2):
            with self.subTest(control=case_id):
                angles = [
                    command["a"]
                    for command in self._all_move_commands(
                        self.sections[case_id]
                    )
                ]
                self.assertTrue(angles)
                self.assertTrue(all(abs(angle) < 1e-9 for angle in angles))

        normal = self._trace_commands(
            self._feed_sections(self.sections[3])[0][1],
            "forward trace",
        )
        reverse = self._trace_commands(
            self._feed_sections(self.sections[5])[0][1],
            "forward trace",
        )
        self.assertLess(normal[0]["a"], 0.0)
        self.assertGreater(normal[-1]["a"], 0.0)
        self.assertGreater(reverse[0]["a"], 0.0)
        self.assertLess(reverse[-1]["a"], 0.0)

        self.assertEqual(self.cases[7]["orientation_deg"], 90.0)
        self.assertEqual(self.cases[8]["orientation_deg"], 90.0)
        self.assertLess(
            max(
                math.hypot(x, y)
                for x, y in self.module.path_points(self.cases[9])
            ),
            max(
                math.hypot(x, y)
                for x, y in self.module.path_points(self.cases[3])
            ),
        )

    def test_compensation_changes_each_on_off_pair(self):
        for case_id in (4, 6, 8, 10, 11):
            with self.subTest(case=case_id):
                case = self.cases[case_id]
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

    def test_each_case_has_pen_up_round_trip_and_two_witnesses(self):
        for case_id, case in self.cases.items():
            with self.subTest(case=case_id):
                section = self.sections[case_id]
                self.assertEqual(section.count("(initial witness)"), 6)
                self.assertEqual(section.count("(return witness)"), 6)
                self.assertEqual(
                    section.count("(pen-up transition to path)"), 1
                )
                self.assertEqual(
                    section.count("(pen-up return to witness)"), 1
                )
                self.assertEqual(section.count("\nM3\n"), 3)
                self.assertEqual(section.count("\nM5\n"), 3)
                transition = self._move_after_description(
                    section, "pen-up transition to path"
                )
                self.assertEqual(
                    abs(transition["a"]) > 1e-9,
                    bool(case["rotate"]),
                )

    def test_global_frame_is_drawn_before_and_after_the_matrix(self):
        first_case = self.gcode.index("(case 1:")
        last_case = self.gcode.rindex("(case 11:")
        for index in range(1, 5):
            marker = f"(frame witness {index})"
            self.assertEqual(self.gcode.count(marker), 12)
            self.assertLess(self.gcode.index(marker), first_case)
            self.assertGreater(self.gcode.rindex(marker), last_case)

    def test_case_regions_stay_separated_on_the_sheet(self):
        points = {
            case["id"]: [
                self.module.witness_point(case),
                *self.module.path_points(case),
            ]
            for case in self.module.CASES
        }
        case_ids = tuple(points)
        for index, first_id in enumerate(case_ids):
            for second_id in case_ids[index + 1 :]:
                separation = min(
                    math.hypot(x0 - x1, y0 - y1)
                    for x0, y0 in points[first_id]
                    for x1, y1 in points[second_id]
                )
                self.assertGreater(separation, 8.0)

    def test_program_fits_letter_paper_and_existing_motion_guards(self):
        points = self._all_machine_points(self.gcode)
        self.assertGreaterEqual(min(x for x, _y in points), -108.0)
        self.assertLessEqual(max(x for x, _y in points), 108.0)
        self.assertGreaterEqual(min(y for _x, y in points), -140.0)
        self.assertLessEqual(max(y for _x, y in points), 140.0)
        self.assertLessEqual(
            max(math.hypot(x, y) for x, y in points),
            self.profile.coverage_radius_mm,
        )

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
        self.assertEqual(checks["fed_rotations"], 18)

    def _assert_machine_point_and_angle(
        self,
        case,
        command,
        expected_point,
        fraction,
    ):
        theta = self.module.theta_for_fraction(case, fraction)
        expected_machine = self.module.machine_point(
            expected_point,
            theta,
            self.profile,
            bool(case["compensate"]),
        )
        self.assertLess(
            math.hypot(
                command["x"] - expected_machine[0],
                command["y"] - expected_machine[1],
            ),
            0.002,
        )
        self.assertAlmostEqual(
            command["a"],
            theta * self.module.THETA_RATIO,
            places=4,
        )

    @classmethod
    def _case_sections(cls, gcode):
        starts = list(
            re.finditer(r"^\(case (\d+):", gcode, re.MULTILINE)
        )
        sections = {}
        last_case_start = starts[-1].start()
        final_start = gcode.index(
            "(final frame recheck)", last_case_start
        )
        for index, match in enumerate(starts):
            end = (
                starts[index + 1].start()
                if index + 1 < len(starts)
                else final_start
            )
            sections[int(match.group(1))] = gcode[match.start() : end]
        return sections

    @staticmethod
    def _feed_sections(section):
        matches = list(
            re.finditer(
                r"^\(feed pass ([\d.]+) mm/min\)$",
                section,
                re.MULTILINE,
            )
        )
        result = []
        for index, match in enumerate(matches):
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(section)
            )
            result.append(
                (float(match.group(1)), section[match.end() : end])
            )
        return result

    @classmethod
    def _trace_commands(cls, section, label):
        return [
            command
            for command in cls._all_move_commands(section)
            if command["label"] == label
        ]

    @staticmethod
    def _all_move_commands(section):
        word = re.compile(
            r"([XYAF])([-+]?\d+(?:\.\d+)?)"
        )
        commands = []
        for line in section.splitlines():
            if not re.match(r"^G[01]\s", line):
                continue
            values = {
                key: float(value)
                for key, value in word.findall(line.split("(", 1)[0])
            }
            if not all(key in values for key in ("X", "Y", "A")):
                continue
            label_match = re.search(r"\(([a-z ]+)\)\s*$", line)
            commands.append(
                {
                    "x": values["X"],
                    "y": values["Y"],
                    "a": values["A"],
                    "feed": values.get("F", 0.0),
                    "label": (
                        label_match.group(1) if label_match else ""
                    ),
                }
            )
        return commands

    @classmethod
    def _all_machine_points(cls, gcode):
        return [
            (command["x"], command["y"])
            for command in cls._all_move_commands(gcode)
        ]

    @classmethod
    def _move_after_description(cls, section, description):
        marker = f"({description})"
        start = section.index(marker) + len(marker)
        return cls._all_move_commands(section[start:])[0]

if __name__ == "__main__":
    unittest.main()
