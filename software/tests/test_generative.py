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


def _fingerprint(contours):
    """A cheap stand-in for a full comparison of thousands of points.

    Comparing or diffing two multi-hundred-contour designs directly makes
    unittest build a difflib report over a huge repr, which is slow enough to
    look like a hang.
    """
    if not contours:
        return (0, 0)
    return (
        len(contours),
        _point_count(contours),
        tuple(round(value, 9) for value in contours[0][0]),
        tuple(round(value, 9) for value in contours[-1][-1]),
    )


class RandomPatternTests(unittest.TestCase):
    def test_same_seed_reproduces_the_same_drawing(self):
        first = converter.random_pattern(seed=7, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0)
        second = converter.random_pattern(seed=7, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0)
        self.assertTrue(first)
        self.assertEqual(first, second)

    def test_different_seeds_produce_different_drawings(self):
        first = converter.random_pattern(seed=3, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0)
        second = converter.random_pattern(seed=4, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0)
        self.assertNotEqual(_fingerprint(first), _fingerprint(second))

    def test_seeds_produce_structurally_different_designs(self):
        styles = set()
        contours = []
        points = []
        for seed in range(8):
            pattern = converter.random_pattern(
                seed=seed, intricacy=8, radius_mm=RADIUS, wedge_deg=15.0
            )
            styles.add(generative.style_for(seed))
            contours.append(len(pattern))
            points.append(_point_count(pattern))
        self.assertGreaterEqual(len(styles), 3, "seeds should draw from several styles")
        self.assertGreaterEqual(len(set(contours)), 6, "ring make-up should vary")
        self.assertGreaterEqual(len(set(points)), 6, "drawing volume should vary")
        self.assertGreater(
            max(points) / min(points), 1.3, "seeds should differ in weight, not just phases"
        )

    def test_higher_intricacy_adds_detail_without_losing_any(self):
        # Contour counts can dip slightly when a level adds rings but thins the
        # bands; the amount of drawing (points) only ever grows.
        counts = []
        for level in (1, 4, 7, 10):
            pattern = converter.random_pattern(
                seed=11, intricacy=level, radius_mm=RADIUS, wedge_deg=15.0
            )
            counts.append((len(pattern), _point_count(pattern)))
        for index in range(1, len(counts)):
            self.assertGreater(counts[index][1], counts[index - 1][1])
        self.assertGreater(counts[-1][0], counts[0][0])

    def test_top_intricacy_is_dense(self):
        pattern = converter.random_pattern(
            seed=4, intricacy=10, radius_mm=RADIUS, wedge_deg=15.0
        )
        self.assertGreaterEqual(
            len(pattern), 300, "max intricacy should fill the wedge with shapes"
        )
        self.assertGreaterEqual(_point_count(pattern), 9000)
        design = converter.kaleidoscope(pattern, 12, mirror=True, radius=RADIUS)
        self.assertGreaterEqual(
            len(design), 8000, "mirrored design should be an engraving, not a sketch"
        )

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
            if len(contour) != 2 or math.dist(contour[0], contour[1]) < 10.0:
                continue
            # Radial spokes, slanted mesh strokes and circle facet edges are
            # honest straight lines. The artefact to catch is a piece fused
            # across a clipped gap: one end sitting on the clip frame and the
            # other end well inside it at a different angle.
            first, second = contour
            first_r, second_r = math.hypot(*first), math.hypot(*second)
            on_frame = min(abs(first_r - RADIUS), abs(second_r - RADIUS)) < 0.05
            ends_inside = max(first_r, second_r) < RADIUS - 5.0
            dr = abs(first_r - second_r)
            da = abs(math.atan2(first[1], first[0]) - math.atan2(second[1], second[0]))
            self.assertTrue(
                dr < 1.5 or da < math.radians(2.0) or not (on_frame and ends_inside),
                "clipping fused a piece across the frame (dr=%.2f mm, da=%.1f deg)"
                % (dr, math.degrees(da)),
            )


def _square_motif(size=20.0):
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


