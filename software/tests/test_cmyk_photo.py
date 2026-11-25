"""CMYK photo processing and automatic exposure behavior."""

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


class CmykPhotoTests(unittest.TestCase):
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
            color_match=False,
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

    def test_auto_photo_settings_preserve_detail_without_extra_contrast(self):
        import numpy as np
        from PIL import Image, ImageFilter
        from converter_core import cmyk as cmyk_module

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
        rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
        luminance = rgb @ np.array(
            [0.299, 0.587, 0.114],
            dtype=np.float32,
        )
        low, high = np.percentile(luminance, [1.0, 99.0])
        processed = cmyk_module._auto_curve_rgb(
            rgb,
            low,
            high,
            mid["auto_levels"],
            mid["saturation"],
            mid["contrast"],
            mid["brightness"],
        )
        tones = converter.rgb_to_cmyk_tone(
            processed,
            gcr=mid["gcr"] / 100.0,
            weights=(1, 1, 1, 1),
            gamma=mid["gamma"],
        )
        predicted = converter.predict_cmyk_rgb(tones)
        source_detail = cmyk_module._detail_score(luminance)
        predicted_detail = cmyk_module._detail_score(
            predicted @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        )
        self.assertLessEqual(mid["predicted_rgb_error"], 3.0)
        self.assertGreaterEqual(predicted_detail, source_detail * 0.9)

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

    def test_edge_flow_auto_preserves_highlights_and_midtone_density(self):
        import numpy as np
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-edge-auto-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        # Warm highlight-to-shadow portrait ramp: the case where a generic
        # sparse-screen search used to choose gamma 0.8 and bury the forehead.
        yy, xx = np.mgrid[0:96, 0:128]
        image = np.empty((96, 128, 3), dtype="float32")
        image[:] = (0.10, 0.16, 0.08)
        image[8:88, 30:98] = (0.88, 0.66, 0.52)
        image[8:88, 30:98, 0] += (1.0 - xx[8:88, 30:98] / 127.0) * 0.09
        image = np.clip(image * 255.0, 0.0, 255.0).astype("uint8")
        path = str(Path(folder) / "warm-portrait.png")
        Image.fromarray(image).save(path)

        values = converter.auto_photo_settings(
            path,
            pen_width_mm=0.8,
            effective_pitch_mm=0.31,
            style="edge_flow",
            dot_pitch_mm=0.31,
        )

        self.assertFalse(values["auto_levels"])
        # The shared Edge-flow gate is opportunistic along a sparse streamline
        # network. Reporting a single-digit error here would repeat the old
        # coverage-only deception; the estimate must reflect that missing ink.
        self.assertGreaterEqual(values["predicted_rgb_error"], 10.0)
        self.assertLessEqual(values["predicted_rgb_error"], 48.0)
        self.assertEqual(
            values["weights"],
            {"c": 100.0, "m": 100.0, "y": 100.0, "k": 100.0},
        )
        self.assertNotIn("dot_pitch_mm", values)

        tones, _geometry = converter.prepare_image_tones(
            path,
            100,
            100,
            margin_mm=6,
            brightness=values["brightness"],
            saturation=values["saturation"] / 100.0,
            contrast=values["contrast"] / 100.0,
            gcr=values["gcr"] / 100.0,
            weights=tuple(
                values["weights"][channel] / 100.0
                for channel in converter.CHANNELS
            ),
            gamma=values["gamma"],
            auto_levels=values["auto_levels"],
        )
        mean_coverage = float(
            np.mean([tones[channel].mean() for channel in converter.CHANNELS])
        )
        # Colour fitting still has to leave enough ink for the path-local
        # portrait screen rather than washing it into a sparse sketch.
        self.assertGreaterEqual(mean_coverage, 0.38)

    def test_edge_flow_auto_keeps_normal_exposure_for_large_pens(self):
        import numpy as np
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-edge-auto-wide-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        yy, xx = np.mgrid[0:128, 0:160]
        image = np.empty((128, 160, 3), dtype=np.float32)
        image[:] = (0.20, 0.16, 0.12)
        face = (
            ((xx - 80.0) / 54.0) ** 2
            + ((yy - 68.0) / 58.0) ** 2
        ) < 1.0
        skin = 0.70 + 0.17 * np.cos((xx - 58.0) / 38.0)
        image[face] = np.stack(
            (skin[face], skin[face] * 0.74, skin[face] * 0.55),
            axis=1,
        )
        image[70:96, 68:96] *= 0.62
        image = np.clip(image * 255.0, 0.0, 255.0).astype("uint8")
        path = str(Path(folder) / "large-pen-portrait.png")
        Image.fromarray(image).save(path)

        values = converter.auto_photo_settings(
            path,
            pen_width_mm=0.9,
            effective_pitch_mm=1.8,
            style="edge_flow",
            flow_layers=3,
        )

        # A large pen cannot compensate for open spacing by crushing the
        # photograph into low-brightness, high-contrast ink.
        self.assertGreaterEqual(values["brightness"], 100)
        self.assertLessEqual(values["contrast"], 180)
        self.assertGreaterEqual(values["gamma"], 1.0)
        self.assertLessEqual(values["saturation"], 120)
        self.assertLessEqual(values["gcr"], 80)

    def test_edge_flow_auto_improves_the_process_ink_prediction(self):
        import numpy as np
        from PIL import Image
        from converter_core import cmyk as cmyk_module

        folder = tempfile.mkdtemp(prefix="cmyk-auto-process-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        image = np.empty((64, 96, 3), dtype=np.uint8)
        image[:, :, :] = (92, 112, 64)
        image[4:30, 8:88] = (224, 185, 158)
        image[34:58, 10:42] = (126, 82, 54)
        image[34:58, 50:86] = (58, 126, 146)
        path = str(Path(folder) / "colour-card.png")
        Image.fromarray(image).save(path)

        baseline = cmyk_module._auto_photo_baseline_settings(
            path,
            pen_width_mm=0.5,
            effective_pitch_mm=0.52,
            style="edge_flow",
        )
        chosen = converter.auto_photo_settings(
            path,
            pen_width_mm=0.5,
            effective_pitch_mm=0.52,
            style="edge_flow",
            dot_pitch_mm=0.2,
        )

        source = (
            np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
            / 255.0
        )
        luminance = source @ np.array(
            [0.299, 0.587, 0.114],
            dtype=np.float32,
        )
        low, high = np.percentile(luminance, [1.0, 99.0])

        def predicted_error(values):
            processed = cmyk_module._auto_curve_rgb(
                source,
                low,
                high,
                values["auto_levels"],
                values["saturation"],
                values["contrast"],
                values["brightness"],
            )
            weights = values.get(
                "weights",
                {"c": 100.0, "m": 100.0, "y": 100.0, "k": 100.0},
            )
            tones = converter.rgb_to_cmyk_tone(
                processed,
                gcr=values["gcr"] / 100.0,
                weights=tuple(
                    weights[channel] / 100.0
                    for channel in converter.CHANNELS
                ),
                gamma=values["gamma"],
            )
            coverage = cmyk_module._auto_screen_coverage(
                tones,
                "edge_flow",
                0.5,
                0.52,
            )
            predicted = converter.predict_cmyk_rgb(coverage)
            return float(np.sqrt(np.mean((predicted - source) ** 2)))

        baseline_error = predicted_error(baseline)
        chosen_error = predicted_error(chosen)
        self.assertLess(chosen_error, baseline_error)
        self.assertAlmostEqual(
            chosen["predicted_rgb_error"],
            round(chosen_error * 255.0, 1),
            places=1,
        )

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


if __name__ == "__main__":
    unittest.main()
