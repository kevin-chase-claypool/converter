"""General CMYK screen styles and mark placement."""

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


class CmykScreenStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np

        cls.np = np

    def geometry(self, width=100.0, height=100.0):
        return {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": width,
            "height_mm": height,
            "pixels_w": 32,
            "pixels_h": 32,
        }

    def test_mark_cap_grows_the_pitch(self):
        dark = self.np.full((32, 32), 0.9, dtype="float32")
        marks = converter.screen_channel(
            dark, self.geometry(), spacing_mm=1.0, max_marks=300
        )
        self.assertLessEqual(len(marks), 360)
        self.assertGreater(len(marks), 100)

    def test_stipple_style_drops_marks_on_paper(self):
        half = self.np.full((32, 32), 0.5, dtype="float32")
        stipple = converter.screen_channel(
            half, self.geometry(), style="stipple", spacing_mm=5.0, seed=3
        )
        blank = converter.screen_channel(
            self.np.zeros((32, 32), dtype="float32"),
            self.geometry(),
            style="stipple",
            spacing_mm=5.0,
            seed=3,
        )
        self.assertEqual(blank, [])
        self.assertGreater(len(stipple), 20)

    def test_line_screen_breaks_in_white(self):
        dark = self.np.full((32, 32), 0.7, dtype="float32")
        lines = converter.screen_channel(
            dark, self.geometry(), style="lines", spacing_mm=4.0
        )
        self.assertGreater(len(lines), 5)
        self.assertTrue(all(len(line) > 2 for line in lines))
        self.assertEqual(
            converter.screen_channel(
                self.np.zeros((32, 32), dtype="float32"),
                self.geometry(),
                style="lines",
                spacing_mm=4.0,
            ),
            [],
        )

    def test_rectilinear_joins_rows_and_breaks_over_blank(self):
        dark = self.np.full((32, 32), 0.8, dtype="float32")
        lines = converter.screen_channel(
            dark, self.geometry(), style="lines", spacing_mm=4.0
        )
        joined = converter.screen_channel(
            dark, self.geometry(), style="rectilinear", spacing_mm=4.0
        )
        self.assertEqual(len(joined), 1)
        self.assertGreater(len(joined[0]), len(lines[0]))
        self.assertLess(len(joined), len(lines))
        band = self.np.full((32, 32), 0.8, dtype="float32")
        band[12:20, :] = 0.0
        split = converter.screen_channel(
            band, self.geometry(), style="rectilinear", spacing_mm=4.0
        )
        self.assertGreaterEqual(len(split), 2)

    def test_continuous_screen_joins_nearest_adjacent_row_runs(self):
        tone = self.np.zeros((32, 32), dtype="float32")
        for y in range(32):
            if y % 2:
                tone[y, 20:] = 1.0
            else:
                tone[y, :12] = 1.0

        rectilinear = converter.screen_channel(
            tone,
            self.geometry(),
            style="rectilinear",
            spacing_mm=4.0,
        )
        continuous = converter.screen_channel(
            tone,
            self.geometry(),
            style="continuous",
            spacing_mm=4.0,
        )

        self.assertGreater(len(rectilinear), 20)
        self.assertEqual(len(continuous), 1)
        self.assertGreater(len(continuous[0]), 500)

    def test_rectilinear_chains_photo_like_tone(self):
        yy, xx = self.np.mgrid[0:64, 0:64]
        tone = (
            0.15
            + 0.6
            * (self.np.sin(xx / 7.0) * self.np.cos(yy / 9.0) * 0.5 + 0.5)
        ).astype("float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": 64,
            "pixels_h": 64,
        }
        lines = converter.screen_channel(
            tone, geometry, style="lines", spacing_mm=2.0
        )
        chains = converter.screen_channel(
            tone, geometry, style="rectilinear", spacing_mm=2.0
        )
        self.assertLess(len(chains), len(lines) * 0.5)
        self.assertGreater(
            max(len(chain) for chain in chains),
            max(len(line) for line in lines) * 5,
        )

    def test_rectilinear_stretches_light_tone_spacing(self):
        light = self.np.full((32, 32), 0.2, dtype="float32")
        lines = converter.screen_channel(
            light, self.geometry(), style="lines", spacing_mm=4.0
        )
        rect = converter.screen_channel(
            light, self.geometry(), style="rectilinear", spacing_mm=4.0
        )
        # The rectilinear screen opens the pitch much further in light tones
        # (6x vs 2x), so a 20% field keeps open paper instead of hatching it.
        self.assertLess(len(rect), len(lines) * 0.7)

    def test_rectilinear_eases_the_row_pitch_across_a_tone_edge(self):
        from converter_core import cmyk as cmyk_module

        # Paper above 60 mm, a 0.35 tone below it. The first inked row used to
        # drop the pitch in one step, which reads as banding where the subject
        # meets the background.
        def darkness(_x, y):
            return 0.0 if y < 60.0 else 0.35

        runs = cmyk_module._line_runs(
            darkness,
            (0.0, 0.0, 120.0, 120.0),
            0.0,
            1.0,
            cmyk_module.INK_FLOOR,
            adaptive=True,
            connect=True,
            light_stretch=6.0,
        )
        rows = sorted({round(point[1], 3) for run in runs for point in run})
        gaps = [
            second - first
            for first, second in zip(rows, rows[1:])
            if second - first > 0.01
        ]
        jumps = [
            max(first, second) / max(min(first, second), 1e-6)
            for first, second in zip(gaps, gaps[1:])
        ]
        self.assertGreaterEqual(len(gaps), 5)
        self.assertLess(max(jumps), 1.25)

    def test_crosshatch_levels_and_overdraw(self):
        dark = self.np.full((32, 32), 0.8, dtype="float32")
        two = converter.screen_channel(
            dark, self.geometry(), style="crosshatch", spacing_mm=4.0, levels=2
        )
        four = converter.screen_channel(
            dark, self.geometry(), style="crosshatch", spacing_mm=4.0, levels=4
        )
        self.assertGreater(len(four), len(two))
        doubled = converter.screen_channel(
            dark,
            self.geometry(),
            style="crosshatch",
            spacing_mm=4.0,
            levels=4,
            overdraw=2,
        )
        self.assertEqual(len(doubled), 2 * len(four))

    def test_crosshatch_supports_more_than_four_families(self):
        dark = self.np.full((32, 32), 0.9, dtype="float32")
        six = converter.screen_channel(
            dark, self.geometry(), style="crosshatch", spacing_mm=4.0, levels=6
        )
        nine = converter.screen_channel(
            dark, self.geometry(), style="crosshatch", spacing_mm=4.0, levels=9
        )
        self.assertGreater(len(nine), len(six))

    def test_wave_gyroid_and_tsp_styles(self):
        dark = self.np.full((32, 32), 0.6, dtype="float32")
        waves = converter.screen_channel(
            dark,
            self.geometry(),
            style="waves",
            spacing_mm=4.0,
            allow_variable_wave_spacing=True,
        )
        self.assertGreater(len(waves), 3)
        gyroid = converter.screen_channel(
            dark, self.geometry(), style="gyroid", spacing_mm=4.0
        )
        self.assertGreater(len(gyroid), 3)
        tsp = converter.screen_channel(
            dark, self.geometry(), style="tsp", spacing_mm=4.0, seed=1
        )
        self.assertEqual(len(tsp), 1)
        self.assertGreater(len(tsp[0]), 10)


if __name__ == "__main__":
    unittest.main()
