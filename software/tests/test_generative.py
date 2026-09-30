"""Generative patterns: determinism, wedge contract, bands and bounds.

`random_pattern` feeds the same pipeline as an imported image, so these tests
pin down what the app relies on: a seed reproduces a drawing exactly, every
curve lives inside the band it claims, nothing leaves the wedge or the design
radius, and the mirrored result never gains stray straight chords.
"""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter
from converter_core import generative


RADIUS = 181.3


def _point_count(contours):
    return sum(len(contour) for contour in contours)


class RandomPatternTests(unittest.TestCase):
    def test_same_seed_reproduces_the_same_drawing(self):
        first = converter.random_pattern(seed=7, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0)
        second = converter.random_pattern(seed=7, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0)
        self.assertTrue(first)
        self.assertEqual(first, second)

    def test_different_seeds_produce_different_drawings(self):
        first = converter.random_pattern(seed=3, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0)
        second = converter.random_pattern(seed=4, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0)
        self.assertNotEqual(first, second)

    def test_higher_intricacy_adds_detail_without_losing_any(self):
        counts = []
        for level in (1, 4, 7, 10):
            pattern = converter.random_pattern(
                seed=11, intricacy=level, radius_mm=RADIUS, wedge_deg=15.0
            )
            counts.append((len(pattern), _point_count(pattern)))
        for index in range(1, len(counts)):
            self.assertGreaterEqual(counts[index][0], counts[index - 1][0])
            self.assertGreater(counts[index][1], counts[index - 1][1])

    def test_points_are_finite_and_inside_the_radius(self):
        for seed in (0, 5, 99999):
            for level in (1, 5, 10):
                pattern = converter.random_pattern(
                    seed=seed, intricacy=level, radius_mm=RADIUS, wedge_deg=15.0
                )
                self.assertTrue(pattern)
                for contour in pattern:
                    for x, y in contour:
                        self.assertTrue(math.isfinite(x) and math.isfinite(y))
                        self.assertLessEqual(
                            math.hypot(x, y), RADIUS + 1e-6, "pattern left its radius"
                        )

    def test_clipping_keeps_the_pattern_in_the_wedge(self):
        wedge_deg = 180.0 / 17
        wedge = math.radians(wedge_deg)
        pattern = converter.random_pattern(
            seed=21, intricacy=8, radius_mm=RADIUS, wedge_deg=wedge_deg
        )
        clipped = converter.clip_to_wedge(pattern, wedge_deg, radius=RADIUS)
        self.assertTrue(clipped)
        for contour in clipped:
            for x, y in contour:
                angle = math.atan2(y, x) % (2.0 * math.pi)
                if angle > math.pi:
                    angle -= 2.0 * math.pi
                self.assertLessEqual(angle, wedge + 1e-6)
                self.assertGreaterEqual(angle, -1e-6)
        kept = _point_count(clipped)
        self.assertGreater(
            kept, 0.8 * _point_count(pattern), "clipping threw away most of the pattern"
        )

    def test_mirrored_drawing_has_no_stray_chords(self):
        pattern = converter.random_pattern(
            seed=1, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0
        )
        design = converter.kaleidoscope(pattern, 12, mirror=True, radius=RADIUS)
        self.assertTrue(design)
        for contour in design:
            self.assertLessEqual(
                math.hypot(*contour[0]), RADIUS + 1e-6, "mirrored point left the frame"
            )
            if len(contour) == 2:
                self.assertLess(
                    math.dist(contour[0], contour[1]),
                    10.0,
                    "clipping left a long straight chord",
                )


class BandFamilyTests(unittest.TestCase):
    def test_every_family_stays_inside_its_band(self):
        wedge = math.radians(15.0)
        for name in generative.FAMILIES:
            function = generative._FUNCTIONS[name]
            for level in (1, 6, 10):
                contours = function(100.0, 150.0, wedge, level, seed=23)
                self.assertTrue(contours, "%s produced nothing at level %d" % (name, level))
                for contour in contours:
                    self.assertGreaterEqual(len(contour), 2)
                    for x, y in contour:
                        radius = math.hypot(x, y)
                        self.assertGreaterEqual(radius, 100.0 - 1e-6, name)
                        self.assertLessEqual(radius, 150.0 + 1e-6, name)
                        angle = math.atan2(y, x)
                        # Beads and centre circles may overhang a seam a little;
                        # the caller's clip and mirror completes them. Anything
                        # grosser than a bead's angular size is a real mistake.
                        self.assertGreaterEqual(angle, -0.15, name)
                        self.assertLessEqual(angle, wedge + 0.15, name)

    def test_sequences_are_low_discrepancy_and_repeatable(self):
        values = [generative.van_der_corput(index, 2) for index in range(1, 64)]
        self.assertEqual(len(set(values)), len(values))
        self.assertTrue(all(0.0 <= value < 1.0 for value in values))
        self.assertEqual(generative.fibonacci(6), [1, 1, 2, 3, 5, 8])
        self.assertEqual(generative.primes(6), [2, 3, 5, 7, 11, 13])
        self.assertAlmostEqual(generative.weyl(0), 0.0)


if __name__ == "__main__":
    unittest.main()
