"""Pen tip width: the plotter's pen is a Sakura Pigma Micron 005 (0.20 mm).

The number is used for pen-width compensation of imported SVG artwork, for the
gap the fill bridging tolerates, and for ink reporting, so the default has to
match the pen on the machine - and the kaleidoscope window has to pass whatever
the operator types through to the planner.
"""

import dataclasses
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


def _square(size=100.0):
    half = size / 2.0
    return [
        [
            (-half, -half),
            (half, -half),
            (half, half),
            (-half, half),
            (-half, -half),
        ]
    ]


class PenWidthTests(unittest.TestCase):
    def test_default_matches_the_installed_pen(self):
        self.assertAlmostEqual(converter.Settings().pen_diameter_mm, 0.20, places=6)

    def test_compensation_shrinks_artwork_by_the_pen_width(self):
        for pen in (0.20, 0.30, 0.50):
            settings = dataclasses.replace(
                converter.Settings(), pen_diameter_mm=pen, compensate_pen_width=True
            )
            contours = converter.apply_geometry_settings(_square(100.0), settings)
            min_x, min_y, max_x, max_y = converter.contour_bounds(contours)
            self.assertAlmostEqual(max_x - min_x, 100.0 - pen, places=6)
            self.assertAlmostEqual(max_y - min_y, 100.0 - pen, places=6)

    def test_compensation_can_be_switched_off(self):
        settings = dataclasses.replace(
            converter.Settings(), pen_diameter_mm=0.5, compensate_pen_width=False
        )
        contours = converter.apply_geometry_settings(_square(100.0), settings)
        min_x, _, max_x, _ = converter.contour_bounds(contours)
        self.assertAlmostEqual(max_x - min_x, 100.0, places=6)

    def test_header_records_the_pen_width(self):
        settings = converter.Settings()
        gcode = converter.contours_to_gcode([[(0.0, 0.0), (10.0, 0.0)]], settings)
        self.assertIn("pen 0.20 mm", gcode)


if __name__ == "__main__":
    unittest.main()
