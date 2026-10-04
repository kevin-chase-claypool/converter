"""A photo is a valid input: tone comes from its pixels, not from SVG shapes.

The converter's tone path already hatched the rendered image behind an SVG, so
importing a raster is a matter of skipping the SVG parse and feeding the image
straight to that path. These tests cover the parts that could quietly go wrong:
the fill-source decision, the auto fit that has no outlines to measure, and the
point count staying proportional to paper area over spacing squared.
"""

import importlib.util
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter

try:
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover - the app needs Qt, the core does not
    HAVE_QT = False


def _write_test_photo(path, width=240, height=160):
    """A grey ramp across the image with a white band along the top."""
    image = QImage(width, height, QImage.Format_ARGB32)
    for y in range(height):
        for x in range(width):
            if y < height // 5:
                image.setPixelColor(x, y, QColor(255, 255, 255))
            else:
                value = int(255 * (1.0 - x / max(width - 1, 1)))
                image.setPixelColor(x, y, QColor(value, value, value))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError("could not write the test image")
    return path


def _write_large_photo(path, width=1200, height=900):
    """A bed-filling-size photo: a grey field with lighter and darker zones.

    Fast to build (no per-pixel Python loop) so the image-tone path can be
    exercised at the paper scale of a real imported photo.
    """
    from PySide6.QtCore import QRect
    from PySide6.QtGui import QPainter

    image = QImage(width, height, QImage.Format_ARGB32)
    image.fill(QColor(140, 140, 140))
    painter = QPainter(image)
    painter.fillRect(QRect(0, 0, width, height // 5), QColor(255, 255, 255))
    painter.fillRect(
        QRect(width // 4, height // 2, width // 2, height // 3), QColor(40, 40, 40)
    )
    painter.end()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(path)):
        raise RuntimeError("could not write the test image")
    return path


def _load_app_module():
    path = Path(__file__).resolve().parents[1] / "qt_svg_to_gcode.pyw"
    spec = importlib.util.spec_from_file_location("qt_svg_to_gcode_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RasterDetectionTests(unittest.TestCase):
    def test_raster_extensions_are_recognised(self):
        for name in ("photo.jpg", "Photo.JPEG", "scan.png", "art.webp", "x.tif"):
            self.assertTrue(converter.is_raster_image(name), name)
        for name in ("drawing.svg", "notes.txt", "noextension"):
            self.assertFalse(converter.is_raster_image(name), name)

    def test_a_raster_is_always_hatched_from_tone(self):
        settings = converter.Settings(fill_source="shapes")
        self.assertEqual(
            converter.resolve_fill_source(settings, "photo.jpg"),
            "tone",
            "a photo has no vector regions, so the shapes source cannot apply",
        )
        self.assertEqual(
            converter.svg_fill_sources("photo.jpg"),
            {"filled": 0, "outline": 0, "image": 1, "gradient": 0},
        )

    def test_a_traced_bitmap_reports_many_flat_shapes(self):
        """A bitmap trace is hundreds of filled paths and no tone source.

        It cannot carry a gradient, and it is the input that makes the shape
        hatch path slow, so the app has to be able to recognise it.
        """
        folder = Path(tempfile.mkdtemp(prefix="traced-"))
        path = folder / "trace.svg"
        paths = "".join(
            f'<rect x="{index % 10}" y="{index // 10}" width="0.9" height="0.9" fill="#000000"/>'
            for index in range(60)
        )
        path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6">'
            + paths
            + "</svg>",
            encoding="utf-8",
        )
        sources = converter.svg_fill_sources(path)
        self.assertEqual(sources["filled"], 60)
        self.assertEqual(sources["image"], 0)
        self.assertEqual(sources["gradient"], 0)
        self.assertEqual(
            converter.resolve_fill_source(converter.Settings(), str(path)), "shapes"
        )


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class RasterImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()
        folder = Path(tempfile.mkdtemp(prefix="raster-import-"))
        cls.photo = _write_test_photo(folder / "ramp.png")
        cls.large_photo = _write_large_photo(folder / "large.png")

    def setUp(self):
        self.window = self.module.MainWindow()
        combo = self.window.fields["hatch_pattern"]
        combo.setCurrentIndex(combo.findData("sine_gradient"))
        self.window.update_pattern_settings()
        fit = self.window.fields["fit_mode"]
        fit.setCurrentIndex(fit.findData("fill"))
        self.window.fields["fill_source"].setCurrentIndex(
            self.window.fields["fill_source"].findData("auto")
        )
        self.window.fields["wave_size_mm"].setText("0")
        self.window.fields["hatch_angle_deg"].setText("0")

    def _build(self, spacing_mm, photo=None):
        photo = photo or self.photo
        self.window.fields["hatch_spacing_mm"].setText(str(spacing_mm))
        self.window.raw_cache_key = None
        self.window.raw_contours = None
        settings = self.window.fitted_settings_for_artwork_bounds(
            self.window.settings(), str(photo)
        )
        return settings, self.window.load_contours(str(photo), settings)

    def test_a_photo_fills_from_its_pixels(self):
        settings, contours = self._build(4.0)
        self.assertTrue(contours, "a photo must produce fill geometry")
        reach = float(settings.machine_reach_radius_mm)
        xs = [point[0] for contour in contours for point in contour]
        ys = [point[1] for contour in contours for point in contour]
        self.assertGreater(max(xs) - min(xs), 0.0)
        # The auto fit puts the longer side on the drawable diameter, so the
        # image spans the bed rather than a few millimetres of it.
        self.assertGreater(max(ys) - min(ys), reach)
        self.assertLessEqual(max(ys) - min(ys), 2.0 * reach + 1e-6)

    def test_the_fit_does_not_depend_on_the_scale_left_in_the_field(self):
        first = self.window.fitted_settings_for_artwork_bounds(
            self.window.settings(), str(self.photo)
        ).scale
        stale = self.window.settings()
        stale = self.module.dataclasses.replace(stale, scale=0.05)
        second = self.window.fitted_settings_for_artwork_bounds(stale, str(self.photo)).scale
        self.assertAlmostEqual(first, second, places=6)

    def test_points_follow_paper_area_over_spacing_squared(self):
        wide_settings, wide = self._build(4.0)
        tight_settings, tight = self._build(2.0)
        wide_points = sum(len(contour) for contour in wide)
        tight_points = sum(len(contour) for contour in tight)
        self.assertGreater(wide_points, 0)
        ratio = tight_points / wide_points
        self.assertGreater(ratio, 3.0)
        self.assertLess(ratio, 5.0)
        reach = float(wide_settings.machine_reach_radius_mm)
        # 12 samples per mm^2 of paper at a 1 mm pitch is the generator's rate:
        # the whole drawable circle at 2 mm is the worst case the machine allows.
        ceiling = 12.0 * 3.14159 * reach * reach / 4.0
        self.assertLess(tight_points, ceiling * 1.3)

    def test_photo_shading_patterns_build_from_pixels(self):
        """The dot-family photo styles run through the real image-tone path."""
        for value in ("stipple", "halftone", "tsp"):
            with self.subTest(pattern=value):
                combo = self.window.fields["hatch_pattern"]
                combo.setCurrentIndex(combo.findData(value))
                self.window.update_pattern_settings()
                self.window.fields["dot_spacing_mm"].setText("0")
                _settings, contours = self._build(4.0)
                points = [point for contour in contours for point in contour]
                self.assertGreater(len(points), 0, value)

    def test_terrain_contours_follow_tone(self):
        """`terrain` crowds its contours into the dark half of the ramp."""
        combo = self.window.fields["hatch_pattern"]
        combo.setCurrentIndex(combo.findData("terrain"))
        self.window.update_pattern_settings()
        self.window.fields["terrain_size_mm"].setText("0")
        self.window.fields["shade_levels"].setText("4")
        settings, contours = self._build(4.0)
        self.assertTrue(contours)
        xs = [point[0] for contour in contours for point in contour]
        middle = 0.5 * (min(xs) + max(xs))

        def length(predicate):
            return sum(
                math.hypot(b[0] - a[0], b[1] - a[1])
                for contour in contours
                for a, b in zip(contour, contour[1:])
                if predicate(0.5 * (a[0] + b[0]))
            )

        dark = length(lambda x: x >= middle)
        light = length(lambda x: x < middle)
        self.assertGreater(dark, 0.0)
        # The test ramp runs white (left) to black (right), so the darker half
        # must carry visibly more contour length.
        self.assertGreater(dark, light * 1.5)

    def test_photo_shading_patterns_survive_a_bed_filling_photo(self):
        """Regression: a real-scale photo dropped every stipple dot.

        ``load_contours`` scales the fill to paper and removes sub-millimetre
        fragments, so the marks must be sized on paper, not as a fraction of
        the fill spacing.
        """
        dot_spans = None
        for value in ("stipple", "halftone", "tsp"):
            with self.subTest(pattern=value):
                combo = self.window.fields["hatch_pattern"]
                combo.setCurrentIndex(combo.findData(value))
                self.window.update_pattern_settings()
                self.window.fields["dot_spacing_mm"].setText("0")
                settings, contours = self._build(4.0, photo=self.large_photo)
                self.assertTrue(contours, value)
                self.assertLess(settings.scale, 0.35, "the test photo must fit the bed")
                if value == "stipple":
                    dot_spans = [
                        max(x for x, _ in contour) - min(x for x, _ in contour)
                        for contour in contours
                    ]
        self.assertGreater(
            min(dot_spans), 0.3, "every stipple dot keeps a paper size"
        )


if __name__ == "__main__":
    unittest.main()
