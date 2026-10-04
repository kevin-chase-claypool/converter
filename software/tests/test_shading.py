"""Popular photo-shading fills: stipple, halftone, and single-line (TSP).

These styles read tone directly - stipple as dot density, halftone as dot size,
and single-line as the density of a connected point tour - so they are drawn at
the requested pitch and ignore ``Shade levels``.  The tests pin the core
properties (density follows tone, minimum spacing is honoured, output is
reproducible, and the line visits every point once) plus the settings contract
the sidebar drives.
"""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


def _min_pairwise_distance(points):
    best = math.inf
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            dx = points[i][0] - points[j][0]
            dy = points[i][1] - points[j][1]
            best = min(best, math.hypot(dx, dy))
    return best


def _circle_radius(circle):
    first = circle[0]
    unique = [first]
    for point in circle[1:]:
        if math.hypot(point[0] - first[0], point[1] - first[1]) > 1e-9:
            unique.append(point)
    cx = sum(point[0] for point in unique) / len(unique)
    cy = sum(point[1] for point in unique) / len(unique)
    return max(math.hypot(point[0] - cx, point[1] - cy) for point in unique)


class ShadingSettingsTests(unittest.TestCase):
    def test_patterns_are_registered_with_readable_labels(self):
        for value in ("stipple", "halftone", "tsp"):
            self.assertIn(value, converter.HATCH_PATTERNS)
            self.assertEqual(converter.normalized_hatch_pattern(value), value)
        for label in (
            "stipple (tone dots)",
            "halftone (variable dots)",
            "single line (tsp)",
        ):
            self.assertIn(label, converter.HATCH_PATTERN_LABELS.values())

    def test_aliases_resolve_to_the_canonical_patterns(self):
        self.assertEqual(converter.normalized_hatch_pattern("stippling"), "stipple")
        self.assertEqual(converter.normalized_hatch_pattern("pointillism"), "stipple")
        self.assertEqual(converter.normalized_hatch_pattern("half-tone"), "halftone")
        self.assertEqual(converter.normalized_hatch_pattern("screen"), "halftone")
        self.assertEqual(converter.normalized_hatch_pattern("single line"), "tsp")
        self.assertEqual(converter.normalized_hatch_pattern("one line"), "tsp")

    def test_dot_based_patterns_share_the_dot_spacing_field(self):
        for pattern in ("dots", "stipple", "halftone", "tsp"):
            self.assertEqual(
                converter.PATTERN_SIZE_FIELDS[pattern],
                "dot_spacing_mm",
                pattern,
            )

    def test_defaults_are_valid(self):
        converter.validate_settings(converter.Settings())


class StippleTests(unittest.TestCase):
    def test_density_follows_tone(self):
        bounds = (0.0, 0.0, 100.0, 100.0)
        inside = lambda x, y: True
        dark = converter.stipple_points(
            bounds, inside, lambda x, y: 1.0, min_dist=6.0, seed=0
        )
        grey = converter.stipple_points(
            bounds, inside, lambda x, y: 0.5, min_dist=6.0, seed=0
        )
        light = converter.stipple_points(
            bounds, inside, lambda x, y: 0.1, min_dist=6.0, seed=0
        )
        self.assertTrue(dark)
        self.assertGreater(len(dark), len(grey))
        self.assertGreater(len(grey), len(light))

    def test_minimum_spacing_is_honoured(self):
        points = converter.stipple_points(
            (0.0, 0.0, 100.0, 100.0),
            lambda x, y: True,
            lambda x, y: 1.0,
            min_dist=6.0,
            seed=1,
        )
        self.assertGreater(len(points), 10)
        self.assertGreaterEqual(_min_pairwise_distance(points), 6.0 - 1e-9)

    def test_output_is_reproducible_for_a_seed(self):
        args = ((0.0, 0.0, 50.0, 50.0), lambda x, y: True, lambda x, y: 0.8)
        first = converter.stipple_points(*args, min_dist=4.0, seed=7)
        second = converter.stipple_points(*args, min_dist=4.0, seed=7)
        self.assertEqual(first, second)

    def test_white_paper_gets_no_ink(self):
        points = converter.stipple_points(
            (0.0, 0.0, 100.0, 100.0),
            lambda x, y: True,
            lambda x, y: 0.0,
            min_dist=6.0,
            seed=0,
        )
        self.assertEqual(points, [])


