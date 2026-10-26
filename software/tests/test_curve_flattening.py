"""Regression tests for SVG curve flattening density and accuracy."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


def _point_segment_distance(point, start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-18:
        return math.hypot(point[0] - start[0], point[1] - start[1])
    t = (
        (point[0] - start[0]) * dx
        + (point[1] - start[1]) * dy
    ) / length_sq
    t = max(0.0, min(1.0, t))
    nearest = (start[0] + t * dx, start[1] + t * dy)
    return math.hypot(point[0] - nearest[0], point[1] - nearest[1])


def _polyline_error(points, curve):
    return max(
        min(
            _point_segment_distance(curve(t), start, end)
            for start, end in zip(points, points[1:])
        )
        for t in (index / 500.0 for index in range(501))
    )


def _polyline_error_for_curves(points, curves):
    return max(
        min(
            _point_segment_distance(curve(t), start, end)
            for curve in curves
            for start, end in zip(points, points[1:])
        )
        for t in (index / 500.0 for index in range(501))
    )


class CurveFlatteningTests(unittest.TestCase):
    def test_shallow_cubics_are_not_forced_to_eight_segments(self):
        # This is the mandala failure pattern: many short, nearly straight
        # cubic segments that are already within tolerance as one chord.
        path = "M 0,0 " + "c 0,0.01 0.02,0.01 0.02,0 " * 1000
        contours = converter.path_to_contours(path, tolerance=0.05)

        self.assertEqual(len(contours), 1)
        self.assertLessEqual(len(contours[0]), 1500)
        self.assertLess(len(contours[0]), 8001)

    def test_adaptive_flattening_keeps_a_curved_cubic_within_tolerance(self):
        tolerance = 0.10
        p0 = (0.0, 0.0)
        c1 = (0.0, 10.0)
        c2 = (10.0, 10.0)
        p3 = (10.0, 0.0)
        path = "M 0,0 C 0,10 10,10 10,0"
        contours = converter.path_to_contours(path, tolerance=tolerance)

        self.assertEqual(len(contours), 1)
        error = _polyline_error(
            contours[0],
            lambda t: converter.cubic(p0, c1, c2, p3, t),
        )
        self.assertLessEqual(error, tolerance + 1e-9)

    def test_adaptive_flattening_does_not_collapse_a_curve_loop(self):
        tolerance = 0.05
        p0 = (0.0, 0.0)
        c1 = (10.0, 10.0)
        c2 = (-10.0, -10.0)
        p3 = (0.0, 0.0)
        path = "M 0,0 C 10,10 -10,-10 0,0"
        contours = converter.path_to_contours(path, tolerance=tolerance)

        self.assertEqual(len(contours), 1)
        self.assertGreater(len(contours[0]), 2)
        error = _polyline_error(
            contours[0],
            lambda t: converter.cubic(p0, c1, c2, p3, t),
        )
        self.assertLessEqual(error, tolerance + 1e-9)

    def test_quadratic_and_smooth_continuation_obey_tolerance(self):
        tolerance = 0.05
        first = (
            (0.0, 0.0),
            (5.0, 10.0),
            (10.0, 0.0),
        )
        second = (
            (10.0, 0.0),
            (15.0, -10.0),
            (20.0, 0.0),
        )
        contours = converter.path_to_contours(
            "M 0,0 Q 5,10 10,0 T 20,0",
            tolerance=tolerance,
        )

        self.assertEqual(len(contours), 1)
        error = _polyline_error_for_curves(
            contours[0],
            (
                lambda t: converter.quad(*first, t),
                lambda t: converter.quad(*second, t),
            ),
        )
        self.assertLessEqual(error, tolerance + 1e-9)


if __name__ == "__main__":
    unittest.main()
