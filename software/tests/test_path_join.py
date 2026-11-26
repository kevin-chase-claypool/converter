"""Conservative endpoint joining for ordinary SVG contours."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


class PathJoinTests(unittest.TestCase):
    def test_touching_contours_join_without_adding_a_gap(self):
        joined, stats = converter.join_touching_contours(
            [
                [(0.0, 0.0), (10.0, 0.0)],
                [(10.0, 0.0), (10.0, 10.0)],
                [(10.0, 10.0), (0.0, 10.0)],
            ],
            tolerance_mm=0.0,
        )

        self.assertEqual(len(joined), 1)
        self.assertEqual(
            joined[0],
            [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)],
        )
        self.assertEqual(stats["joined"], 2)

    def test_reversed_endpoint_is_joined(self):
        joined, _stats = converter.join_touching_contours(
            [
                [(0.0, 0.0), (10.0, 0.0)],
                [(20.0, 0.0), (10.0, 0.0)],
            ],
            tolerance_mm=0.0,
        )

        self.assertEqual(len(joined), 1)
        self.assertEqual(joined[0][-1], (20.0, 0.0))

    def test_gap_larger_than_tolerance_forces_a_pen_lift(self):
        joined, stats = converter.join_touching_contours(
            [
                [(0.0, 0.0), (10.0, 0.0)],
                [(10.1, 0.0), (20.0, 0.0)],
            ],
            tolerance_mm=0.05,
        )

        self.assertEqual(len(joined), 2)
        self.assertEqual(stats["joined"], 0)

    def test_small_gap_inside_tolerance_is_joined(self):
        joined, stats = converter.join_touching_contours(
            [
                [(0.0, 0.0), (10.0, 0.0)],
                [(10.01, 0.0), (20.0, 0.0)],
            ],
            tolerance_mm=0.02,
        )

        self.assertEqual(len(joined), 1)
        self.assertEqual(stats["joined"], 1)

    def test_closed_contours_stay_separate(self):
        closed = [(0.0, 0.0), (10.0, 0.0), (0.0, 10.0), (0.0, 0.0)]
        joined, stats = converter.join_touching_contours(
            [closed, [(0.0, 0.0), (-10.0, 0.0)]],
            tolerance_mm=0.01,
        )

        self.assertEqual(len(joined), 2)
        self.assertEqual(stats["joined"], 0)

    def test_tagged_wave_rows_are_left_to_their_specialized_planner(self):
        rows = [
            converter.WaveTrail([(0.0, 0.0), (10.0, 0.0)], wave_row_index=0),
            converter.WaveTrail([(10.0, 0.0), (20.0, 0.0)], wave_row_index=0),
        ]
        joined, stats = converter.join_touching_contours(rows)

        self.assertEqual(joined, rows)
        self.assertFalse(stats["enabled"])
        self.assertEqual(stats["reason"], "tagged contours")

    def test_gcode_has_one_pen_cycle_for_a_joined_chain(self):
        contours = [
            [(0.0, 0.0), (10.0, 0.0)],
            [(10.0, 0.0), (10.0, 10.0)],
            [(20.0, 0.0), (30.0, 0.0)],
        ]
        settings = converter.Settings(
            theta_mode="fixed",
            bed_compensation_path="",
            flip_y=False,
            join_touching_contours=True,
            path_join_tolerance_mm=0.0,
        )
        plan = converter.plan_program(contours, settings)
        gcode = converter.contours_to_gcode(contours, settings, plan)

        self.assertEqual(len(plan["contours"]), 2)
        self.assertEqual(gcode.count("\nM3\n"), 2)
        self.assertIn("(contour join 3 -> 2 contours", gcode)

    def test_join_tolerance_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "path join tolerance"):
            converter.validate_settings(
                converter.Settings(path_join_tolerance_mm=5.1)
            )
        with self.assertRaisesRegex(ValueError, "physical pen width"):
            converter.validate_settings(
                converter.Settings(
                    join_touching_contours=True,
                    pen_diameter_mm=0.2,
                    path_join_tolerance_mm=0.21,
                )
            )

    def test_setting_is_available_in_the_convert_sidebar(self):
        self.assertIn(
            ("Geometry", "join_touching_contours", "Join touching contours (keep pen down)", False),
            converter.CHECKBOX_FIELDS,
        )
        geometry_fields = dict(
            (key, default)
            for group, fields in converter.TEXT_FIELD_GROUPS
            if group == "Geometry"
            for _label, key, default in fields
        )
        self.assertEqual(geometry_fields["path_join_tolerance_mm"], "0.02")


if __name__ == "__main__":
    unittest.main()
