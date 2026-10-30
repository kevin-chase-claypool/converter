"""CMYK separation, screening, layer SVGs, and per-ink cost analysis."""

import hashlib
import json
import math
import os
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover - the core tests do not need Qt
    HAVE_QT = False


def svg_groups(root):
    """Return the data-ink groups (the SVG root also ends in 'g')."""
    return [
        element.get("data-ink")
        for element in root.iter()
        if element.tag.split("}")[-1] == "g"
    ]


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

    def test_gcr_zero_keeps_the_gray_in_cmy(self):
        import numpy as np

        gray = np.full((1, 1, 3), 0.5, dtype="float32")
        tones = converter.rgb_to_cmyk_tone(gray, gcr=0.0, weights=(1, 1, 1, 1))
        self.assertAlmostEqual(float(tones["k"][0, 0]), 0.0, places=5)
        for channel in ("c", "m", "y"):
            self.assertAlmostEqual(float(tones[channel][0, 0]), 0.5, places=5)

    def test_weights_and_gamma_shape_the_ink(self):
        import numpy as np

        gray = np.full((1, 1, 3), 0.5, dtype="float32")
        tones = converter.rgb_to_cmyk_tone(
            gray, gcr=0.0, weights=(0.0, 1.0, 1.0, 1.0), gamma=2.0
        )
        self.assertAlmostEqual(float(tones["c"][0, 0]), 0.0, places=6)
        self.assertAlmostEqual(float(tones["m"][0, 0]), 0.25, places=5)


