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
        self.assertEqual(
            converter.PATTERN_SIZE_FIELDS["sine_gradient"],
            "wave_size_mm",
            "the sine gradient reuses the wave size field for its row spacing",
        )
        defaults = converter.Settings()
        self.assertEqual(defaults.gradient_wave_amplitude_pct, 50.0)
        self.assertTrue(defaults.sine_rows_connected)

    def test_amplitude_cannot_exceed_one_row_spacing(self):
        converter.validate_settings(converter.Settings(gradient_wave_amplitude_pct=100.0))
        with self.assertRaises(ValueError):
            converter.validate_settings(converter.Settings(gradient_wave_amplitude_pct=100.1))
        with self.assertRaises(ValueError):
            converter.validate_settings(converter.Settings(gradient_wave_amplitude_pct=-1.0))


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
        centers = sorted(sum(point[1] for point in row) / len(row) for row in rows)
        gaps = [b - a for a, b in zip(centers, centers[1:])]
        for gap in gaps:
            self.assertAlmostEqual(gap, self.SPACING, places=6)

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

    def test_vector_fill_degrades_to_a_uniform_sine_hatch(self):
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
        # Without rendered tone the fallback is the uniform wave family, whose
        # rows sit on the 4 mm lattice and swing by 42% of the spacing.
        middle = [point for point in points if 10.0 <= point[0] <= 30.0]
        deviation = max(abs(point[1] - round(point[1] / 4.0) * 4.0) for point in middle)
        self.assertAlmostEqual(deviation, 4.0 * 0.42, places=6)


if __name__ == "__main__":
    unittest.main()
