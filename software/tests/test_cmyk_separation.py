"""CMYK separation, process-ink prediction, and image metadata."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


class SeparationTests(unittest.TestCase):
    def test_white_needs_no_ink(self):
        import numpy as np

        tones = converter.rgb_to_cmyk_tone(np.ones((2, 2, 3), dtype="float32"))
        for channel in converter.CHANNELS:
            self.assertLess(float(tones[channel].max()), 1e-6)

    def test_black_moves_into_k_with_gcr(self):
        import numpy as np

        tones = converter.rgb_to_cmyk_tone(
            np.zeros((1, 1, 3), dtype="float32"), weights=(1, 1, 1, 1)
        )
        self.assertAlmostEqual(float(tones["k"][0, 0]), 1.0, places=5)
        for channel in ("c", "m", "y"):
            self.assertAlmostEqual(float(tones[channel][0, 0]), 0.0, places=5)

    def test_pure_cyan_stays_in_c(self):
        import numpy as np

        pixel = np.array([[[0.0, 1.0, 1.0]]], dtype="float32")
        tones = converter.rgb_to_cmyk_tone(pixel)
        self.assertAlmostEqual(float(tones["c"][0, 0]), 1.0, places=5)
        self.assertAlmostEqual(float(tones["k"][0, 0]), 0.0, places=5)

    def test_tombow_process_preview_colours_are_explicit(self):
        self.assertEqual(
            converter.CHANNEL_COLORS,
            {
                "c": "#00aeef",
                "m": "#ec008c",
                "y": "#ffff00",
                "k": "#231f20",
            },
        )
        self.assertEqual(converter.CHANNEL_COLORS, converter.TOMBOW_PROCESS_COLORS)

    def test_gcr_zero_keeps_the_gray_in_cmy(self):
        import numpy as np

        gray = np.full((1, 1, 3), 0.5, dtype="float32")
        tones = converter.rgb_to_cmyk_tone(
            gray,
            gcr=0.0,
            weights=(1, 1, 1, 1),
            color_match=False,
        )
        self.assertAlmostEqual(float(tones["k"][0, 0]), 0.0, places=5)
        for channel in ("c", "m", "y"):
            self.assertAlmostEqual(float(tones[channel][0, 0]), 0.5, places=5)

    def test_weights_and_gamma_shape_the_ink(self):
        import numpy as np

        gray = np.full((1, 1, 3), 0.5, dtype="float32")
        tones = converter.rgb_to_cmyk_tone(
            gray,
            gcr=0.0,
            weights=(0.0, 1.0, 1.0, 1.0),
            gamma=2.0,
            color_match=False,
        )
        self.assertAlmostEqual(float(tones["c"][0, 0]), 0.0, places=6)
        self.assertAlmostEqual(float(tones["m"][0, 0]), 0.25, places=5)

    def test_process_ink_model_matches_gray_and_skin_tones(self):
        import numpy as np

        target = np.array(
            [[[0.50, 0.50, 0.50], [0.75, 0.20, 0.18]]],
            dtype="float32",
        )
        plain = converter.rgb_to_cmyk_tone(
            target,
            gcr=0.8,
            weights=(1, 1, 1, 1),
            color_match=False,
        )
        matched = converter.rgb_to_cmyk_tone(
            target,
            gcr=0.8,
            weights=(1, 1, 1, 1),
        )
        plain_error = np.linalg.norm(
            converter.predict_cmyk_rgb(
                {channel: plain[channel][0, 0] for channel in converter.CHANNELS}
            )
            - target[0, 0],
            axis=-1,
        )
        matched_error = np.linalg.norm(
            converter.predict_cmyk_rgb(
                {
                    channel: matched[channel][0, 0]
                    for channel in converter.CHANNELS
                }
            )
            - target[0, 0],
            axis=-1,
        )
        self.assertTrue(np.all(matched_error < plain_error))
        self.assertTrue(np.all(matched_error < 0.005))

    def test_measured_ink_colors_drive_the_process_prediction(self):
        import numpy as np

        tones = {
            channel: np.zeros((1, 1), dtype="float32")
            for channel in converter.CHANNELS
        }
        tones["c"][0, 0] = 1.0
        measured = {"c": (0.2, 0.9, 0.7)}
        predicted = converter.predict_cmyk_rgb(
            {channel: tones[channel][0, 0] for channel in converter.CHANNELS},
            ink_colors=measured,
        )
        np.testing.assert_allclose(predicted, [0.2, 0.9, 0.7], atol=1e-7)

    def test_embedded_icc_profile_is_converted_to_srgb(self):
        from PIL import Image

        with tempfile.TemporaryDirectory(prefix="cmyk-icc-") as folder:
            path = Path(folder) / "tagged.png"
            Image.new("RGB", (8, 8), (180, 70, 30)).save(
                path,
                icc_profile=b"test profile",
            )
            converted = Image.new("RGB", (8, 8), (90, 40, 20))
            with mock.patch(
                "PIL.ImageCms.ImageCmsProfile",
                return_value=object(),
            ) as profile, mock.patch(
                "PIL.ImageCms.createProfile",
                return_value=object(),
            ) as target, mock.patch(
                "PIL.ImageCms.profileToProfile",
                return_value=converted,
            ) as transform:
                tones, _geometry = converter.prepare_image_tones(
                    path,
                    60.0,
                    60.0,
                    margin_mm=4.0,
                    resolution_px=32,
                )

        profile.assert_called_once()
        target.assert_called_once_with("sRGB")
        transform.assert_called_once()
        self.assertEqual(tones["k"].shape, (8, 8))

    def test_exif_orientation_is_applied_before_layout(self):
        from PIL import Image

        with tempfile.TemporaryDirectory(prefix="cmyk-exif-") as folder:
            path = Path(folder) / "rotated.jpg"
            image = Image.new("RGB", (8, 4), "white")
            exif = Image.Exif()
            exif[274] = 6
            image.save(path, exif=exif)
            _tones, geometry = converter.prepare_image_tones(
                path,
                100.0,
                100.0,
                margin_mm=6.0,
                resolution_px=100,
            )

        self.assertLess(geometry["width_mm"], geometry["height_mm"])
        self.assertAlmostEqual(
            geometry["width_mm"] / geometry["height_mm"],
            0.5,
            places=5,
        )

    def test_transparent_pixels_become_paper_not_black_ink(self):
        from PIL import Image

        with tempfile.TemporaryDirectory(prefix="cmyk-alpha-") as folder:
            path = Path(folder) / "cutout.png"
            Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(path)
            tones, _geometry = converter.prepare_image_tones(
                path,
                60.0,
                60.0,
                margin_mm=4.0,
                resolution_px=32,
                auto_levels=False,
                brightness=100.0,
                color_match=False,
            )

        for channel in converter.CHANNELS:
            self.assertLess(float(tones[channel].max()), 1e-6)


if __name__ == "__main__":
    unittest.main()