class StippleDotSizeTests(unittest.TestCase):
    def test_dot_radius_never_shrinks_below_a_pen_tip(self):
        self.assertGreaterEqual(converter.stipple_mark_radius(0.0), 0.25)
        self.assertGreaterEqual(converter.stipple_mark_radius(0.8), 0.4)

    def test_each_point_becomes_one_closed_dot_circle(self):
        marks = converter.dot_mark_contours([(1.0, 2.0), (5.0, 6.0)], 0.75)
        self.assertEqual(len(marks), 2)
        for mark, (x, y) in zip(marks, [(1.0, 2.0), (5.0, 6.0)]):
            self.assertGreater(len(mark), 6)
            self.assertEqual(mark[0], mark[-1])
            radius = math.hypot(mark[0][0] - x, mark[0][1] - y)
            self.assertAlmostEqual(radius, 0.75, places=6)

    def test_dots_survive_the_geometry_filter_at_a_bed_filling_scale(self):
        """Regression: a bed-filling photo's dots were dropped as slivers.

        The fill is generated in view units and then scaled to paper, where
        ``apply_geometry_settings`` removes anything shorter than 1 mm. A dot
        drawn as a fraction of the fill spacing vanished at real photo scales;
        it must instead be a paper-sized circle about one pen tip across.
        """
        square = [(0.0, 0.0), (300.0, 0.0), (300.0, 400.0), (0.0, 400.0)]
        scale = 0.3
        unit_per_mm = 1.0 / scale
        contours = converter.fill_region_pattern_contours(
            [square],
            4.0 * unit_per_mm,
            0.0,
            1,
            90.0,
            0.6,
            "stipple",
            unit_per_mm=unit_per_mm,
            pen_diameter_mm=0.2,
        )
        self.assertTrue(contours)
        settings = converter.Settings(scale=scale, hatch_pattern="stipple")
        paper = converter.apply_geometry_settings(contours, settings)
        self.assertTrue(paper, "stipple dots must survive the sub-pen-width filter")
        spans = [
            max(x for x, _ in contour) - min(x for x, _ in contour)
            for contour in paper
        ]
        # A 0.25 mm dot radius is 0.5 mm across on paper before pen width.
        self.assertGreater(min(spans), 0.3)


class HalftoneTests(unittest.TestCase):
    def test_dot_radius_follows_tone(self):
        full = converter.halftone_contours(
            (0.0, 0.0, 100.0, 100.0),
            lambda x, y: True,
            lambda x, y: 1.0,
            spacing=10.0,
        )
        half = converter.halftone_contours(
            (0.0, 0.0, 100.0, 100.0),
            lambda x, y: True,
            lambda x, y: 0.5,
            spacing=10.0,
        )
        self.assertTrue(full)
        self.assertGreater(_circle_radius(full[0]), _circle_radius(half[0]))

    def test_blank_paper_gets_no_dots(self):
        dots = converter.halftone_contours(
            (0.0, 0.0, 100.0, 100.0),
            lambda x, y: True,
            lambda x, y: 0.0,
            spacing=10.0,
        )
        self.assertEqual(dots, [])

    def test_radius_is_bounded_by_half_the_pitch(self):
        dots = converter.halftone_contours(
            (0.0, 0.0, 100.0, 100.0),
            lambda x, y: True,
            lambda x, y: 1.0,
            spacing=10.0,
        )
        self.assertLessEqual(_circle_radius(dots[0]), 5.0 + 1e-9)


class SingleLineTests(unittest.TestCase):
    def test_line_visits_every_point_once(self):
        points = converter.stipple_points(
            (0.0, 0.0, 100.0, 100.0),
            lambda x, y: True,
            lambda x, y: 1.0,
            min_dist=8.0,
            seed=0,
        )
        line = converter.greedy_single_line(points, cell=8.0)
        self.assertEqual(len(line), len(points))
        self.assertEqual(len(set(line)), len(points))

    def test_empty_and_single_point_inputs(self):
        self.assertEqual(converter.greedy_single_line([]), [])
        self.assertEqual(converter.greedy_single_line([(1.0, 2.0)]), [(1.0, 2.0)])


class VectorFillTests(unittest.TestCase):
    def test_shading_patterns_fill_a_shape(self):
        square = [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0), (0.0, 40.0)]
        for pattern in ("stipple", "halftone", "tsp"):
            with self.subTest(pattern=pattern):
                contours = converter.fill_pattern_contours(
                    square, 6.0, 0.0, 1, 90.0, 1.0, pattern
                )
                self.assertTrue(contours, pattern)
                points = [point for contour in contours for point in contour]
                self.assertGreaterEqual(min(x for x, _ in points), -1e-6)
                self.assertLessEqual(max(x for x, _ in points), 40.0 + 1e-6)
                self.assertGreaterEqual(min(y for _, y in points), -1e-6)
                self.assertLessEqual(max(y for _, y in points), 40.0 + 1e-6)


if __name__ == "__main__":
    unittest.main()
