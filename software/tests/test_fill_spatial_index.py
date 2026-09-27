"""The fill spatial index must be pure acceleration.

`_PolygonGrid` exists because a compound path can carry thousands of subpaths
(the F15 cutaway has 4,875) and the fill code used to test every one of them for
every hatch row and every inset query. The grid must only reduce how many exact
predicates run -- never which answers they produce.

These tests drive the indexed and unindexed paths with the same inputs and
require identical results, so a future change to the grid cannot silently alter
geometry.
"""

import math
import random
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from converter_core import geometry as geometry


def _random_polygons(count, seed, extent=200.0):
    """A polygon soup with a mix of sizes, overlaps, and nesting."""
    rng = random.Random(seed)
    polygons = []
    for index in range(count):
        if index % 7 == 0:
            # A large ring that nests several of the small polygons.
            cx, cy, r = extent * 0.5, extent * 0.5, extent * 0.45
            steps = 16
            outer = [
                (cx + r * math.cos(2 * math.pi * i / steps),
                 cy + r * math.sin(2 * math.pi * i / steps))
                for i in range(steps + 1)
            ]
            polygons.append(outer)
            continue
        cx = rng.uniform(5.0, extent - 5.0)
        cy = rng.uniform(5.0, extent - 5.0)
        size = rng.uniform(1.0, 12.0)
        corners = rng.randint(3, 5)
        poly = [
            (cx + size * math.cos(2 * math.pi * i / corners),
             cy + size * math.sin(2 * math.pi * i / corners))
            for i in range(corners)
        ]
        polygons.append(poly)
    return polygons


class FillSpatialIndexTests(unittest.TestCase):
    def setUp(self):
        self.polygons = _random_polygons(120, seed=20260927)
        self.index = geometry._PolygonGrid(self.polygons)

    def test_grid_engages_above_the_threshold(self):
        self.assertTrue(self.index.enabled)
        small = _random_polygons(3, seed=7)
        self.assertFalse(
            geometry._PolygonGrid(small).enabled,
            "small regions must keep the original unindexed path",
        )

    def test_indexed_segment_clipping_is_identical(self):
        rng = random.Random(11)
        for _ in range(400):
            a = (rng.uniform(-20.0, 220.0), rng.uniform(-20.0, 220.0))
            b = (rng.uniform(-20.0, 220.0), rng.uniform(-20.0, 220.0))
            self.assertEqual(
                geometry.clip_segment_to_region(a, b, self.polygons),
                geometry.clip_segment_to_region(a, b, self.polygons, self.index),
                msg=f"segment {a} -> {b}",
            )

    def test_indexed_even_odd_is_identical(self):
        rng = random.Random(13)
        for _ in range(2000):
            point = (rng.uniform(-20.0, 220.0), rng.uniform(-20.0, 220.0))
            self.assertEqual(
                geometry._point_in_polygons_even_odd(point, self.polygons),
                geometry._point_in_polygons_even_odd(point, self.polygons, self.index),
                msg=f"point {point}",
            )

    def test_hatch_lattice_is_identical_with_and_without_the_index(self):
        # Exercise the real entry point: it builds the grid internally, so this
        # guards the wiring rather than just the grid class.
        polygons = self.polygons
        indexed = geometry.line_region_contours(polygons, 3.0, 45.0)

        def unindexed(polygons, spacing, angle):
            ang = math.radians(angle)
            ca, sa = math.cos(ang), math.sin(ang)
            min_x, min_y, max_x, max_y = geometry.rotated_region_bounds(polygons, angle)
            out = []
            y = math.floor(min_y / spacing) * spacing
            row = 0
            while y <= max_y:
                start = (min_x - spacing, y)
                end = (max_x + spacing, y)
                a = (start[0] * ca - start[1] * sa, start[0] * sa + start[1] * ca)
                b = (end[0] * ca - end[1] * sa, end[0] * sa + end[1] * ca)
                segments = geometry.clip_segment_to_region(a, b, polygons)
                if row % 2:
                    segments = [[seg[1], seg[0]] for seg in reversed(segments)]
                out.extend(segments)
                y += spacing
                row += 1
            return out

        self.assertEqual(indexed, unindexed(polygons, 3.0, 45.0))
        self.assertTrue(indexed, "the fixture should produce hatch segments")

    def test_pull_back_never_leaves_the_fill_region(self):
        # The bleed margin must shorten a pass, never move ink outside the fill.
        # Offsetting the region per subpath used to do the latter.
        for pull in (0.2, 0.5):
            segments = geometry.line_region_contours(self.polygons, 3.0, 45.0, None, pull)
            self.assertTrue(segments)
            for segment in segments:
                for point in segment:
                    self.assertTrue(
                        geometry.point_in_region(point, self.polygons),
                        msg=f"pull_back={pull} endpoint {point} escaped the fill region",
                    )

    def test_pull_back_shortens_passes(self):
        def total(segments):
            return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segments)

        base = geometry.line_region_contours(self.polygons, 3.0, 45.0, None, 0.0)
        pulled = geometry.line_region_contours(self.polygons, 3.0, 45.0, None, 0.4)

        self.assertTrue(base)
        self.assertTrue(pulled)
        self.assertLessEqual(len(pulled), len(base))
        self.assertLess(total(pulled), total(base))


if __name__ == "__main__":
    unittest.main()
