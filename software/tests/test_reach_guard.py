"""Post-compensation reach safety for generated G-code."""

import dataclasses
import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


class ReachGuardTests(unittest.TestCase):
    def settings(self):
        return dataclasses.replace(
            converter.default_settings(),
            theta_mode="fixed",
            flip_y=False,
        )

    def test_compensated_edge_artwork_stays_inside_machine_reach(self):
        contours = [
            [
                (0.0, 0.0),
                (
                    200.0 * math.cos(2.0 * math.pi * index / 16.0),
                    200.0 * math.sin(2.0 * math.pi * index / 16.0),
                ),
            ]
            for index in range(16)
        ]
        settings = self.settings()

        gcode = converter.contours_to_gcode(contours, settings)
        analysis = converter.analyse_gcode(gcode, settings)

        self.assertIn("(reach guard 180.000 mm, planning radius", gcode)
        self.assertLessEqual(
            analysis["max_xy_radius_mm"],
            settings.machine_reach_radius_mm + 1e-6,
        )
        self.assertFalse(
            any(
                "machine reach" in problem
                for problem in converter.preflight_problems(analysis)
            )
        )

    def test_preflight_rejects_a_final_point_outside_machine_reach(self):
        settings = dataclasses.replace(
            self.settings(),
            bed_compensation_path="",
        )
        gcode = "\n".join(
            [
                "G21",
                "G90",
                "G54",
                "M5",
                "G1 X0 Y0 A0 F3000 (travel)",
                "M3",
                "G1 X180.5 Y2.0 A0 F700 (fixed)",
                "M5",
            ]
        )

        analysis = converter.analyse_gcode(gcode, settings)
        problems = converter.preflight_problems(analysis)

        self.assertAlmostEqual(analysis["max_xy_radius_mm"], math.hypot(180.5, 2.0))
        self.assertEqual(analysis["max_xy_radius_line"], 7)
        self.assertTrue(
            any("machine reach" in problem for problem in problems),
            problems,
        )


if __name__ == "__main__":
    unittest.main()
