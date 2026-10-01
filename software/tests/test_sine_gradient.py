"""Gradient tone plotted as continuous adjacent sinusoids.

`sine_gradient` is the plotter-art gradient: instead of encoding tone as hatch
density it draws rows of sine curves whose amplitude is the rendered darkness
at that row, joined head to tail into one continuous stroke. These tests pin
the three properties the look depends on - amplitude follows tone, rows stay
adjacent and continuous, and blank paper stays blank - plus the settings
contract the Qt sidebar drives.
"""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


def _ramp_fading_right():
    """Fully dark at x = 0, white by x = 100 - a left-to-right gradient."""

    def darkness(x, _y):
        return max(0.0, min(1.0, 1.0 - x / 100.0))

    return darkness


class SineGradientSettingsTests(unittest.TestCase):
    def test_gradient_aliases_resolve_to_the_sine_gradient_pattern(self):
        for name in (
            "sine_gradient",
            "gradient",
            "gradient waves",
            "gradient-waves",
            "sine wave gradient",
            "continuous sine",
        ):
            self.assertEqual(converter.normalized_hatch_pattern(name), "sine_gradient", name)

    def test_settings_model_offers_the_pattern_and_its_controls(self):
        self.assertIn("sine_gradient", converter.HATCH_PATTERNS)
        self.assertLess(
            converter.HATCH_PATTERNS.index("sine_gradient"),
            3,
            "the sidebar shows this tuple in order and the gradient option must "
            "stay visible without scrolling the combo",
        )
        self.assertIn(
            "gradient waves (sine_gradient)",
            converter.HATCH_PATTERN_LABELS.values(),
            "the option must be findable by name in the Fill pattern list",
        )
        self.assertEqual(
            converter.PATTERN_SIZE_FIELDS["sine_gradient"],
            "wave_size_mm",
            "the sine gradient reuses the wave size field for its row spacing",
        )
        defaults = converter.Settings()
        self.assertEqual(defaults.gradient_wave_amplitude_pct, 50.0)
        self.assertEqual(defaults.gradient_wave_density_pct, 100.0)
        self.assertTrue(defaults.sine_rows_connected)

    def test_combo_labels_round_trip_to_the_stored_pattern(self):
        for value, label in converter.HATCH_PATTERN_LABELS.items():
            self.assertIn(value, converter.HATCH_PATTERNS)
            self.assertEqual(converter.normalized_hatch_pattern(label), value, label)
        # Labels are presentation only; the value in a settings file stays short.
        for value in converter.HATCH_PATTERNS:
            self.assertEqual(converter.normalized_hatch_pattern(value), value)

    def test_amplitude_cannot_exceed_one_row_spacing(self):
        converter.validate_settings(converter.Settings(gradient_wave_amplitude_pct=100.0))
        with self.assertRaises(ValueError):
            converter.validate_settings(converter.Settings(gradient_wave_amplitude_pct=100.1))
        with self.assertRaises(ValueError):
            converter.validate_settings(converter.Settings(gradient_wave_amplitude_pct=-1.0))
        converter.validate_settings(converter.Settings(gradient_wave_density_pct=400.0))
        with self.assertRaises(ValueError):
            converter.validate_settings(converter.Settings(gradient_wave_density_pct=400.1))