class NaturalMotifTests(unittest.TestCase):
    def test_motifs_replace_the_shape_rings(self):
        motif = _square_motif()
        plain = converter.random_pattern(
            seed=5, intricacy=7, radius_mm=RADIUS, wedge_deg=15.0
        )
        with_motifs = converter.random_pattern(
            seed=5, intricacy=7, radius_mm=RADIUS, wedge_deg=15.0, motifs=[motif]
        )
        self.assertNotEqual(_fingerprint(plain), _fingerprint(with_motifs))
        self.assertIn(5, {len(contour) for contour in with_motifs})

    def test_placed_motifs_overlap_their_band_but_stay_inside_bounds(self):
        wedge = math.radians(15.0)
        diamond = [
            [(0.0, -30.0), (30.0, 0.0), (0.0, 30.0), (-30.0, 0.0), (0.0, -30.0)]
        ]
        for seed in (1, 4, 9):
            placed = generative._motif_ring(
                [diamond],
                100.0,
                150.0,
                wedge,
                6,
                seed=seed,
                limit=181.3,
                floor=5.0,
            )
            self.assertTrue(placed)
            beyond = 0
            for contour in placed:
                for x, y in contour:
                    radius = math.hypot(x, y)
                    self.assertGreaterEqual(radius, 5.0 - 1e-6)
                    self.assertLessEqual(radius, 181.3 + 1e-6)
                    if radius > 150.0:
                        beyond += 1
                    angle = math.atan2(y, x)
                    self.assertGreaterEqual(angle, -0.3)
                    self.assertLessEqual(angle, wedge + 0.3)
            self.assertGreater(beyond, 0, "motifs should overlap into the next ring")

    def test_motif_plan_is_deterministic_and_bounded(self):
        self.assertEqual(
            converter.motif_plan(seed=12, intricacy=8, count=5),
            converter.motif_plan(seed=12, intricacy=8, count=5),
        )
        plan = converter.motif_plan(seed=12, intricacy=8, count=5)
        self.assertTrue(plan)
        indices = [index for pool in plan for index in pool]
        self.assertTrue(indices)
        self.assertTrue(all(0 <= index < 5 for index in indices))
        # Only the outer two rings carry motifs: engravings are far too
        # detailed to tile through the whole design.
        self.assertEqual(plan[-1], sorted(plan[-1]))
        self.assertTrue(all(plan[-2:]), "the outer two rings draw motifs")
        self.assertEqual(
            sum(1 for pool in plan if pool),
            min(2, len(plan)),
            "nothing but the outer rings uses the motif pool",
        )
        self.assertGreater(max(len(pool) for pool in plan), 1)
        self.assertLess(
            len(converter.motif_plan(11, 4, 9)),
            len(converter.motif_plan(11, 10, 9)),
        )
        self.assertEqual(converter.motif_plan(0, 5, 0), [])

    def test_empty_motifs_fall_back_to_the_drawn_families(self):
        plain = converter.random_pattern(
            seed=8, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0
        )
        fallback = converter.random_pattern(
            seed=8, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0, motifs=[[]]
        )
        with_motif = converter.random_pattern(
            seed=8, intricacy=6, radius_mm=RADIUS, wedge_deg=15.0, motifs=[_square_motif()]
        )
        self.assertTrue(fallback, "an empty motif list must not empty the design")
        self.assertGreater(len(fallback), 0.5 * len(plain))
        self.assertNotEqual(_fingerprint(fallback), _fingerprint(with_motif))

    def test_motif_choice_varies_with_the_seed(self):
        thin = [
            [(0.0, -30.0), (30.0, 0.0), (0.0, 30.0), (-30.0, 0.0), (0.0, -30.0)]
        ]
        plans = {
            tuple(tuple(pool) for pool in converter.motif_plan(seed, 8, 3))
            for seed in range(10)
        }
        self.assertGreater(len(plans), 1)
        for seed in range(4):
            pattern = converter.random_pattern(
                seed=seed,
                intricacy=8,
                radius_mm=RADIUS,
                wedge_deg=15.0,
                motifs=[_square_motif(), thin, _square_motif(40.0)],
            )
            self.assertTrue(pattern)


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
