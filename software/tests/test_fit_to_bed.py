"""Fit-to-bed geometry: measure the artwork radius and scale it to the reach.

An over-scale artwork is clipped by the reach circle, and a cropped plot still
looks like a complete drawing. These helpers are what the Qt "Fit to bed"
action uses to size the artwork so the whole drawing fits.
"""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


def _square(half):
    return [[(-half, -half), (half, -half), (half, half), (-half, half), (-half, -half)]]


class ArtworkRadiusTests(unittest.TestCase):
    def test_radius_is_measured_from_the_bounding_box_center(self):
        # A square whose corners sit on a circle of radius sqrt(2) * half.
        self.assertAlmostEqual(
            converter.artwork_radius(_square(10.0)),
            10.0 * 2.0 ** 0.5,
            places=9,
        )

    def test_offset_artwork_is_measured_after_being_centered(self):
        square = [[(x + 100.0, y + 40.0) for x, y in _square(10.0)[0]]]
        self.assertAlmostEqual(
            converter.artwork_radius(square),
            10.0 * 2.0 ** 0.5,
            places=9,
            msg="placement is removed before the radius decides whether it fits",
        )

    def test_empty_artwork_has_no_radius(self):
        self.assertEqual(converter.artwork_radius([]), 0.0)
        self.assertEqual(converter.artwork_radius([[(0.0, 0.0)]]), 0.0)


class FitScaleTests(unittest.TestCase):
    def test_artwork_inside_the_reach_is_left_alone(self):
        self.assertEqual(converter.fit_scale_to_radius(_square(10.0), 200.0), 1.0)

    def test_oversized_artwork_scales_until_it_fits_with_margin(self):
        limit = 191.4
        contours = _square(500.0)
        factor = converter.fit_scale_to_radius(contours, limit)
        self.assertLess(factor, 1.0)
        scaled = [
            [(x * factor, y * factor) for x, y in contour] for contour in contours
        ]
        fitted = converter.artwork_radius(scaled)
        self.assertLessEqual(fitted, limit)
        self.assertAlmostEqual(fitted, limit * 0.98, places=6)

    def test_artwork_exactly_at_the_reach_gains_the_margin(self):
        factor = converter.fit_scale_to_radius(_square(100.0), 100.0 * 2.0 ** 0.5)
        self.assertLess(factor, 1.0)

    def test_unknown_geometry_is_a_no_op(self):
        self.assertEqual(converter.fit_scale_to_radius([], 191.4), 1.0)
        self.assertEqual(converter.fit_scale_to_radius(_square(10.0), 0.0), 1.0)
        self.assertEqual(converter.fit_scale_to_radius(_square(10.0), -5.0), 1.0)

    def test_scaling_up_is_never_requested(self):
        # Fit to bed only ever shrinks: enlarging artwork that already fits
        # would silently change the user's Scale for no reason.
        self.assertEqual(converter.fit_scale_to_radius(_square(1.0), 1000.0), 1.0)


if __name__ == "__main__":
    unittest.main()