class SineGradientGeometryTests(unittest.TestCase):
    BOUNDS = (0.0, 0.0, 100.0, 40.0)
    SPACING = 4.0

    def _rows(self, darkness=None, **kwargs):
        darkness = darkness or _ramp_fading_right()
        return converter.sine_gradient_region_contours(
            self.BOUNDS, darkness, self.SPACING, 0.0, connect_rows=False, **kwargs
        )

    @staticmethod
    def _window_spread(contour, x_lo, x_hi):
        band = [point[1] for point in contour if x_lo <= point[0] <= x_hi]
        if len(band) < 2:
            return 0.0
        return max(band) - min(band)

    def test_amplitude_follows_the_local_tone(self):
        rows = self._rows()
        self.assertTrue(rows, "a dark gradient must produce wave rows")
        dark_spreads = sorted(self._window_spread(row, 0.0, 8.0) for row in rows)
        light_spreads = sorted(self._window_spread(row, 92.0, 100.0) for row in rows)
        median_dark = dark_spreads[len(dark_spreads) // 2]
        median_light = light_spreads[len(light_spreads) // 2]
        self.assertGreater(
            median_dark,
            5.0 * max(median_light, 1e-6),
            "the fully dark end must swing far wider than the white end",
        )

    def test_amplitude_is_capped_by_the_configured_percentage(self):
        rows = self._rows()
        widest = max(max(point[1] for point in row) - min(point[1] for point in row) for row in rows)
        self.assertLessEqual(
            widest,
            self.SPACING + 1e-6,
            "50% of a 4 mm row spacing is a 2 mm crest, so a row spans at most one spacing",
        )
        tight = self._rows(amplitude_pct=10.0)
        tight_widest = max(
            max(point[1] for point in row) - min(point[1] for point in row) for row in tight
        )
        self.assertLess(tight_widest, widest)

    def test_rows_are_adjacent_at_the_configured_spacing(self):
        rows = self._rows(lambda _x, _y: 1.0)
        # The mid-range of a sine row is its baseline; the mean drifts once the
        # phase is accumulated unevenly, and the sample grid never lands exactly
        # on the crest.
        centers = sorted(
            (max(point[1] for point in row) + min(point[1] for point in row)) / 2.0
            for row in rows
        )
        gaps = [b - a for a, b in zip(centers, centers[1:])]
        for gap in gaps:
            self.assertAlmostEqual(gap, self.SPACING, delta=0.05)

    def test_connected_rows_form_one_continuous_stroke(self):
        strokes = converter.sine_gradient_region_contours(
            self.BOUNDS, lambda _x, _y: 1.0, self.SPACING, 0.0, connect_rows=True
        )
        self.assertEqual(len(strokes), 1, "a solid region is one pen-down serpentine")
        stroke = strokes[0]
        longest = max(
            converter.distance(a, b) for a, b in zip(stroke, stroke[1:])
        )
        self.assertLessEqual(
            longest,
            2.0 * self.SPACING + 1e-6,
            "the turnaround between two antiphase rows is at most two spacings",
        )
        unjoined = converter.sine_gradient_region_contours(
            self.BOUNDS, lambda _x, _y: 1.0, self.SPACING, 0.0, connect_rows=False
        )
        self.assertGreater(len(unjoined), 1)
        self.assertEqual(sum(len(row) for row in unjoined), len(stroke))

    def test_white_paper_gets_no_ink(self):
        rows = self._rows(lambda x, _y: 1.0 if x <= 60.0 else 0.0)
        points = [point for row in rows for point in row]
        self.assertTrue(points)
        self.assertLessEqual(
            max(point[0] for point in points),
            60.0 + 1e-6,
            "the wave must stop where the rendered tone stops",
        )

    def test_a_blank_band_breaks_the_serpentine_instead_of_crossing_it(self):
        def with_hole(_x, y):
            return 0.0 if 18.0 <= y <= 22.0 else 1.0

        strokes = converter.sine_gradient_region_contours(
            self.BOUNDS, with_hole, self.SPACING, 0.0, connect_rows=True
        )
        self.assertGreater(len(strokes), 1, "a blank band forces a pen lift")
        for stroke in strokes:
            rows = [point[1] for point in stroke]
            self.assertTrue(
                max(rows) < 22.0 or min(rows) > 18.0,
                "no stroke may cross the blank band",
            )

    def test_vector_fill_uses_the_shape_tone_as_amplitude(self):
        square = [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0), (0.0, 40.0)]
        contours = converter.fill_pattern_contours(
            square, 4.0, 0.0, 1, 90.0, 1.0, "sine_gradient"
        )
        self.assertTrue(contours, "the shape source must still draw something")
        points = [point for contour in contours for point in contour]
        self.assertLess(
            len(contours),
            40,
            "rows must arrive as chained sine curves, not one contour per "
            "clipped segment",
        )
        self.assertGreater(max(len(contour) for contour in contours), 20)
        self.assertGreaterEqual(min(point[0] for point in points), -1e-6)
        self.assertLessEqual(max(point[0] for point in points), 40.0 + 1e-6)
        self.assertGreaterEqual(min(point[1] for point in points), -1e-6)
        self.assertLessEqual(max(point[1] for point in points), 40.0 + 1e-6)
        # The vector path reads the element's own darkness, so a black shape
        # gets the full 50% crest (2 mm on a 4 mm row) exactly as a fully dark
        # area does under the image-tone source.
        middle = [point for point in points if 10.0 <= point[0] <= 30.0]
        deviation = max(abs(point[1] - round(point[1] / 4.0) * 4.0) for point in middle)
        self.assertAlmostEqual(deviation, 2.0, places=3)

    def test_vector_fill_amplitude_follows_the_shape_tone(self):
        square = [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0), (0.0, 40.0)]

        def crest(darkness, **kwargs):
            contours = converter.fill_pattern_contours(
                square, 4.0, 0.0, 1, 90.0, darkness, "sine_gradient", **kwargs
            )
            points = [point for contour in contours for point in contour]
            return max(abs(point[1] - round(point[1] / 4.0) * 4.0) for point in points)

        self.assertAlmostEqual(crest(1.0), 2.0, places=3)
        self.assertAlmostEqual(crest(0.5), 1.0, places=3)
        self.assertAlmostEqual(crest(0.25), 0.5, places=3)
        self.assertAlmostEqual(
            crest(1.0, gradient_amplitude_pct=25.0),
            1.0,
            places=3,
            msg="the sidebar's amplitude percentage must reach the shapes path too",
        )

    def test_vector_fill_tone_is_amplitude_not_density(self):
        """A grey shape gets shorter waves, not closer rows.

        `waves` encodes tone as density, so with four shade levels and 50% grey
        its rows close up to about 2.8 mm. The sine gradient must keep the
        requested 4 mm pitch and vary only the crest: otherwise the tone is
        counted twice and a pale shape turns into a dense mesh.
        """
        square = [(0.0, 0.0), (40.0, 0.0), (40.0, 40.0), (0.0, 40.0)]
        contours = converter.fill_pattern_contours(
            square, 4.0, 0.0, 4, 45.0, 0.5, "sine_gradient"
        )
        rows = sorted(
            (max(point[1] for point in contour) + min(point[1] for point in contour)) / 2.0
            for contour in contours
        )
        pitches = [b - a for a, b in zip(rows, rows[1:]) if 2.0 < b - a < 6.0]
        self.assertTrue(pitches)
        pitch = sorted(pitches)[len(pitches) // 2]
        self.assertAlmostEqual(pitch, 4.0, delta=0.05)

        dense = converter.fill_pattern_contours(
            square, 4.0, 0.0, 4, 45.0, 0.5, "waves"
        )
        dense_rows = sorted(
            (max(point[1] for point in contour) + min(point[1] for point in contour)) / 2.0
            for contour in dense
        )
        dense_pitches = [
            b - a for a, b in zip(dense_rows, dense_rows[1:]) if 1.0 < b - a < 6.0
        ]
        self.assertTrue(dense_pitches)
        saturated = sorted(dense_pitches)[len(dense_pitches) // 2]
        self.assertLess(
            saturated,
            3.5,
            "the comparison pattern does encode tone as density",
        )

    def test_density_follows_tone_into_the_wiggle_rate(self):
        """SquiggleDraw accumulates phase from brightness; so does this.

        At density 0 the wave keeps one wavelength across the row, so the two
        halves of a step-tone row carry the same number of crests. At density
        200 the fully dark half wiggles about three times as fast as the 20%
        grey half, which is what makes dark areas read as dense squiggles
        instead of just taller ones.
        """
        width = 60.0
        step = (0.0, 0.0, width, 20.0)

        def darkness(x, _y):
            return 1.0 if x > width * 0.5 else 0.2

        def crests(contour, x_lo, x_hi):
            ys = [
                point[1]
                for point in contour
                if x_lo <= point[0] <= x_hi
            ]
            return sum(
                1
                for index in range(1, len(ys) - 1)
                if ys[index] > ys[index - 1] and ys[index] >= ys[index + 1]
            )

        def ratio(density_pct):
            rows = converter.sine_gradient_region_contours(
                step,
                darkness,
                4.0,
                0.0,
                density_pct=density_pct,
                connect_rows=False,
            )
            row = max(rows, key=len)
            grey = crests(row, 2.0, width * 0.5 - 2.0)
            dark = crests(row, width * 0.5 + 2.0, width - 2.0)
            return dark / max(grey, 1)

        flat = ratio(0.0)
        squiggly = ratio(200.0)
        self.assertLess(abs(flat - 1.0), 0.25, "density 0 keeps one wavelength")
        self.assertGreater(
            squiggly,
            1.7,
            "density 200 must make the dark half wiggle visibly faster",
        )
        self.assertGreater(squiggly, flat)


if __name__ == "__main__":
    unittest.main()