class ScreeningTests(unittest.TestCase):
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

    def test_halftone_marks_follow_tone(self):
        white = self.np.zeros((32, 32), dtype="float32")
        self.assertEqual(
            converter.screen_channel(white, self.geometry(), spacing_mm=4.0), []
        )
        gray = self.np.full((32, 32), 0.6, dtype="float32")
        marks = converter.screen_channel(
            gray, self.geometry(), spacing_mm=4.0, solid=False
        )
        self.assertGreater(len(marks), 100)
        self.assertEqual(len(marks[0]), 9)  # closed 8-step circle
        solid = converter.screen_channel(gray, self.geometry(), spacing_mm=4.0)
        self.assertEqual(len(solid), len(marks))
        self.assertEqual(len(solid[0]), 15)  # 14-step spiral reads as a dot

    def test_auto_levels_stretch_a_low_key_image(self):
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-levels-")
        self.addCleanup(lambda: __import__("shutil").rmtree(folder, ignore_errors=True))
        path = str(Path(folder) / "lowkey.png")
        image = Image.new("L", (32, 32))
        for x in range(32):
            for y in range(32):
                image.putpixel((x, y), 90 + (x * 40) // 31)
        image.save(path)
        plain, _ = converter.prepare_image_tones(
            path, 80, 80, margin_mm=4, resolution_px=64, auto_levels=False
        )
        stretched, _ = converter.prepare_image_tones(
            path, 80, 80, margin_mm=4, resolution_px=64, auto_levels=True
        )
        plain_range = float(plain["k"].max() - plain["k"].min())
        stretched_range = float(stretched["k"].max() - stretched["k"].min())
        self.assertGreater(stretched_range, plain_range + 0.3)

    def test_depth_field_uses_scene_luminance_not_ink_coverage(self):
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-depth-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = str(Path(folder) / "colour.png")
        image = Image.new("RGB", (16, 16))
        for x in range(16):
            red = round(255 * x / 15)
            for y in range(16):
                image.putpixel((x, y), (red, 128, 0))
        image.save(path)
        tones, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=32,
            auto_levels=False,
            gcr=0.0,
            weights=(1, 1, 1, 1),
        )
        self.assertAlmostEqual(
            float(tones["m"].max() - tones["m"].min()), 0.0, places=5
        )
        self.assertGreater(
            float(tones["depth"].max() - tones["depth"].min()),
            0.25,
        )

    def test_contrast_200_does_not_clip_tone_endpoints(self):
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-contrast-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = str(Path(folder) / "ramp.png")
        image = Image.new("L", (16, 16))
        for x in range(16):
            value = int(64 + x * 127 / 15)
            for y in range(16):
                image.putpixel((x, y), value)
        image.save(path)
        tones, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=64,
            auto_levels=False,
            contrast=2.0,
            gcr=1.0,
            weights=(1, 1, 1, 1),
        )
        k = tones["k"]
        # The old hard-clip contrast mapped 0.25/0.75 to pure white/black.
        self.assertGreater(float(k.min()), 0.05)
        self.assertLess(float(k.max()), 0.95)

    def test_brightness_lifts_mid_tone_ink(self):
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-brightness-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = str(Path(folder) / "gray.png")
        image = Image.new("RGB", (16, 16), (77, 77, 77))
        image.save(path)
        base, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=32,
            auto_levels=False,
            gcr=1.0,
            weights=(1, 1, 1, 1),
        )
        lifted, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=32,
            auto_levels=False,
            gcr=1.0,
            weights=(1, 1, 1, 1),
            brightness=130.0,
        )
        # 130 % brightness keeps the black point but lays less ink.
        self.assertLess(float(lifted["k"].mean()), float(base["k"].mean()) - 0.05)

    def test_sharpening_restores_a_soft_edge_without_shifting_the_mean(self):
        import numpy as np
        from PIL import Image, ImageFilter

        folder = tempfile.mkdtemp(prefix="cmyk-sharpen-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = str(Path(folder) / "soft-edge.png")
        values = np.zeros((64, 64), dtype=np.uint8)
        values[:, 32:] = 180
        soft = np.asarray(
            Image.fromarray(values).filter(ImageFilter.GaussianBlur(2.0))
        )
        Image.fromarray(np.stack([soft] * 3, axis=2)).save(path)
        plain, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=64,
            auto_levels=False,
            gcr=0.0,
            weights=(1, 1, 1, 1),
        )
        sharpened, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=64,
            auto_levels=False,
            gcr=0.0,
            weights=(1, 1, 1, 1),
            sharpen_pct=100.0,
            sharpen_radius_mm=2.0,
        )
        plain_gradient = float(np.abs(np.diff(plain["c"], axis=1)).max())
        sharp_gradient = float(np.abs(np.diff(sharpened["c"], axis=1)).max())
        self.assertGreater(sharp_gradient, plain_gradient * 1.2)
        self.assertLess(
            abs(float(sharpened["c"].mean()) - float(plain["c"].mean())),
            0.01,
        )

    def test_ink_processing_does_not_flatten_wave_depth(self):
        import numpy as np
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-depth-processing-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = str(Path(folder) / "gradient.png")
        ramp = np.tile(np.linspace(20, 235, 64, dtype="uint8"), (64, 1))
        Image.fromarray(np.stack([ramp] * 3, axis=2)).save(path)
        neutral, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=64,
            auto_levels=False,
            gcr=1.0,
            weights=(1, 1, 1, 1),
        )
        processed, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=64,
            auto_levels=False,
            saturation=1.25,
            contrast=2.5,
            brightness=40.0,
            gcr=0.99,
            weights=(1, 1, 1, 1),
            gamma=3.0,
        )
        np.testing.assert_allclose(
            processed["depth"],
            neutral["depth"],
            atol=1e-6,
            err_msg="ink density controls must not saturate scene depth",
        )

    def test_auto_photo_settings_fit_dark_and_bright_images(self):
        import numpy as np
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-auto-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        rng = np.random.default_rng(7)

        def save(name, values):
            path = str(Path(folder) / name)
            Image.fromarray(np.stack([values] * 3, axis=2)).save(path)
            return path

        dark_values = (12 + rng.random((64, 64)) * 22).astype("uint8")
        dark_values[10:22, 10:22] = 190
        dark_values[40:55, 35:50] = 150
        bright_values = (150 + rng.random((64, 64)) * 70).astype("uint8")
        dark = converter.auto_photo_settings(save("dark.png", dark_values))
        bright = converter.auto_photo_settings(
            save("bright.png", bright_values)
        )
        self.assertTrue(dark["auto_levels"])
        # A dark scene still needs the full lift so its structure sits in the
        # visible mid tones; the tone term trades a little gamma away to keep
        # the print's mean inside the printable window. A bright image needs
        # no lift and prints at its own tone.
        self.assertGreaterEqual(dark["brightness"], 160)
        self.assertGreaterEqual(dark["gamma"], 1.4)
        self.assertLessEqual(bright["brightness"], 140)
        self.assertLessEqual(bright["gamma"], 1.05)
        self.assertEqual(
            dark, converter.auto_photo_settings(save("dark2.png", dark_values))
        )

    def test_auto_photo_settings_match_the_printed_tone_to_the_photo(self):
        import numpy as np
        from PIL import Image
        from converter_core import cmyk as cmyk_module

        folder = tempfile.mkdtemp(prefix="cmyk-auto-tone-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        rng = np.random.default_rng(11)
        # A bright, low-contrast field with soft structure - a stand-in for a
        # portrait, where the detail-only search used to lift the print a stop
        # lighter than the photo and wash the skin out.
        values = (150 + rng.random((64, 64)) * 70).astype("uint8")
        path = str(Path(folder) / "portrait.png")
        Image.fromarray(np.stack([values] * 3, axis=2)).save(path)
        chosen = converter.auto_photo_settings(path)

        rgb = np.asarray(Image.open(path).convert("RGB"), dtype="float32") / 255.0
        luminance = rgb @ np.array([0.299, 0.587, 0.114], dtype="float32")
        low, high = np.percentile(luminance, [1.0, 99.0])
        stretched = np.clip(
            (luminance - low) / max(high - low, 1e-3), 0.0, 1.0
        )
        contrasted = cmyk_module._soft_contrast(
            stretched, chosen["contrast"] / 100.0
        )
        lifted = np.power(
            contrasted, 100.0 / max(1.0, chosen["brightness"])
        )
        printed = 1.0 - np.power(1.0 - lifted, chosen["gamma"])
        # The search now aims the print's mean tone at the photo's instead of
        # chasing detail energy wherever it leads.
        self.assertLess(
            abs(float(printed.mean()) - float(stretched.mean())), 0.03
        )

    def test_auto_photo_settings_compensate_a_sparse_screen(self):
        import numpy as np
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-auto-screen-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        rng = np.random.default_rng(11)
        values = (150 + rng.random((64, 64)) * 70).astype("uint8")
        path = str(Path(folder) / "portrait.png")
        Image.fromarray(np.stack([values] * 3, axis=2)).save(path)
        plain = converter.auto_photo_settings(path)
        sparse = converter.auto_photo_settings(
            path, pen_width_mm=0.30, effective_pitch_mm=0.31
        )
        fine = converter.auto_photo_settings(
            path, pen_width_mm=0.30, effective_pitch_mm=0.10
        )
        # Rows one pen width apart only ink about a fifth of a light tone, so
        # the search has to ask for a darker chain than the tone model alone.
        self.assertLess(sparse["gamma"], plain["gamma"])
        self.assertLessEqual(sparse["brightness"], plain["brightness"])
        # A screen finer than the pen over-inks the same tone and needs less.
        self.assertGreater(fine["gamma"], sparse["gamma"])
        self.assertGreaterEqual(fine["brightness"], sparse["brightness"])

    def test_auto_photo_settings_add_contrast_when_it_helps_detail(self):
        import numpy as np
        from PIL import Image, ImageFilter

        folder = tempfile.mkdtemp(prefix="cmyk-auto-mid-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        rng = np.random.default_rng(3)
        values = (96 + rng.random((64, 64)) * 64).astype("uint8")
        values = np.asarray(
            Image.fromarray(values).filter(ImageFilter.GaussianBlur(1.5))
        )
        path = str(Path(folder) / "mid.png")
        Image.fromarray(np.stack([values] * 3, axis=2)).save(path)
        mid = converter.auto_photo_settings(path)
        # A mid-key texture has its detail energy where the soft S-curve
        # steepens, so the search chooses real contrast there.
        self.assertGreaterEqual(mid["contrast"], 180)

    def test_wave_auto_preserves_a_normal_photo_exposure(self):
        import numpy as np
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-wave-auto-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        yy, xx = np.mgrid[0:96, 0:128]
        image = np.empty((96, 128, 3), dtype="float32")
        image[:55] = (0.62, 0.73, 0.82)
        image[:55, 55:100] = (0.92, 0.75, 0.52)
        image[55:] = (0.20, 0.28, 0.16)
        image[55:, 18:45] = (0.62, 0.18, 0.12)
        image[55:, 82:115] = (0.48, 0.12, 0.09)
        image += (xx[..., None] / 127.0 - 0.5) * 0.06
        image = np.clip(image * 255.0, 0.0, 255.0).astype("uint8")
        path = str(Path(folder) / "landscape.png")
        Image.fromarray(image).save(path)

        values = converter.auto_photo_settings(
            path,
            pen_width_mm=0.8,
            effective_pitch_mm=1.92,
            style="waves_even",
            dot_pitch_mm=0.8,
        )

        self.assertTrue(values["auto_levels"])
        self.assertGreaterEqual(values["brightness"], 100)
        self.assertLessEqual(values["brightness"], 160)
        self.assertGreaterEqual(values["contrast"], 100)
        self.assertLessEqual(values["contrast"], 160)
        self.assertGreaterEqual(values["saturation"], 90)
        self.assertLessEqual(values["saturation"], 110)
        self.assertGreaterEqual(values["gcr"], 0)
        self.assertLessEqual(values["gcr"], 70)
        self.assertGreaterEqual(values["gamma"], 0.85)
        self.assertLessEqual(values["gamma"], 1.40)
        self.assertEqual(values["sharpen_pct"], 100.0)
        self.assertEqual(values["sharpen_radius_mm"], 1.5)
        self.assertGreater(values["dot_pitch_mm"], 0.8)

    def test_auto_photo_settings_keep_colour_on_vivid_images(self):
        import numpy as np
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-auto-colour-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        # Vivid purple/green vertical stripes against a vivid background.
        vivid = np.zeros((64, 64, 3), dtype="uint8")
        vivid[:, :, :] = (130, 110, 200)
        vivid[:, ::8, :] = (60, 170, 70)
        vivid_path = str(Path(folder) / "vivid.png")
        Image.fromarray(vivid).save(vivid_path)
        gray_path = str(Path(folder) / "gray.png")
        Image.new("RGB", (64, 64), (128, 128, 128)).save(gray_path)
        vivid_values = converter.auto_photo_settings(vivid_path)
        gray_values = converter.auto_photo_settings(gray_path)
        # Colourful subjects get more CMY retention (lower GCR) and a lower
        # saturation boost than neutral ones.
        self.assertLess(vivid_values["gcr"], gray_values["gcr"])
        self.assertLessEqual(
            vivid_values["saturation"], gray_values["saturation"]
        )
        self.assertGreaterEqual(vivid_values["saturation"], 110)

    def test_contrast_300_keeps_smooth_shoulders(self):
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-contrast300-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = str(Path(folder) / "ramp.png")
        image = Image.new("L", (16, 16))
        for x in range(16):
            value = int(64 + x * 127 / 15)
            for y in range(16):
                image.putpixel((x, y), value)
        image.save(path)
        tones, _ = converter.prepare_image_tones(
            path,
            80,
            80,
            margin_mm=4,
            resolution_px=64,
            auto_levels=False,
            contrast=3.0,
            gcr=1.0,
            weights=(1, 1, 1, 1),
        )
        k = tones["k"]
        # Contrast 300 steepens the soft curve past the old 200 % ceiling
        # (a wider spread than contrast 2.0) yet keeps the shoulders finite.
        self.assertGreater(float(k.max()) - float(k.min()), 0.85)
        self.assertLess(float(k.max()), 0.99)
        self.assertGreater(float(k.min()), 0.01)

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

    def test_wave_rows_keep_bounded_spacing_across_row_tone_changes(self):
        spacing = 4.0
        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        page_mm = 64
        pixels_per_mm = 4
        pixel_count = page_mm * pixels_per_mm
        yy, xx = self.np.mgrid[0:pixel_count, 0:pixel_count]
        yy_mm = yy / pixels_per_mm
        xx_mm = xx / pixels_per_mm
        for angle_deg in converter.SCREEN_ANGLES_DEG.values():
            with self.subTest(angle_deg=angle_deg):
                radians = math.radians(angle_deg)
                local_normal = (
                    xx_mm * math.sin(radians) + yy_mm * math.cos(radians)
                )
                tone = (
                    0.7
                    + 0.3
                    * self.np.sin(
                        2.0 * self.np.pi * local_normal / (2.0 * spacing)
                    )
                ).astype("float32")
                waves = converter.screen_channel(
                    tone,
                    {
                        "off_x": 0.0,
                        "off_y": 0.0,
                        "width_mm": float(page_mm),
                        "height_mm": float(page_mm),
                        "pixels_w": pixel_count,
                        "pixels_h": pixel_count,
                    },
                    style="waves",
                    allow_variable_wave_spacing=True,
                    spacing_mm=spacing,
                    angle_deg=angle_deg,
                )
                local_rows = []
                for points in waves:
                    local_rows.append(
                        [
                            (
                                x * math.cos(radians) + y * math.sin(radians),
                                -x * math.sin(radians) + y * math.cos(radians),
                            )
                            for x, y in points
                        ]
                    )

                x_min = min(
                    point[0] for points in local_rows for point in points
                )
                sample_xs = [
                    x_min + spacing / 2.0 + index * 2.0 * spacing
                    for index in range(8)
                ]
                sample_x = max(
                    sample_xs,
                    key=lambda candidate: sum(
                        min(point[0] for point in row)
                        <= candidate
                        <= max(point[0] for point in row)
                        for row in local_rows
                    ),
                )
                # One quarter wavelength is where tone-driven amplitude has
                # its strongest effect on the visible gap between rows.
                ys = sorted(
                    value
                    for points in local_rows
                    if (value := value_at_x(points, sample_x)) is not None
                )
                # End rows have a one-sided tone window; guard the field.
                ys = ys[2:-2]
                gaps = [
                    second - first
                    for first, second in zip(ys, ys[1:])
                    if 0.1 <= second - first <= 2.0 * spacing
                ]
                self.assertGreaterEqual(len(gaps), 10)
                self.assertGreater(min(gaps), 0.85 * spacing)
                self.assertLess(max(gaps), 1.15 * spacing)
                self.assertLess(max(gaps) - min(gaps), 0.3 * spacing)

    def test_wave_rows_vary_depth_but_stay_bounded_on_a_vertical_gradient(self):
        spacing = 4.0
        yy, _xx = self.np.mgrid[0:64, 0:64]
        tone = (0.2 + 0.6 * yy / 63.0).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        amplitudes = []
        for points in waves:
            baseline = value_at_x(points, 0.0)
            crest = value_at_x(points, spacing / 2.0)
            if baseline is not None and crest is not None:
                amplitudes.append((baseline, crest - baseline))
        amplitudes.sort()
        self.assertGreaterEqual(len(amplitudes), 10)
        wave_amplitudes = [amplitude for _baseline, amplitude in amplitudes]
        self.assertGreater(
            max(wave_amplitudes) - min(wave_amplitudes),
            spacing * 0.12,
            "vertical tone must create visible depth",
        )
        self.assertLess(
            max(wave_amplitudes) - min(wave_amplitudes),
            spacing * 0.35,
            "depth variation must stay within the bounded row envelope",
        )

    def test_wave_rows_restore_vertical_tone_depth_without_crossing(self):
        spacing = 4.0
        yy, _xx = self.np.mgrid[0:64, 0:64]
        tone = (0.1 + 0.8 * yy / 63.0).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        amplitudes = []
        crest_y = []
        for points in waves:
            baseline = value_at_x(points, 0.0)
            crest = value_at_x(points, spacing / 2.0)
            if baseline is not None and crest is not None:
                amplitudes.append(abs(crest - baseline))
                crest_y.append(crest)

        self.assertGreaterEqual(len(amplitudes), 12)
        self.assertGreater(
            max(amplitudes) - min(amplitudes),
            spacing * 0.2,
            "vertical image tone must still create visible wave depth",
        )
        gaps = sorted(
            second - first for first, second in zip(crest_y, crest_y[1:])
        )
        self.assertGreater(min(gaps), 0.75 * spacing)
        self.assertLess(max(gaps), 1.25 * spacing)

    def test_wave_depth_can_follow_a_separate_luminance_field(self):
        spacing = 4.0
        yy, _xx = self.np.mgrid[0:64, 0:64]
        ink_mask = self.np.ones((64, 64), dtype="float32")
        depth_tone = (0.1 + 0.8 * yy / 63.0).astype("float32")
        waves = converter.screen_channel(
            ink_mask,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
            depth_tone=depth_tone,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        amplitudes = []
        for points in waves:
            baseline = value_at_x(points, 0.0)
            crest = value_at_x(points, spacing / 2.0)
            if baseline is not None and crest is not None:
                amplitudes.append(abs(crest - baseline))
        self.assertGreaterEqual(len(amplitudes), 12)
        self.assertGreater(
            max(amplitudes) - min(amplitudes),
            spacing * 0.2,
            "wave depth should follow scene luminance even where one ink "
            "channel is uniformly saturated",
        )

    def test_depth_wave_keeps_near_full_pitch_amplitude_at_full_tone(self):
        spacing = 4.0
        tone = self.np.ones((128, 128), dtype="float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 128,
                "pixels_h": 128,
            },
            style="waves_zero",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
            pen_diameter_mm=0.8,
            depth_tone=tone,
        )
        ranges = [
            max(y for _x, y in points) - min(y for _x, y in points)
            for points in waves
            if len(points) > 100
        ]
        self.assertGreater(min(ranges), spacing * 0.95)

    def test_depth_wave_shares_phase_while_amplitude_follows_tone(self):
        spacing = 4.0
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 64.0,
            "height_mm": 64.0,
            "pixels_w": 64,
            "pixels_h": 64,
        }
        tone = self.np.ones((64, 64), dtype="float32")
        yy, _xx = self.np.mgrid[0:64, 0:64]
        depth = (0.25 + 0.7 * yy / 63.0).astype("float32")
        rows = converter.screen_channel(
            tone,
            geometry,
            style="waves_zero",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
            pen_diameter_mm=0.8,
            depth_tone=depth,
        )
        rows = [points for points in rows if len(points) > 100]
        peaks = []
        ranges = []
        for points in rows:
            ys = [y for _x, y in points]
            ranges.append(max(ys) - min(ys))
            first_half = [point for point in points if point[0] <= spacing]
            peaks.append(max(first_half, key=lambda point: point[1])[0])
        self.assertLess(max(peaks) - min(peaks), 0.2)
        self.assertGreater(max(ranges), min(ranges) * 1.8)

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        ys = sorted(
            value
            for points in rows
            if (value := value_at_x(points, spacing * 0.5)) is not None
        )
        gaps = [second - first for first, second in zip(ys, ys[1:])]
        self.assertGreater(
            max(gaps) - min(gaps),
            spacing * 0.02,
            "phase-locked depth keeps crest phase, not exact row pitch",
        )

    def test_depth_wave_scales_amplitude_not_frequency_across_pitches(self):
        size = 128
        yy, _xx = self.np.mgrid[0:size, 0:size]
        tone = self.np.ones((size, size), dtype="float32")
        depth = self.np.where(
            yy < size * 0.42,
            0.12,
            0.92,
        ).astype("float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": float(size),
            "height_mm": float(size),
            "pixels_w": size,
            "pixels_h": size,
        }

        def crossings(points):
            baseline = points[0][1]
            signs = [1 if y > baseline else -1 for _x, y in points]
            return sum(
                first != second for first, second in zip(signs, signs[1:])
            )

        for spacing in (2.80, 3.36, 4.20):
            with self.subTest(spacing=spacing):
                waves = converter.screen_channel(
                    tone,
                    geometry,
                    style="waves_zero",
                    allow_variable_wave_spacing=True,
                    spacing_mm=spacing,
                    pen_diameter_mm=0.8,
                    depth_tone=depth,
                )
                rows = sorted(
                    (points for points in waves if len(points) > 100),
                    key=lambda points: sum(y for _x, y in points)
                    / len(points),
                )
                self.assertGreaterEqual(len(rows), 20)
                light_count = crossings(rows[1])
                dark_count = crossings(rows[-2])
                self.assertLessEqual(
                    abs(dark_count - light_count),
                    1,
                    "depth must change amplitude without changing row frequency",
                )
                light_range = max(y for _x, y in rows[1]) - min(
                    y for _x, y in rows[1]
                )
                dark_range = max(y for _x, y in rows[-2]) - min(
                    y for _x, y in rows[-2]
                )
                self.assertGreater(
                    dark_range,
                    light_range * 2.0,
                    "darker scene areas must retain visibly deeper waves",
                )

    def test_phase_locked_depth_clearance_scales_at_all_angles_and_pitches(
        self,
    ):
        import converter_core.cmyk as cmyk_core

        page_mm = 64.0
        pixels_per_mm = 4
        pixel_count = int(page_mm * pixels_per_mm)
        yy, xx = self.np.mgrid[0:pixel_count, 0:pixel_count]
        yy_mm = yy / pixels_per_mm
        xx_mm = xx / pixels_per_mm
        tone = self.np.ones((pixel_count, pixel_count), dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": page_mm,
            "height_mm": page_mm,
            "pixels_w": pixel_count,
            "pixels_h": pixel_count,
        }

        def value_at_x(points, x_value):
            lo, hi = 0, len(points) - 1
            while lo < hi:
                middle = (lo + hi) // 2
                if points[middle][0] < x_value:
                    lo = middle + 1
                else:
                    hi = middle
            if lo == 0:
                return points[0][1] if points[0][0] == x_value else None
            first, second = points[lo - 1], points[lo]
            if first[0] <= x_value <= second[0]:
                fraction = (x_value - first[0]) / max(
                    second[0] - first[0], 1e-9
                )
                return first[1] + fraction * (second[1] - first[1])
            return None

        minimum_clearance = 0.8 + converter.WAVE_MIN_EDGE_GAP_MM
        for spacing in (2.80, 3.36, 4.20):
            for angle_deg in converter.SCREEN_ANGLES_DEG.values():
                with self.subTest(spacing=spacing, angle_deg=angle_deg):
                    radians = math.radians(angle_deg)
                    local_normal = (
                        xx_mm * math.sin(radians)
                        + yy_mm * math.cos(radians)
                    )
                    depth = (
                        0.08
                        + 0.84
                        * (
                            0.5
                            + 0.5
                            * self.np.sin(
                                2.0
                                * self.np.pi
                                * local_normal
                                / (3.0 * spacing)
                            )
                        )
                    ).astype("float32")
                    waves = converter.screen_channel(
                        tone,
                        geometry,
                        style="waves_zero",
                        allow_variable_wave_spacing=True,
                        spacing_mm=spacing,
                        angle_deg=angle_deg,
                        pen_diameter_mm=0.8,
                        depth_tone=depth,
                    )
                    local_rows = [
                        [
                            (
                                x * math.cos(radians)
                                + y * math.sin(radians),
                                -x * math.sin(radians)
                                + y * math.cos(radians),
                            )
                            for x, y in points
                        ]
                        for points in waves
                    ]
                    local_rows.sort(
                        key=lambda points: sum(y for _x, y in points)
                        / len(points)
                    )
                    self.assertGreaterEqual(len(local_rows), 12)
                    for first, second in zip(
                        local_rows,
                        local_rows[1:],
                    ):
                        self.assertTrue(
                            cmyk_core._polyline_pair_is_clear(
                                cmyk_core._polyline_segments(first),
                                cmyk_core._polyline_segments(second),
                                minimum_clearance,
                            )
                        )

    def test_phase_locked_pitch_below_pen_envelope_fails_explicitly(self):
        tone = self.np.ones((64, 64), dtype="float32")
        with self.assertRaisesRegex(
            ValueError,
            "effective pitch is smaller than the pen width plus edge gap",
        ):
            converter.screen_channel(
                tone,
                {
                    "off_x": 0.0,
                    "off_y": 0.0,
                    "width_mm": 64.0,
                    "height_mm": 64.0,
                    "pixels_w": 64,
                    "pixels_h": 64,
                },
                style="waves_zero",
                allow_variable_wave_spacing=True,
                spacing_mm=0.8,
                pen_diameter_mm=0.8,
            )

    def test_depth_wave_keeps_row_variation_within_exact_clearance(self):
        spacing = 4.0
        yy, xx = self.np.mgrid[0:64, 0:64]
        tone = self.np.full((64, 64), 0.82, dtype="float32")
        depth = (
            0.1
            + 0.8 * yy / 63.0
            + 0.1 * self.np.sin(2.0 * self.np.pi * xx / 19.0)
        ).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_zero",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
            depth_tone=depth,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        for sample_x in (2.0, 10.0, 18.0, 26.0, 34.0, 42.0):
            with self.subTest(sample_x=sample_x):
                ys = sorted(
                    value
                    for points in waves
                    if (value := value_at_x(points, sample_x)) is not None
                )
                gaps = [
                    second - first
                    for first, second in zip(ys, ys[1:])
                    if 2.0 < second - first < 6.0
                ]
                self.assertGreaterEqual(len(gaps), 10)
                self.assertGreaterEqual(
                    min(gaps),
                    converter.WAVE_MIN_EDGE_GAP_MM
                    + 0.8
                    - 1e-6,
                )
                self.assertGreater(
                    max(gaps) - min(gaps),
                    0.05,
                    "row-specific waveform depth must survive the clearance "
                    "envelope",
                )

    def test_phase_locked_depth_preserves_untouched_rows(self):
        size = 128
        spacing = 2.8
        tone = self.np.ones((size, size), dtype="float32")
        depth = self.np.full((size, size), 0.80, dtype="float32")
        disturbed = depth.copy()
        # One short, steep tonal patch must not flatten unrelated rows across
        # the page. The old global safety scale reacted to this patch as if
        # every row contained the same maximum slope.
        disturbed[40:52, 60:64] = 0.10
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 64.0,
            "height_mm": 64.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        def vertical_ranges(depth_tone):
            waves = converter.screen_channel(
                tone,
                geometry,
                style="waves_zero",
                allow_variable_wave_spacing=True,
                spacing_mm=spacing,
                pen_diameter_mm=0.8,
                depth_tone=depth_tone,
            )
            rows = sorted(
                waves,
                key=lambda points: sum(y for _x, y in points)
                / len(points),
            )
            return [
                max(y for _x, y in points)
                - min(y for _x, y in points)
                for points in rows
            ]

        uniform_ranges = vertical_ranges(depth)
        disturbed_ranges = vertical_ranges(disturbed)
        self.assertGreaterEqual(len(uniform_ranges), 20)
        self.assertGreaterEqual(len(disturbed_ranges), 20)
        typical = sorted(uniform_ranges)[len(uniform_ranges) // 2]
        untouched = sorted(disturbed_ranges[:5])[2]
        self.assertGreater(
            untouched,
            typical * 0.9,
            "a local high-slope patch must not reduce amplitude of distant rows",
        )

    def test_phase_locked_blank_depth_changes_do_not_limit_inked_rows(self):
        size = 128
        spacing = 2.8
        ink_mask = self.np.zeros((size, size), dtype="float32")
        ink_mask[:, :64] = 1.0
        depth = self.np.full((size, size), 0.80, dtype="float32")
        changed_blank = depth.copy()
        changed_blank[:, 70:] = 0.10
        changed_blank[40:80, 90:94] = 1.0
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 64.0,
            "height_mm": 64.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        def visible_ranges(depth_tone):
            waves = converter.screen_channel(
                ink_mask,
                geometry,
                style="waves_zero",
                allow_variable_wave_spacing=True,
                spacing_mm=spacing,
                pen_diameter_mm=0.8,
                depth_tone=depth_tone,
            )
            ranges = []
            for points in waves:
                if len(points) <= 20:
                    continue
                ys = [y for _x, y in points]
                ranges.append(max(ys) - min(ys))
            return ranges

        uniform = sorted(visible_ranges(depth))
        changed = sorted(visible_ranges(changed_blank))
        self.assertGreaterEqual(len(uniform), 10)
        self.assertGreaterEqual(len(changed), 10)
        self.assertGreater(
            changed[len(changed) // 2],
            uniform[len(uniform) // 2] * 0.9,
            "depth changes over blank paper must not reduce ink-wave amplitude",
        )

    def test_phase_locked_clearance_checks_segment_distance(self):
        import converter_core.cmyk as cmyk_core

        positions = [
            [(0.0, 0.0), (1.0, 2.75), (2.0, 0.0)],
            [(0.0, 3.0), (1.0, 5.75), (2.0, 3.0)],
        ]
        self.assertFalse(
            cmyk_core._wave_clearance_ok(
                positions,
                4.0,
                minimum_clearance_mm=1.05,
            ),
            "the rows are three millimetres apart at every sampled column, "
            "but the steep segments come closer than a 1.05 mm pen envelope",
        )

    def test_clearance_does_not_impose_a_fixed_band_floor(self):
        import converter_core.cmyk as cmyk_core

        positions = [
            [(0.0, 1.0), (1.0, 1.0)],
            [(0.0, 3.4), (1.0, 3.4)],
        ]
        self.assertTrue(
            cmyk_core._wave_clearance_ok(
                positions,
                4.0,
                minimum_clearance_mm=1.05,
            ),
            "2.4 mm between rows is legal when the pen envelope is clear",
        )

    def test_phase_locked_wave_chords_stay_within_path_tolerance(self):
        spacing = 4.0
        tone = self.np.ones((64, 64), dtype="float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_zero",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
        )
        row = next(points for points in waves if len(points) > 100)
        baseline = row[0][1]
        amplitude = spacing * 0.5
        phase_rate = math.pi / spacing
        errors = []
        for first, second in zip(row, row[1:]):
            midpoint_x = (first[0] + second[0]) / 2.0
            chord_y = (first[1] + second[1]) / 2.0
            sine_y = baseline + amplitude * math.sin(
                phase_rate * midpoint_x
            )
            errors.append(abs(chord_y - sine_y))
        self.assertLess(max(errors), 0.05)

    def test_equidistant_wave_rows_keep_constant_spacing(self):
        spacing = 4.0
        yy, xx = self.np.mgrid[0:64, 0:64]
        tone = (
            0.2
            + 0.55 * xx / 63.0
            + 0.1 * self.np.sin(2.0 * self.np.pi * yy / (2.0 * spacing))
        ).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_even",
            spacing_mm=spacing,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        crest_values = []
        for sample_x in (2.0, 18.0, 34.0, 50.0):
            ys = sorted(
                value
                for points in waves
                if (value := value_at_x(points, sample_x)) is not None
            )
            gaps = [
                second - first
                for first, second in zip(ys, ys[1:])
                if abs((second - first) - spacing) < 0.1
            ]
            self.assertGreaterEqual(len(gaps), 10)
            self.assertLess(max(gaps) - min(gaps), 1e-5)
            crest_values.append((sample_x, ys))

        # The common waveform still changes size across the page even though
        # every row moves by exactly the same vertical offset.
        first_offsets = [
            value_at_x(points, 2.0) - points[0][1]
            for points in waves
            if value_at_x(points, 2.0) is not None
            and abs(points[0][0]) < 0.1
        ]
        later_offsets = [
            value_at_x(points, 18.0) - points[0][1]
            for points in waves
            if value_at_x(points, 18.0) is not None
            and abs(points[0][0]) < 0.1
        ]
        self.assertGreater(
            abs(sum(later_offsets) / len(later_offsets)
                - sum(first_offsets) / len(first_offsets)),
            0.2,
        )

    def test_dark_tone_changes_depth_without_dragging_row_baselines(self):
        spacing = 4.0
        _yy, xx = self.np.mgrid[0:64, 0:64]
        tone = self.np.where(xx < 32, 1.0, 0.15).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_even",
            spacing_mm=spacing,
            depth_tone=tone,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        # Ten and forty-two millimetres are one or more full wavelengths
        # apart. They sample dark and light tone at the same sine phase.
        dark_x = 10.0
        light_x = 42.0
        rows = sorted(waves, key=lambda points: points[0][1])
        dark_values = sorted(
            value
            for row in rows
            if (value := value_at_x(row, dark_x)) is not None
        )
        light_values = sorted(
            value
            for row in rows
            if (value := value_at_x(row, light_x)) is not None
        )
        dark_offsets = [
            value_at_x(row, dark_x) - row[0][1]
            for row in rows
        ]
        light_offsets = [
            value_at_x(row, light_x) - row[0][1]
            for row in rows
        ]

        for values in (dark_values, light_values):
            gaps = [
                second - first
                for first, second in zip(values, values[1:])
            ]
            self.assertEqual(len(gaps), 15)
            self.assertLess(max(gaps) - min(gaps), 1e-9)
            self.assertAlmostEqual(sum(gaps) / len(gaps), spacing, places=9)

        self.assertLess(max(dark_offsets) - min(dark_offsets), 1e-9)
        self.assertLess(max(light_offsets) - min(light_offsets), 1e-9)
        self.assertGreater(
            abs(sum(dark_offsets)) / len(dark_offsets),
            abs(sum(light_offsets)) / len(light_offsets) + 1.0,
            "full tone must deepen the wave without changing row baselines",
        )

    def test_equidistant_wave_rows_work_at_all_screen_angles(self):
        spacing = 4.0
        page_mm = 64.0
        pixels_per_mm = 4
        pixel_count = int(page_mm * pixels_per_mm)
        yy, xx = self.np.mgrid[0:pixel_count, 0:pixel_count]
        xx_mm = xx / pixels_per_mm
        yy_mm = yy / pixels_per_mm

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        for angle_deg in converter.SCREEN_ANGLES_DEG.values():
            with self.subTest(angle_deg=angle_deg):
                radians = math.radians(angle_deg)
                local_u = xx_mm * math.cos(radians) + yy_mm * math.sin(radians)
                local_v = -xx_mm * math.sin(radians) + yy_mm * math.cos(radians)
                tone = (
                    0.35
                    + 0.25 * (local_u - local_u.min()) / self.np.ptp(local_u)
                    + 0.1
                    * self.np.sin(
                        2.0 * self.np.pi * local_v / (2.0 * spacing)
                    )
                ).astype("float32")
                waves = converter.screen_channel(
                    tone,
                    {
                        "off_x": 0.0,
                        "off_y": 0.0,
                        "width_mm": page_mm,
                        "height_mm": page_mm,
                        "pixels_w": pixel_count,
                        "pixels_h": pixel_count,
                    },
                    style="waves_even",
                    spacing_mm=spacing,
                    angle_deg=angle_deg,
                )
                local_rows = [
                    [
                        (
                            x * math.cos(radians) + y * math.sin(radians),
                            -x * math.sin(radians) + y * math.cos(radians),
                        )
                        for x, y in points
                    ]
                    for points in waves
                ]
                min_u = min(point[0] for row in local_rows for point in row)
                max_u = max(point[0] for row in local_rows for point in row)
                for fraction in (0.2, 0.4, 0.6, 0.8):
                    sample_u = min_u + fraction * (max_u - min_u)
                    ys = sorted(
                        value
                        for row in local_rows
                        if (value := value_at_x(row, sample_u)) is not None
                    )
                    gaps = [
                        second - first
                        for first, second in zip(ys, ys[1:])
                        if abs((second - first) - spacing) < 0.1
                    ]
                    self.assertGreaterEqual(len(gaps), 6)
                    self.assertLess(max(gaps) - min(gaps), 1e-5)

    def test_legacy_wave_styles_default_to_equidistant_rows(self):
        spacing = 4.0
        tone = self.np.ones((64, 64), dtype="float32")
        yy, _xx = self.np.mgrid[0:64, 0:64]
        depth = (0.2 + 0.7 * yy / 63.0).astype("float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 64.0,
            "height_mm": 64.0,
            "pixels_w": 64,
            "pixels_h": 64,
        }
        for angle_deg in converter.SCREEN_ANGLES_DEG.values():
            expected = converter.screen_channel(
                tone,
                geometry,
                style="waves_even",
                spacing_mm=spacing,
                angle_deg=angle_deg,
                depth_tone=depth,
            )
            for legacy_style in ("waves", "waves_zero"):
                with self.subTest(
                    style=legacy_style,
                    angle_deg=angle_deg,
                ):
                    actual = converter.screen_channel(
                        tone,
                        geometry,
                        style=legacy_style,
                        spacing_mm=spacing,
                        angle_deg=angle_deg,
                        depth_tone=depth,
                    )
                    self.assertEqual(actual, expected)

    def test_wave_rows_approximate_the_sinusoid_within_path_tolerance(self):
        spacing = 4.0
        tone = self.np.ones((64, 64), dtype="float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
        )

        row = next(points for points in waves if len(points) > 20)
        baseline = row[0][1]
        amplitude = spacing * 0.5
        errors = []
        for first, second in zip(row, row[1:]):
            midpoint_x = (first[0] + second[0]) / 2.0
            chord_y = (first[1] + second[1]) / 2.0
            sine_y = baseline + amplitude * math.sin(
                2.0 * math.pi * midpoint_x / (2.0 * spacing)
            )
            errors.append(abs(chord_y - sine_y))

        self.assertLess(
            max(errors),
            0.05,
            "wave chords must not turn the intended sine into visible facets",
        )

    def test_wave_rows_still_break_over_blank_image_regions(self):
        tone = self.np.ones((64, 64), dtype="float32")
        tone[:, 28:36] = 0.0
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=4.0,
        )
        self.assertGreater(len(waves), 4)
        centers = [
            (min(point[0] for point in row) + max(point[0] for point in row))
            / 2.0
            for row in waves
            if max(point[0] for point in row) - min(point[0] for point in row) > 5
        ]
        self.assertTrue(
            all(
                center < 28.0 or center > 36.0
                for center in centers
            ),
            "a blank image band must split the wave instead of drawing through it",
        )

    def test_contours_need_a_gradient(self):
        ramp = self.np.tile(
            self.np.linspace(0.0, 1.0, 32, dtype="float32"), (32, 1)
        )
        contours = converter.screen_channel(
            ramp, self.geometry(), style="contours", spacing_mm=4.0
        )
        self.assertGreater(len(contours), 3)
        flat = self.np.full((32, 32), 0.8, dtype="float32")
        self.assertEqual(
            converter.screen_channel(
                flat, self.geometry(), style="contours", spacing_mm=4.0
            ),
            [],
        )

    def test_svg_document_groups_and_order(self):
        polyline = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
        document = converter.svg_document(
            {"c": [polyline], "k": [polyline]}, 50.0, 50.0, order=["c", "k"]
        )
        root = ET.fromstring(document)
        groups = [
            element
            for element in root.iter()
            if element.tag.split("}")[-1] == "g"
        ]
        self.assertEqual([group.get("data-ink") for group in groups], ["c", "k"])
        self.assertEqual(
            [group.get("stroke") for group in groups],
            [converter.CHANNEL_COLORS["c"], converter.CHANNEL_COLORS["k"]],
        )
        # Layer groups blend multiplicatively so external SVG viewers show
        # overprint the way the ink simulation does.
        self.assertTrue(
            all(
                "mix-blend-mode" in (group.get("style") or "")
                for group in groups
            )
        )

    def test_ink_tags_survive_the_geometry_pipeline(self):
        tagged = converter.tag_ink(
            [[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]], "c"
        )
        moved = converter.apply_geometry_settings(tagged, converter.Settings())
        self.assertEqual(getattr(moved[0], "ink", None), "c")
        clipped = converter.clip_contours_to_bed(moved, (10.0, 0.0), 3.0)
        self.assertTrue(clipped)
        self.assertTrue(all(getattr(c, "ink", None) == "c" for c in clipped))

    def test_cost_summary_names_both_strategies(self):
        from generator_tabs.cmyk_tab import format_cost_summary, format_seconds

        rows = {
            "c": {
                "marks": 10,
                "moves": 42,
                "x_count": 30,
                "y_count": 12,
                "draw_mm": 100.0,
                "seconds": 61.0,
            }
        }
        summary = format_cost_summary(rows)
        self.assertIn("x30/y12", summary)
        self.assertIn("C ", summary)
        self.assertIn("1m01s", summary)
        self.assertEqual(format_seconds(61.0), "1m01s")
        self.assertEqual(format_seconds(3600.0), "1h00m")

    def test_cost_summary_names_xy_only(self):
        from generator_tabs.cmyk_tab import format_cost_summary

        rows = {
            "k": {
                "marks": 4,
                "moves": 9,
                "x_count": 0,
                "y_count": 0,
                "draw_mm": 12.0,
                "seconds": 5.0,
            }
        }
        summary = format_cost_summary(rows)
        self.assertIn("XY only", summary)
        self.assertIn("5s", summary)


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class CmykTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from generator_tabs.cmyk_tab import CmykTab

        cls.CmykTab = CmykTab
        cls.app = QApplication.instance() or QApplication([])
        folder = tempfile.mkdtemp(prefix="cmyk-tab-")
        cls.folder = folder
        from PIL import Image

        image = Image.new("RGB", (48, 48), (255, 255, 255))
        for x in range(12, 36):
            for y in range(12, 36):
                image.putpixel((x, y), (0, 0, 0))
        cls.image_path = str(Path(folder) / "art.png")
        image.save(cls.image_path)
        # A full-ink, asymmetric image: every channel carries marks in a
        # different region, so per-ink bounding boxes differ strongly.
        colour = Image.new("RGB", (96, 96), (255, 255, 255))
        for x in range(96):
            for y in range(96):
                if x < 48 and y < 48:
                    colour.putpixel((x, y), (0, 200, 220))
                elif x >= 48 and y < 48:
                    colour.putpixel((x, y), (220, 0, 150))
                elif x < 48:
                    colour.putpixel((x, y), (240, 220, 0))
                else:
                    colour.putpixel((x, y), (40, 40, 40))
        cls.colour_path = str(Path(folder) / "colour.png")
        colour.save(cls.colour_path)

    def make_tab(self, host=None):
        host = host or FakeHost(self.image_path)
        tab = self.CmykTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(60)
        tab.page_h.setValue(60)
        tab.margin.setValue(4)
        tab.pitch.setValue(4.0)
        tab.max_marks.setValue(400)
        return tab

    @staticmethod
    def clean_checks():
        return {
            "drawing": 1,
            "travel": 0,
            "hold": 0,
            "strategies": {},
            "step": 0.0,
            "step_line": 0,
            "rate": 0.0,
            "rate_line": 0,
            "deviation": (0.0, 0.0, 0, ""),
            "tolerance": 0.05,
            "over_tolerance": 0,
            "rapids_with_rotation": 0,
            "fed_rotations": 0,
            "unwinds": 0,
            "cap": 15.0,
            "rate_cap": 500.0,
        }

    def test_build_svg_writes_every_layer_for_the_planner(self):
        tab = self.make_tab()
        path = tab.build_svg()
        root = ET.parse(path).getroot()
        self.assertEqual(svg_groups(root), list(converter.CHANNELS))
        tab.preview_boxes["k"].setChecked(False)
        path = tab.build_svg()
        root = ET.parse(path).getroot()
        self.assertEqual(svg_groups(root), list(converter.CHANNELS))
        self.assertEqual(tab.preview_visible_inks(), ["c", "m", "y"])

    def test_preview_can_hide_every_layer(self):
        tab = self.make_tab()
        for box in tab.preview_boxes.values():
            box.setChecked(False)
        path = tab.build_svg()
        self.assertTrue(Path(path).exists())
        self.assertEqual(tab.preview_visible_inks(), [])

    def test_every_screen_style_builds_all_four_layers(self):
        tab = self.make_tab()
        tab.levels.setValue(3)
        tab.overdraw.setValue(2)
        for style in (
            "halftone",
            "stipple",
            "lines",
            "rectilinear",
            "crosshatch",
            "waves_even",
            "gyroid",
            "tsp",
            "contours",
        ):
            tab.style.setCurrentIndex(tab.style.findData(style))
            root = ET.parse(tab.build_svg()).getroot()
            self.assertEqual(svg_groups(root), list(converter.CHANNELS), style)

    def test_analysis_worker_reports_strategy_split(self):
        from generator_tabs.cmyk_tab import ProgramAnalysisWorker

        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._ensure_layers()
        results = {}
        worker = ProgramAnalysisWorker(
            host,
            converter.Settings(),
            converter.DEFAULT_MOTION_ESTIMATE_SCALE,
            [("k", tab._layer_files["k"])],
        )
        worker.finished.connect(results.update)
        worker.run()
        record = results["k"]
        self.assertEqual(record["x_count"], 2)
        self.assertEqual(record["y_count"], 1)
        self.assertEqual(record["marks"], 2)
        self.assertGreater(record["seconds"], 0.0)

    def test_analysis_worker_passes_each_inks_screen_angle(self):
        from generator_tabs.cmyk_tab import ProgramAnalysisWorker

        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._ensure_layers()
        seen = {}
        analyze = host.analyze_program

        def recording_analyze(path, settings, cancel_check=None):
            seen[settings.row_lock_screen_angle_deg] = path
            return analyze(path, settings, cancel_check)

        host.analyze_program = recording_analyze
        worker = ProgramAnalysisWorker(
            host,
            converter.Settings(row_locked_compensation=True),
            converter.DEFAULT_MOTION_ESTIMATE_SCALE,
            [
                (channel, tab._layer_files[channel])
                for channel in converter.CHANNELS
            ],
        )
        results = {}
        worker.finished.connect(results.update)

        worker.run()

        self.assertEqual(
            set(seen),
            set(converter.SCREEN_ANGLES_DEG.values()),
        )
        self.assertEqual(set(results), set(converter.CHANNELS))

    def test_kinematics_bullets_override_the_settings(self):
        tab = self.make_tab()
        self.assertEqual(
            [button.property("choice_value") for button in tab.theta_mode._buttons],
            ["optimized", "fixed"],
            "the CMYK tab offers exactly the two kinematic bullets",
        )
        settings = tab.apply_tab_settings(converter.Settings())
        self.assertEqual(settings.theta_mode, "optimized")
        self.assertEqual(settings.theta_center_hold_diameter_mm, 60.0)
        tab.theta_mode.set_value("fixed")
        tab.center_hold.setValue(70.0)
        settings = tab.apply_tab_settings(converter.Settings())
        self.assertEqual(settings.theta_mode, "fixed")
        self.assertEqual(settings.theta_center_hold_diameter_mm, 70.0)
        self.assertEqual(tab._effective_settings().theta_mode, "fixed")

    def test_cmyk_wave_selector_only_offers_exact_spacing(self):
        tab = self.make_tab()
        self.assertEqual(tab.style.findData("waves"), -1)
        self.assertEqual(tab.style.findData("waves_zero"), -1)
        exact = tab.style.findData("waves_even")
        self.assertGreaterEqual(exact, 0)
        self.assertEqual(
            tab.style.itemText(exact),
            "Wave screen - equidistant rows",
        )
        tooltip = tab.style.toolTip().lower()
        self.assertIn("exactly one pitch apart", tooltip)
        self.assertIn("legacy variable-depth", tooltip)

    def test_wave_spacing_guard_row_locks_bed_compensation(self):
        tab = self.make_tab()
        tab.host.settings_for_source = mock.Mock(
            return_value=converter.default_settings()
        )
        tab.style.setCurrentIndex(tab.style.findData("waves_even"))

        guarded = tab._effective_settings()
        self.assertEqual(
            guarded.bed_compensation_path,
            converter.default_settings().bed_compensation_path,
        )
        self.assertTrue(guarded.row_locked_compensation)
        self.assertTrue(tab._wave_spacing_guard_active())

        tab.preserve_wave_pitch.setChecked(False)
        unguarded = tab._effective_settings()
        self.assertEqual(
            unguarded.bed_compensation_path,
            converter.default_settings().bed_compensation_path,
        )
        self.assertFalse(unguarded.row_locked_compensation)
        self.assertIn(
            "raw compensation may alter pitch",
            tab._summary_text().lower(),
        )

        tab.style.setCurrentIndex(tab.style.findData("rectilinear"))
        self.assertEqual(
            tab._effective_settings().bed_compensation_path,
            converter.default_settings().bed_compensation_path,
        )
        self.assertFalse(
            tab._effective_settings().row_locked_compensation
        )
        self.assertFalse(tab.preserve_wave_pitch.isEnabled())

        tab.style.setCurrentIndex(tab.style.findData("waves_even"))
        tab.calibration_mode.setChecked(True)
        self.assertFalse(tab._wave_spacing_guard_active())
        self.assertFalse(tab.preserve_wave_pitch.isEnabled())
        self.assertIn("not applicable", tab._summary_text().lower())
        self.assertEqual(
            tab._effective_settings().bed_compensation_path,
            converter.default_settings().bed_compensation_path,
        )

    def test_xy_only_layer_program_holds_the_bed(self):
        tab = self.make_tab()
        tab._ensure_layers()
        tab.theta_mode.set_value("fixed")
        settings = tab._effective_settings()
        contours = converter.read_svg(str(tab._layer_files["k"]), settings)
        plan = converter.plan_program(contours, settings)
        text = converter.contours_to_gcode(contours, settings, plan)
        self.assertIn(
            "(frame center 30.000,30.000 mm, bed motion XY only)", text
        )
        angles = set()
        for line in text.splitlines():
            if line.startswith(("G0 ", "G1 ", "G53 ")):
                angles.update(
                    float(value) for value in re.findall(r"A(-?\d+\.?\d*)", line)
                )
        self.assertEqual(angles, {0.0}, "XY only must never rotate the bed")
        strategies = set()
        for _planned, _points, _thetas, labels in plan["planned_jobs"]:
            strategies.update(label for label in labels if label)
        self.assertEqual(strategies, {"fixed"})

    def test_pen_offsets_shift_only_the_selected_ink(self):
        tab = self.make_tab()
        tab.registration_marks.setChecked(False)
        tab._ensure_layers()
        before = {
            channel: [list(line) for line in tab._layers[channel]]
            for channel in converter.CHANNELS
        }
        tab.offset_spins["m"][0].setValue(1.25)
        tab.offset_spins["m"][1].setValue(-0.50)
        tab._ensure_layers()
        for channel in converter.CHANNELS:
            dx, dy = (1.25, -0.50) if channel == "m" else (0.0, 0.0)
            after = tab._layers[channel]
            self.assertEqual(len(before[channel]), len(after), channel)
            for line_before, line_after in zip(before[channel], after):
                self.assertEqual(len(line_before), len(line_after), channel)
                for (x0, y0), (x1, y1) in zip(line_before, line_after):
                    self.assertAlmostEqual(x1, x0 + dx, places=6)
                    self.assertAlmostEqual(y1, y0 + dy, places=6)

    def test_measured_alignment_sets_opposite_corrections(self):
        tab = self.make_tab()
        tab.measured_spins["y"][0].setValue(1.20)
        tab.measured_spins["y"][1].setValue(-0.40)
        tab.measured_spins["c"][0].setValue(9.0)
        tab._apply_measured_offsets()
        self.assertAlmostEqual(
            tab.offset_spins["y"][0].value(), -1.20, places=2
        )
        self.assertAlmostEqual(
            tab.offset_spins["y"][1].value(), 0.40, places=2
        )
        self.assertEqual(tab.offset_spins["c"][0].value(), 0.0)

    def test_every_ink_inherits_the_centered_dense_compensation(self):
        host = FakeHost(self.colour_path)
        host.settings_for_source = lambda _tab: converter.default_settings()
        tab = self.make_tab(host)
        tab._ensure_layers()
        settings = tab._effective_settings()

        self.assertEqual(
            Path(settings.bed_compensation_path).name,
            "bed-error-compensation-2026-10-29-dense-v3-centered.json",
        )
        for channel in converter.CHANNELS:
            contours = converter.read_svg(
                str(tab._layer_files[channel]), settings
            )
            plan = converter.plan_program(contours, settings)
            self.assertEqual(
                plan["bed_compensation"].fingerprint,
                "18bfb4ed1c33",
                channel,
            )

    def test_pen_offsets_keep_the_shared_page_frame(self):
        tab = self.make_tab(FakeHost(self.colour_path))
        tab.scale_pct.setValue(280)
        tab.offset_spins["y"][0].setValue(3.0)
        tab.offset_spins["y"][1].setValue(-2.0)
        tab._ensure_layers()
        settings = tab._effective_settings()
        expected = (tab.page_w.value() / 2.0, tab.page_h.value() / 2.0)
        for channel in converter.CHANNELS:
            contours = converter.read_svg(
                str(tab._layer_files[channel]), settings
            )
            plan = converter.plan_program(contours, settings)
            self.assertAlmostEqual(
                plan["source_center"][0], expected[0], places=6, msg=channel
            )
            self.assertAlmostEqual(
                plan["source_center"][1], expected[1], places=6, msg=channel
            )

    def test_calibration_sheet_ignores_pen_offsets(self):
        tab = self.make_tab()
        tab.calibration_mode.setChecked(True)
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        tab._ensure_layers()
        before = {
            channel: [list(line) for line in tab._layers[channel]]
            for channel in converter.CHANNELS
        }
        tab.offset_spins["m"][0].setValue(2.0)
        tab._ensure_layers()
        for channel in converter.CHANNELS:
            self.assertEqual(tab._layers[channel], before[channel], channel)

    def test_pass_summary_reports_offsets_and_preflight(self):
        tab = self.make_tab()
        tab.offset_spins["m"][0].setValue(0.50)
        text = tab._summary_text()
        self.assertIn("pen offsets", text)
        self.assertIn("M +0.50", text)
        clean = {"c": {"checks": self.clean_checks()}}
        self.assertIn("preflight OK", tab._summary_text(clean))
        broken = self.clean_checks()
        broken["step"] = 20.0
        self.assertIn(
            "preflight BLOCKED",
            tab._summary_text({"c": {"checks": broken}}),
        )

    def test_hard_preflight_violation_blocks_save(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        broken = self.clean_checks()
        broken["rate"] = 600.0
        results = {
            channel: {
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "checks": dict(broken),
            }
            for channel in converter.CHANNELS
        }
        tab._write_files(results)
        self.assertEqual(host.saved_labels, [])
        self.assertIn("preflight blocked", tab.status.text().lower())

    def test_artwork_save_writes_a_set_manifest(self):
        host = FakeHost(self.image_path)
        host.settings_for_source = mock.Mock(
            return_value=converter.default_settings()
        )
        tab = self.make_tab(host)
        tab.style.setCurrentIndex(tab.style.findData("waves_even"))
        tab.offset_spins["m"][0].setValue(0.75)
        checks = self.clean_checks()
        results = {
            channel: {
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "checks": dict(checks),
            }
            for channel in converter.CHANNELS
        }
        tab._write_files(results)
        manifest = Path(host.saved_paths["cyan"]).with_name("art-cmyk-set.json")
        self.assertTrue(manifest.exists())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["kind"], "cmyk-print-set")
        self.assertEqual(data["version"], 3)
        self.assertAlmostEqual(data["pen_offsets_mm"]["m"][0], 0.75)
        self.assertEqual(set(data["preflight"]), set(converter.CHANNELS))
        self.assertEqual(
            data["source"]["sha256"],
            hashlib.sha256(Path(self.image_path).read_bytes()).hexdigest(),
        )
        self.assertEqual(
            data["screen"]["style"],
            tab.style.currentData(),
        )
        self.assertEqual(
            data["screen"]["wave_phase_mode"],
            "identical_translated_rows",
        )
        self.assertNotIn(
            "wave_frequency_tone_gain",
            data["screen"],
        )
        self.assertAlmostEqual(
            data["screen"]["effective_pitch_mm"],
            tab.pitch.value() * tab.scale_pct.value() / 100.0,
        )
        self.assertEqual(data["ink_processing"]["weights"]["y"], 1.0)
        self.assertEqual(
            data["bed_compensation_path"],
            converter.default_settings().bed_compensation_path,
        )
        self.assertTrue(data["screen"]["preserve_exact_row_pitch"])
        self.assertEqual(
            data["bed_compensation"]["mode"],
            "row_locked_projection",
        )
        self.assertEqual(
            data["bed_compensation"]["profile_fingerprint"],
            "18bfb4ed1c33",
        )
        self.assertEqual(
            set(data["bed_compensation"]["screen_angles_deg"]),
            set(converter.CHANNELS),
        )
        self.assertEqual(
            data["ink_processing"]["sharpening"],
            {
                "enabled": True,
                "amount_pct": 70.0,
                "radius_mm": 1.5,
            },
        )
        self.assertIn("bed_compensation_path", data)
        for channel in converter.CHANNELS:
            saved = Path(
                host.saved_paths[converter.CHANNEL_LABELS[channel].lower()]
            )
            self.assertEqual(
                data["file_sha256"][channel],
                hashlib.sha256(saved.read_bytes()).hexdigest(),
            )
        self.assertIn("Set manifest", tab.status.text())

    def test_scaled_ink_layers_share_the_page_frame(self):
        tab = self.make_tab(FakeHost(self.colour_path))
        tab.scale_pct.setValue(280)
        tab.registration_marks.setChecked(False)
        tab._ensure_layers()
        settings = tab._effective_settings()
        expected = (tab.page_w.value() / 2.0, tab.page_h.value() / 2.0)
        scaled_radii = {}
        for channel in converter.CHANNELS:
            contours = converter.read_svg(
                str(tab._layer_files[channel]), settings
            )
            plan = converter.plan_program(contours, settings)
            anchor = plan["source_center"]
            self.assertAlmostEqual(anchor[0], expected[0], places=6, msg=channel)
            self.assertAlmostEqual(anchor[1], expected[1], places=6, msg=channel)
            scaled_radii[channel] = max(
                math.hypot(x, y)
                for contour in plan["contours"]
                for x, y in contour
            )

        # The Artwork scale control still sizes the print: 280 % must draw
        # appreciably larger than 100 % while both stay in one frame.
        tab.scale_pct.setValue(100)
        tab._ensure_layers()
        settings = tab._effective_settings()
        plain_radii = []
        for channel in converter.CHANNELS:
            contours = converter.read_svg(
                str(tab._layer_files[channel]), settings
            )
            plan = converter.plan_program(contours, settings)
            plain_radii.append(
                max(
                    math.hypot(x, y)
                    for contour in plan["contours"]
                    for x, y in contour
                )
            )
        self.assertGreater(max(scaled_radii.values()), 2.0 * max(plain_radii))

    def test_save_writes_one_file_per_ink(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._ensure_layers()
        results = {
            channel: {
                "marks": 1,
                "moves": 3,
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "x_count": 1,
                "y_count": 0,
                "x_mm": 1.0,
                "y_mm": 0.0,
                "draw_mm": 1.0,
                "seconds": 1.0,
            }
            for channel in converter.CHANNELS
        }
        tab._analysis = results
        tab._analysis_key = tab._control_key()
        tab._write_files(results)
        self.assertEqual(host.saved_labels, ["cyan", "magenta", "yellow", "black"])
        for channel in converter.CHANNELS:
            self.assertTrue(
                Path(host.saved_paths[converter.CHANNEL_LABELS[channel].lower()]).exists()
            )

    def test_preview_loads_every_layer_and_filters_live(self):
        tab = self.make_tab()
        tab.build_svg()
        # Every layer is loaded; the checkboxes only drive the live filter.
        self.assertEqual(
            [ink for ink, _path in tab.preview_layers()], list(converter.CHANNELS)
        )
        tab.preview_boxes["m"].setChecked(False)
        tab.build_svg()
        self.assertEqual(
            [ink for ink, _path in tab.preview_layers()], list(converter.CHANNELS)
        )
        self.assertEqual(tab.preview_visible_inks(), ["c", "y", "k"])

    def test_preview_toggle_notifies_the_host_live(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab.preview_boxes["m"].setChecked(False)
        self.assertEqual(host.visibility_updates, 1)
        tab.preview_boxes["m"].setChecked(True)
        self.assertEqual(host.visibility_updates, 2)

    def test_shipped_defaults_suit_a_photo(self):
        tab = self.CmykTab(FakeHost(self.image_path))
        self.addCleanup(tab.deleteLater)
        self.assertTrue(tab.auto_levels.isChecked())
        self.assertFalse(tab.solid_dots.isChecked())
        self.assertEqual(tab.style.currentData(), "rectilinear")
        self.assertEqual(tab.levels.value(), 8)
        self.assertAlmostEqual(tab.pitch.value(), 0.1, places=3)
        self.assertAlmostEqual(tab.gcr.value(), 95.0, places=3)
        self.assertAlmostEqual(tab.saturation.value(), 115.0, places=3)
        self.assertAlmostEqual(tab.contrast.value(), 285.0, places=3)
        self.assertAlmostEqual(tab.brightness.value(), 170.0, places=3)
        self.assertTrue(tab.sharpen.isChecked())
        self.assertAlmostEqual(tab.sharpen_amount.value(), 70.0, places=3)
        self.assertAlmostEqual(tab.sharpen_radius.value(), 1.5, places=3)
        self.assertAlmostEqual(tab.gamma.value(), 1.40, places=2)
        self.assertAlmostEqual(tab.dot_size.value(), 100.0, places=3)
        self.assertEqual(tab.max_marks.value(), 40000)
        self.assertEqual(tab.resolution.value(), 10000)
        self.assertAlmostEqual(tab.scale_pct.value(), 280.0, places=3)
        self.assertAlmostEqual(tab.weight_c.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_m.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_y.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_k.value(), 100.0, places=3)

    def test_sharpening_settings_reach_preparation_and_invalidate_layers(self):
        tab = self.make_tab()
        tab.scale_pct.setValue(200)
        captured = []
        prepare = converter.prepare_image_tones

        def capture_prepare(*args, **kwargs):
            captured.append(dict(kwargs))
            return prepare(*args, **kwargs)

        before = tab._control_key()
        tab.sharpen_amount.setValue(95)
        tab.sharpen_radius.setValue(2.2)
        self.assertNotEqual(before, tab._control_key())
        with (
            mock.patch.object(
                converter,
                "prepare_image_tones",
                side_effect=capture_prepare,
            ),
            mock.patch.object(converter, "screen_channel", return_value=[]),
        ):
            tab._ensure_layers()
            tab.sharpen.setChecked(False)
            tab._ensure_layers()

        self.assertEqual(captured[0]["sharpen_pct"], 95.0)
        self.assertAlmostEqual(
            captured[0]["sharpen_radius_mm"],
            2.2 / 2.0,
            places=6,
        )
        self.assertEqual(captured[1]["sharpen_pct"], 0.0)
        self.assertFalse(tab.sharpen_amount.isEnabled())
        self.assertFalse(tab.sharpen_radius.isEnabled())
        tab.sharpen.setChecked(True)
        self.assertTrue(tab.sharpen_amount.isEnabled())
        self.assertTrue(tab.sharpen_radius.isEnabled())

    def test_resolution_is_not_capped_at_2000(self):
        tab = self.make_tab()
        tab.resolution.setValue(8192)
        self.assertEqual(tab.resolution.value(), 8192)

    def test_artwork_scale_scales_the_screened_marks(self):
        tab = self.make_tab()
        tab.scale_pct.setValue(100)
        tab._ensure_layers()
        full = [
            point
            for channel in converter.CHANNELS
            for line in tab._layers[channel]
            for point in line
        ]
        tab.scale_pct.setValue(50)
        tab._ensure_layers()
        half = [
            point
            for channel in converter.CHANNELS
            for line in tab._layers[channel]
            for point in line
        ]

        def bounds(points):
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            return min(xs), min(ys), max(xs), max(ys)

        full_box = bounds(full)
        half_box = bounds(half)
        self.assertAlmostEqual(
            half_box[2] - half_box[0],
            0.5 * (full_box[2] - full_box[0]),
            delta=0.05,
        )
        self.assertAlmostEqual(
            half_box[3] - half_box[1],
            0.5 * (full_box[3] - full_box[1]),
            delta=0.05,
        )
        self.assertAlmostEqual(
            (half_box[0] + half_box[2]) / 2.0,
            (full_box[0] + full_box[2]) / 2.0,
            delta=1.0,
        )

    def test_artwork_scale_keeps_wave_tolerance_in_paper_space(self):
        tab = self.make_tab(FakeHost(self.colour_path))
        tab.scale_pct.setValue(280)
        tab.path_tolerance.setValue(0.05)
        captured = []
        captured_depth = []
        screen_channel = converter.screen_channel

        def capture_tolerance(*args, **kwargs):
            captured.append(kwargs.get("path_tolerance_mm"))
            captured_depth.append(kwargs.get("depth_tone"))
            return screen_channel(*args, **kwargs)

        with mock.patch.object(
            converter, "screen_channel", side_effect=capture_tolerance
        ):
            tab._ensure_layers()

        self.assertEqual(len(captured), len(converter.CHANNELS))
        for tolerance in captured:
            self.assertAlmostEqual(tolerance, 0.05 / 2.8)
        self.assertTrue(all(depth is not None for depth in captured_depth))

    def test_artwork_scale_keeps_wave_clearance_in_paper_space(self):
        tab = self.make_tab(FakeHost(self.colour_path))
        tab.scale_pct.setValue(280)
        tab.pen_width.setValue(0.8)
        captured = []
        screen_channel = converter.screen_channel

        def capture_clearance(*args, **kwargs):
            captured.append(kwargs.get("row_clearance_mm"))
            return screen_channel(*args, **kwargs)

        with mock.patch.object(
            converter, "screen_channel", side_effect=capture_clearance
        ):
            tab._ensure_layers()

        self.assertEqual(len(captured), len(converter.CHANNELS))
        expected = (
            tab.pen_width.value() + converter.WAVE_MIN_EDGE_GAP_MM
        ) / 2.8
        for clearance in captured:
            self.assertAlmostEqual(clearance, expected)

    def test_hatch_levels_allow_more_families(self):
        tab = self.make_tab()
        tab.levels.setValue(9)
        self.assertEqual(tab.levels.value(), 9)

    def test_pitch_allows_solid_fill_spacing(self):
        tab = self.make_tab()
        tab.pitch.setValue(0.2)
        self.assertEqual(tab.pitch.value(), 0.2)

    def test_auto_button_applies_photo_settings(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab.saturation.setValue(100)
        tab.contrast.setValue(100)
        tab.brightness.setValue(100)
        tab.gamma.setValue(1.0)
        tab.gcr.setValue(100)
        tab.scale_pct.setValue(150)
        pitch_before = tab.pitch.value()
        tab.auto_button.click()
        values = converter.auto_photo_settings(
            self.image_path,
            pen_width_mm=tab.pen_width.value(),
            effective_pitch_mm=(
                tab.pitch.value() * tab.scale_pct.value() / 100.0
            ),
        )
        self.assertEqual(tab.saturation.value(), values["saturation"])
        self.assertEqual(tab.contrast.value(), values["contrast"])
        self.assertEqual(tab.brightness.value(), values["brightness"])
        self.assertEqual(tab.gcr.value(), values["gcr"])
        self.assertAlmostEqual(tab.gamma.value(), values["gamma"], places=2)
        self.assertTrue(tab.auto_levels.isChecked())
        # Auto no longer touches Dot pitch: the operator's spacing choice
        # stands; the status line suggests what Match pen would set instead.
        self.assertAlmostEqual(tab.pitch.value(), pitch_before, places=3)
        self.assertIn("Auto:", tab.status.text())
        self.assertIn("Dot pitch", tab.status.text())
        self.assertIn("Match pen would suggest", tab.status.text())

    def test_auto_button_applies_wave_photo_fidelity_settings(self):
        host = FakeHost(self.colour_path)
        tab = self.make_tab(host)
        tab.style.setCurrentIndex(tab.style.findData("waves_even"))
        tab.sharpen.setChecked(False)
        tab.sharpen_amount.setValue(70)
        tab.sharpen_radius.setValue(1.0)
        values = converter.auto_photo_settings(
            self.colour_path,
            pen_width_mm=tab.pen_width.value(),
            effective_pitch_mm=(
                tab.pitch.value() * tab.scale_pct.value() / 100.0
            ),
            style="waves_even",
            dot_pitch_mm=tab.pitch.value(),
        )

        tab.auto_button.click()

        self.assertEqual(tab.saturation.value(), values["saturation"])
        self.assertEqual(tab.contrast.value(), values["contrast"])
        self.assertEqual(tab.brightness.value(), values["brightness"])
        self.assertEqual(tab.gcr.value(), values["gcr"])
        self.assertAlmostEqual(tab.gamma.value(), values["gamma"], places=2)
        self.assertTrue(tab.sharpen.isChecked())
        self.assertEqual(tab.sharpen_amount.value(), values["sharpen_pct"])
        self.assertEqual(
            tab.sharpen_radius.value(),
            values["sharpen_radius_mm"],
        )
        self.assertAlmostEqual(tab.pitch.value(), values["dot_pitch_mm"])

    def test_match_pen_pitch_uses_the_effective_scale(self):
        tab = self.make_tab()
        tab.scale_pct.setValue(200)
        tab.pen_width.setValue(0.3)
        tab.match_pen_pitch()
        self.assertAlmostEqual(tab.pitch.value(), 0.15, places=2)
        self.assertIn("matches", tab.status.text())

    def test_registration_crosses_are_identical_on_every_ink(self):
        tab = self.make_tab()
        tab.registration_marks.setChecked(True)
        tab._ensure_layers()
        crosses = tab._registration_crosses()
        self.assertEqual(len(crosses), 8)
        for channel in converter.CHANNELS:
            self.assertEqual(tab._layers[channel][-8:], crosses, channel)
        tab.registration_marks.setChecked(False)
        tab._ensure_layers()
        for channel in converter.CHANNELS:
            self.assertNotEqual(tab._layers[channel][-8:], crosses, channel)

    def test_max_marks_is_not_capped_at_40000(self):
        tab = self.make_tab()
        tab.max_marks.setValue(80000)
        self.assertEqual(tab.max_marks.value(), 80000)

    def test_preview_defers_exact_planning_until_save(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        self.assertFalse(hasattr(tab, "analyze_button"))
        calls = []
        tab.start_analysis = lambda: calls.append("plan")
        tab.on_preview_finished()
        self.assertEqual(calls, [])
        self.assertIn("when you save", tab.cost_label.text())
        self.assertIn("when you save", host.status[-1])

    def test_save_starts_deferred_exact_planning(self):
        tab = self.make_tab()
        tab._write_channels = lambda: ["k"]
        calls = []
        tab.start_analysis = lambda: calls.append("plan")
        tab.save_all()
        self.assertEqual(calls, ["plan"])
        self.assertTrue(tab._pending_save)
        self.assertIn("before save", tab.status.text())

    def test_planning_state_reaches_the_shared_cancel_control(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._set_planning_state(True)
        self.assertTrue(tab.cancel_button.isEnabled())
        self.assertFalse(tab.save_button.isEnabled())
        self.assertEqual(host.planning_states[-1], (tab, True))

        tab._set_planning_state(False)
        self.assertFalse(tab.cancel_button.isEnabled())
        self.assertTrue(tab.save_button.isEnabled())
        self.assertEqual(host.planning_states[-1], (tab, False))

    def test_calibration_sheet_mode_builds_and_saves_manifest(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab.calibration_mode.setChecked(True)
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        path = tab.build_svg()
        root = ET.parse(path).getroot()
        self.assertEqual(svg_groups(root), list(converter.CHANNELS))
        self.assertIsNotNone(tab._layers_manifest)
        self.assertGreater(len(tab._layers_manifest["patches"]), 80)
        results = {
            channel: {
                "marks": 1,
                "moves": 3,
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "x_count": 1,
                "y_count": 0,
                "x_mm": 1.0,
                "y_mm": 0.0,
                "draw_mm": 1.0,
                "seconds": 1.0,
            }
            for channel in converter.CHANNELS
        }
        tab._analysis = results
        tab._analysis_key = tab._control_key()
        tab._write_files(results)
        manifest_path = Path(host.saved_paths["cyan"]).with_name(
            "art-cmyk-calibration.json"
        )
        self.assertTrue(manifest_path.exists())
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data["kind"], "cmyk-calibration-sheet")
        self.assertIn("Calibration manifest", tab.status.text())

    def test_calibration_sheet_mode_needs_no_artwork(self):
        tab = self.make_tab(FakeHost(""))
        tab.calibration_mode.setChecked(True)
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        path = tab.build_svg()
        self.assertTrue(Path(path).exists())

    def test_calibration_mode_changes_the_layer_key(self):
        tab = self.make_tab()
        before = tab._control_key()
        tab.calibration_mode.setChecked(True)
        self.assertNotEqual(before, tab._control_key())

    def test_calibration_sheet_reports_small_pages(self):
        tab = self.make_tab()
        tab.calibration_mode.setChecked(True)
        with self.assertRaises(ValueError):
            tab.build_svg()

    def test_calibration_sheet_follows_the_line_screen(self):
        tab = self.make_tab()
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        self.assertEqual(tab.calibration_screen.currentData(), "match")
        tab.style.setCurrentIndex(tab.style.findData("lines"))
        tab.calibration_mode.setChecked(True)
        tab.build_svg()
        self.assertEqual(
            tab._layers_manifest["sheet_settings"]["style"], "lines"
        )
        tab.calibration_screen.setCurrentIndex(
            tab.calibration_screen.findData("halftone")
        )
        tab.build_svg()
        self.assertEqual(
            tab._layers_manifest["sheet_settings"]["style"], "halftone"
        )

    def test_calibration_sheet_follows_the_rectilinear_fill(self):
        tab = self.make_tab()
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        tab.style.setCurrentIndex(tab.style.findData("rectilinear"))
        tab.calibration_mode.setChecked(True)
        tab.build_svg()
        self.assertEqual(
            tab._layers_manifest["sheet_settings"]["style"], "rectilinear"
        )


class FakeHost:
    """Minimal host: analysis is synthetic, saving writes real temp files."""

    def __init__(self, artwork):
        self._artwork = artwork
        self.status = []
        self.log = []
        self.saved_labels = []
        self.saved_paths = {}
        self.visibility_updates = 0
        self.planning_states = []
        self._folder = tempfile.mkdtemp(prefix="cmyk-save-")

    def artwork_path(self):
        return self._artwork

    def generator_status(self, message):
        self.status.append(message)

    def generator_planning_changed(self, tab, running):
        self.planning_states.append((tab, running))

    def update_preview_visibility(self):
        self.visibility_updates += 1

    def settings_for_source(self, _tab):
        return converter.Settings()

    def motion_estimate_scale(self):
        return converter.DEFAULT_MOTION_ESTIMATE_SCALE

    def analyze_program(self, _path, _settings, cancel_check=None):
        moves = [
            {
                "type": "draw",
                "strategy": "x_theta",
                "motion_length": 2.0,
                "duration_ms": 1000.0,
            },
            {
                "type": "draw",
                "strategy": "x_theta",
                "motion_length": 2.0,
                "duration_ms": 1000.0,
            },
            {
                "type": "draw",
                "strategy": "y_theta",
                "motion_length": 1.0,
                "duration_ms": 500.0,
            },
            {"type": "pen_down", "duration_ms": 600.0},
        ]
        return {
            "contours": [[(0.0, 0.0), (1.0, 1.0)], [(1.0, 1.0), (2.0, 2.0)]],
            "moves": moves,
            "gcode": "; synthetic\nG1 X0 Y0\n",
            "stats": {},
        }

    def export_program_set(self, entries, base_path=None, default_base=""):
        del base_path, default_base
        written = []
        for label, gcode in entries:
            path = str(Path(self._folder) / f"art-cmyk-{label}.gcode")
            Path(path).write_text(gcode, encoding="utf-8")
            self.saved_labels.append(label)
            self.saved_paths[label] = path
            written.append(path)
        return written


if __name__ == "__main__":
    unittest.main()
