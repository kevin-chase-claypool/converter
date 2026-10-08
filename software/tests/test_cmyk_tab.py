"""CMYK separation, screening, layer SVGs, and per-ink cost analysis."""

import json
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


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

    def test_auto_photo_settings_fit_dark_and_bright_images(self):
        from PIL import Image

        folder = tempfile.mkdtemp(prefix="cmyk-auto-")
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        dark_path = str(Path(folder) / "dark.png")
        bright_path = str(Path(folder) / "bright.png")
        Image.new("RGB", (64, 64), (20, 20, 25)).save(dark_path)
        Image.new("RGB", (64, 64), (180, 180, 180)).save(bright_path)
        dark = converter.auto_photo_settings(dark_path)
        bright = converter.auto_photo_settings(bright_path)
        self.assertTrue(dark["auto_levels"])
        self.assertGreaterEqual(dark["gamma"], 1.3)
        self.assertGreaterEqual(dark["brightness"], 140)
        self.assertEqual(bright["brightness"], 100)
        self.assertEqual(bright["gamma"], 1.0)
        self.assertLessEqual(bright["contrast"], dark["contrast"])

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
            dark, self.geometry(), style="waves", spacing_mm=4.0
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
        for style in ("halftone", "stipple", "lines", "rectilinear", "crosshatch", "waves", "gyroid", "tsp", "contours"):
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
        self.assertAlmostEqual(tab.gamma.value(), 1.40, places=2)
        self.assertAlmostEqual(tab.dot_size.value(), 100.0, places=3)
        self.assertEqual(tab.max_marks.value(), 40000)
        self.assertEqual(tab.resolution.value(), 10000)
        self.assertAlmostEqual(tab.scale_pct.value(), 280.0, places=3)
        self.assertAlmostEqual(tab.weight_c.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_m.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_y.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_k.value(), 100.0, places=3)

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
        tab.auto_button.click()
        values = converter.auto_photo_settings(self.image_path)
        self.assertEqual(tab.saturation.value(), values["saturation"])
        self.assertEqual(tab.contrast.value(), values["contrast"])
        self.assertEqual(tab.brightness.value(), values["brightness"])
        self.assertEqual(tab.gcr.value(), values["gcr"])
        self.assertAlmostEqual(tab.gamma.value(), values["gamma"], places=2)
        self.assertTrue(tab.auto_levels.isChecked())
        self.assertIn("Auto:", tab.status.text())

    def test_max_marks_is_not_capped_at_40000(self):
        tab = self.make_tab()
        tab.max_marks.setValue(80000)
        self.assertEqual(tab.max_marks.value(), 80000)

    def test_planning_is_background_not_a_button(self):
        tab = self.make_tab()
        self.assertFalse(hasattr(tab, "analyze_button"))
        calls = []
        tab.start_analysis = lambda: calls.append("plan")
        tab.on_preview_finished()
        self.assertEqual(calls, ["plan"])

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
        self._folder = tempfile.mkdtemp(prefix="cmyk-save-")

    def artwork_path(self):
        return self._artwork

    def generator_status(self, message):
        self.status.append(message)

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
