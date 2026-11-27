"""Composite-aware CMYK separation regression tests.

The CMYK photo path now inverts the multiply ink model instead of using naive
``C = 1 - R`` complements, so the four overlaid plates reproduce the source
colour instead of coming out washed, gray, and short on black.
"""

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core.cmyk as cmyk


def _patch(rgb):
    return np.asarray(rgb, dtype=np.float32)[None, None, :]


def _composite_mae(tones, rgb):
    return float(
        np.abs(cmyk.multiply_composite_rgb(tones) - rgb).mean()
    )


class CompositeAwareSeparationTests(unittest.TestCase):
    def test_nominal_transmittances_match_the_preview_colours(self):
        matrix = cmyk.ink_transmittance_matrix()
        for index, channel in enumerate(cmyk.CHANNELS):
            colour = cmyk.CHANNEL_COLORS[channel].lstrip("#")
            expected = [
                int(colour[offset : offset + 2], 16) / 255.0
                for offset in (0, 2, 4)
            ]
            self.assertTrue(
                np.allclose(matrix[index], expected, atol=1e-3),
                channel,
            )

    def test_transparent_pixels_composite_over_paper_white(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "alpha.png"
            image = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
            image.putpixel((4, 4), (210, 120, 90, 255))
            image.save(path)

            loaded = cmyk._load_color_managed_image(path)
            pixels = np.asarray(loaded, dtype=np.float32) / 255.0

        self.assertTrue(np.allclose(pixels[0, 0], 1.0))
        self.assertTrue(
            np.allclose(pixels[4, 4], np.array([210, 120, 90]) / 255.0)
        )

    def test_transparent_source_creates_no_ink_outside_the_subject(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "alpha.png"
            image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
            image.paste((220, 130, 100, 255), (4, 4, 12, 12))
            image.save(path)

            tones, _geometry = cmyk.prepare_image_tones(
                path,
                40.0,
                40.0,
                margin_mm=0.0,
                resolution_px=16,
                auto_levels=False,
                gcr=0.6,
                weights=(1, 1, 1, 1),
            )

        self.assertLess(float(tones["k"][0, 0]), 1e-6)
        self.assertLess(float(tones["c"][-1, -1]), 1e-6)

    def test_in_gamut_colours_reproduce_within_three_percent(self):
        matrix = cmyk.ink_transmittance_matrix()
        patches = {
            "white": (1.0, 1.0, 1.0),
            "gray_25": (0.25, 0.25, 0.25),
            "gray_50": (0.5, 0.5, 0.5),
            "gray_75": (0.75, 0.75, 0.75),
            "cyan_ink": tuple(matrix[0]),
            "magenta_ink": tuple(matrix[1]),
            "yellow_ink": tuple(matrix[2]),
            "skin": (0.85, 0.65, 0.55),
            "shadow": (0.15, 0.12, 0.10),
        }
        for name, colour in patches.items():
            source = _patch(colour)
            tones = cmyk.separate_cmyk_composite(
                source,
                gcr=0.6,
                weights=(1, 1, 1, 1),
                gamma=1.0,
            )
            rendered = cmyk.multiply_composite_rgb(
                {channel: tones[channel] for channel in cmyk.CHANNELS}
            )
            self.assertLess(
                float(np.abs(rendered[0, 0] - source).mean()),
                0.03,
                name,
            )

    def test_natural_and_saturated_colours_stay_inside_gamut_tolerance(self):
        patches = {
            "black": (0.0, 0.0, 0.0),
            "red": (0.8, 0.1, 0.1),
            "green": (0.1, 0.7, 0.2),
            "blue": (0.1, 0.2, 0.8),
            "sky": (0.55, 0.75, 0.95),
        }
        for name, colour in patches.items():
            source = _patch(colour)
            tones = cmyk.separate_cmyk_composite(
                source,
                gcr=0.6,
                weights=(1, 1, 1, 1),
                gamma=1.0,
            )
            rendered = cmyk.multiply_composite_rgb(
                {channel: tones[channel] for channel in cmyk.CHANNELS}
            )
            self.assertLess(
                float(np.abs(rendered[0, 0] - source).mean()),
                0.11,
                name,
            )

    def test_gamma_above_one_darkens_and_below_one_lightens(self):
        gray = _patch((0.5, 0.5, 0.5))
        neutral = cmyk.separate_cmyk_composite(gray, gamma=1.0)
        dark = cmyk.separate_cmyk_composite(gray, gamma=1.8)
        light = cmyk.separate_cmyk_composite(gray, gamma=0.6)

        def luminance(tones):
            return float(
                cmyk.multiply_composite_rgb(tones)[0, 0]
                @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
            )

        self.assertLess(luminance(dark), luminance(neutral))
        self.assertGreater(luminance(light), luminance(neutral))

    def test_weights_scale_each_channel_coverage(self):
        gray = _patch((0.3, 0.3, 0.3))
        base = cmyk.separate_cmyk_composite(
            gray,
            gcr=0.0,
            weights=(1, 1, 1, 1),
            gamma=1.0,
        )
        weighted = cmyk.separate_cmyk_composite(
            gray,
            gcr=0.0,
            weights=(0.5, 1.0, 1.0, 1.0),
            gamma=1.0,
        )
        self.assertAlmostEqual(
            float(weighted["c"][0, 0]),
            0.5 * float(base["c"][0, 0]),
            places=5,
        )

    def test_total_ink_respects_the_area_coverage_limit(self):
        dark = _patch((0.05, 0.05, 0.05))
        tones = cmyk.separate_cmyk_composite(
            dark,
            gcr=1.0,
            weights=(1, 1, 1, 1),
            gamma=1.0,
            ink_limit=3.0,
        )
        total = float(sum(tones[channel][0, 0] for channel in cmyk.CHANNELS))
        self.assertLessEqual(total, 3.0 + 1e-5)

    def test_black_plate_is_no_longer_collapsed(self):
        # A mid-dark neutral should carry meaningful black coverage so the
        # Wave screen has black structure to draw (the old naive GCR chain
        # collapsed black to near zero).
        gray = _patch((0.3, 0.3, 0.3))
        tones = cmyk.separate_cmyk_composite(
            gray,
            gcr=0.6,
            weights=(1, 1, 1, 1),
            gamma=1.0,
        )
        self.assertGreater(float(tones["k"][0, 0]), 0.25)


SOURCE_IMAGE = Path(
    r"C:\Users\jacks\Downloads\Golden Sunset Winter Family Selfie.png"
)


@unittest.skipUnless(SOURCE_IMAGE.is_file(), "owner source image not present")
class SourceImageFidelityTests(unittest.TestCase):
    def test_ideal_composite_approximates_the_source(self):
        image = cmyk._load_color_managed_image(SOURCE_IMAGE)
        longest = max(image.size)
        factor = 384.0 / float(longest)
        image = image.resize(
            (
                max(8, int(round(image.width * factor))),
                max(8, int(round(image.height * factor))),
            ),
            Image.LANCZOS,
        )
        rgb = np.asarray(image, dtype=np.float32) / 255.0
        tones = cmyk.separate_cmyk_composite(
            rgb,
            gcr=0.6,
            weights=(1, 1, 1, 1),
            gamma=1.0,
        )
        rendered = cmyk.multiply_composite_rgb(tones)
        luminance = np.array([0.299, 0.587, 0.114], dtype=np.float32)
        source_lum = float((rgb @ luminance).mean())
        rendered_lum = float((rendered @ luminance).mean())
        self.assertLess(float(np.abs(rendered - rgb).mean()), 0.15)
        self.assertLess(abs(rendered_lum - source_lum), 0.06)
        self.assertGreater(float(np.percentile(tones["k"], 95.0)), 0.25)


if __name__ == "__main__":
    unittest.main()
