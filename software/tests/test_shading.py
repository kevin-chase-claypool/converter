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


class TerrainTests(unittest.TestCase):
    def test_pattern_is_registered_with_readable_label(self):
        self.assertIn("terrain", converter.HATCH_PATTERNS)
        self.assertEqual(converter.normalized_hatch_pattern("terrain"), "terrain")
        self.assertEqual(
            converter.PATTERN_SIZE_FIELDS["terrain"], "terrain_size_mm"
        )
        self.assertEqual(
            converter.HATCH_PATTERN_LABELS["terrain"],
            "terrain (topographic contours)",
        )
        for alias in ("topographic", "topo", "contour", "contours"):
            self.assertEqual(converter.normalized_hatch_pattern(alias), "terrain")

    def test_height_field_is_deterministic(self):
        first = converter.terrain_height(11.0, 7.0, 40.0)
        second = converter.terrain_height(11.0, 7.0, 40.0)
        self.assertEqual(first, second)
        self.assertNotEqual(first, converter.terrain_height(11.0, 7.0, 40.0, seed=3))

    def test_contours_stay_inside_the_bounds_and_chain(self):
        bounds = (0.0, 0.0, 120.0, 90.0)
        lines = converter.terrain_contours(bounds, 4.0)
        self.assertTrue(lines)
        for line in lines:
            self.assertGreaterEqual(len(line), 2)
            for x, y in line:
                self.assertGreaterEqual(x, bounds[0] - 1e-9)
                self.assertLessEqual(x, bounds[2] + 1e-9)
                self.assertGreaterEqual(y, bounds[1] - 1e-9)
                self.assertLessEqual(y, bounds[3] + 1e-9)
        # A marching-squares segment is two points; a chained contour is longer.
        self.assertGreater(max(len(line) for line in lines), 10)

    def test_tighter_spacing_draws_more_contour_length(self):
        def total_length(spacing):
            return sum(
                sum(
                    math.hypot(b[0] - a[0], b[1] - a[1])
                    for a, b in zip(line, line[1:])
                )
                for line in converter.terrain_contours((0.0, 0.0, 120.0, 120.0), spacing)
            )

        wide = total_length(6.0)
        tight = total_length(2.0)
        self.assertGreater(wide, 0.0)
        # Area / pitch: a pitch three times tighter draws about three times
        # the length, and the calibration only promises the same order.
        self.assertGreater(tight / wide, 2.0)

    def test_vector_fill_darkens_with_shade_levels(self):
        square = [(0.0, 0.0), (80.0, 0.0), (80.0, 80.0), (0.0, 80.0)]

        def length(darkness):
            contours = converter.fill_pattern_contours(
                square, 5.0, 0.0, 4, 90.0, darkness, "terrain"
            )
            return sum(
                sum(
                    math.hypot(b[0] - a[0], b[1] - a[1])
                    for a, b in zip(contour, contour[1:])
                )
                for contour in contours
            )

        self.assertGreater(length(1.0), 0.0)
        self.assertGreater(length(1.0), length(0.25))

    def test_vector_fill_is_clipped_to_the_region(self):
        triangle = [(10.0, 10.0), (90.0, 10.0), (50.0, 80.0)]
        contours = converter.fill_pattern_contours(
            triangle, 4.0, 0.0, 1, 90.0, 1.0, "terrain"
        )
        self.assertTrue(contours)
        # All four corners of the bounding box are outside the triangle, so a
        # leak would put a point near one of them.
        tol = 1e-6
        for contour in contours:
            for x, y in contour:
                self.assertGreaterEqual(y, 10.0 - tol)
                self.assertLessEqual(y, 80.0 + tol)
                for (ax, ay), (bx, by) in zip(triangle, triangle[1:] + triangle[:1]):
                    cross = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
                    self.assertGreaterEqual(cross, -tol, (x, y))

    def test_grid_is_capped_for_a_pathological_spacing(self):
        lines = converter.terrain_contours(
            (0.0, 0.0, 1000.0, 1000.0), 0.05, max_cells=4096
        )
        self.assertTrue(lines)
        points = sum(len(line) for line in lines)
        self.assertLess(points, 200000)


class ToneTerrainTests(unittest.TestCase):
    """The image-tone terrain traces the photo's own shading."""

    def test_a_ramp_draws_vertical_lines_at_the_requested_gap(self):
        bounds = (0.0, 0.0, 100.0, 60.0)
        lines = converter.tone_terrain_contours(
            bounds, 5.0, lambda x, y: x / 100.0
        )
        self.assertTrue(lines)
        positions = []
        for line in lines:
            xs = sorted({round(point[0], 3) for point in line})
            self.assertLessEqual(xs[-1] - xs[0], 1e-6, "a ramp level set is vertical")
            positions.append(0.5 * (xs[0] + xs[-1]))
        positions.sort()
        gaps = [b - a for a, b in zip(positions, positions[1:])]
        self.assertGreater(len(gaps), 3)
        for gap in gaps:
            self.assertAlmostEqual(gap, 5.0, delta=1.0)

    def test_a_hard_edge_is_thinned_to_a_few_lines(self):
        # A dark disc on a white field is a tone cliff. Every level crosses it
        # in the same few millimetres, so without the separation pass the edge
        # stacks into a heavy band ("too much on outlines").
        def darkness(x, y):
            return 0.8 if math.hypot(x - 50.0, y - 50.0) <= 30.0 else 0.0

        lines = converter.tone_terrain_contours(
            (0.0, 0.0, 100.0, 100.0), 3.0, darkness, blur=1.0
        )
        self.assertTrue(lines)
        self.assertLessEqual(len(lines), 3)
        for line in lines:
            for x, y in line:
                radius = math.hypot(x - 50.0, y - 50.0)
                self.assertGreaterEqual(radius, 25.0)
                self.assertLessEqual(radius, 35.0)
        rough = converter.tone_terrain_contours(
            (0.0, 0.0, 100.0, 100.0), 3.0, darkness, blur=1.0, separation=0.0
        )
        self.assertGreater(len(rough), len(lines))

    def test_thin_strokes_are_drawn_once_each(self):
        centres = (80.0, 200.0, 320.0, 440.0)

        def darkness(x, y):
            return 0.9 if any(abs(y - centre) <= 1.0 for centre in centres) else 0.0

        lines = converter.tone_terrain_contours(
            (0.0, 0.0, 600.0, 520.0), 20.0, darkness, step=2.0, blur=4.0
        )
        for centre in centres:
            near = [
                line
                for line in lines
                if abs(sum(point[1] for point in line) / len(line) - centre) < 10.0
            ]
            self.assertTrue(near, f"stroke at {centre} lost")
            self.assertLessEqual(len(near), 2, f"stroke at {centre} stacked")

    def test_a_flat_field_draws_nothing(self):
        self.assertEqual(
            converter.tone_terrain_contours((0.0, 0.0, 50.0, 50.0), 4.0, lambda x, y: 0.5),
            [],
        )
        self.assertEqual(
            converter.tone_terrain_contours((0.0, 0.0, 50.0, 50.0), 4.0, lambda x, y: 0.0),
            [],
        )

    def test_a_thin_dark_line_still_draws_at_a_coarse_spacing(self):
        # A scanned line has one enormous slope and no area: without the
        # single-level fallback the ladder exceeds the tone range and nothing
        # is drawn at all.
        darkness = lambda x, y: 1.0 if abs(y - 25.0) < 0.5 else 0.0
        lines = converter.tone_terrain_contours(
            (0.0, 0.0, 60.0, 50.0), 40.0, darkness, step=1.0, blur=1.0
        )
        self.assertTrue(lines)
        for line in lines:
            for x, y in line:
                self.assertAlmostEqual(y, 25.0, delta=2.0)

    def test_smoothing_turns_a_cliff_into_a_slope(self):
        # A hard edge stacks every level in one cell; the smoothing radius is
        # what turns that cliff into the graded band of a real hillside.
        bounds = (0.0, 0.0, 100.0, 60.0)
        darkness = lambda x, y: 1.0 if x > 50.0 else 0.0

        def spread(blur):
            lines = converter.tone_terrain_contours(bounds, 4.0, darkness, blur=blur)
            xs = [point[0] for line in lines for point in line]
            return max(xs) - min(xs)

        self.assertLess(spread(0.0), 4.0)
        self.assertGreater(spread(8.0), 6.0)

    def test_output_is_deterministic(self):
        def darkness(x, y):
            return 0.5 + 0.4 * math.sin(0.2 * x) * math.cos(0.3 * y)

        args = ((0.0, 0.0, 80.0, 80.0), 3.0, darkness)
        first = converter.tone_terrain_contours(*args, blur=1.0)
        second = converter.tone_terrain_contours(*args, blur=1.0)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
