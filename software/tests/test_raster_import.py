"""A photo is a valid input: tone comes from its pixels, not from SVG shapes.

The converter's tone path already hatched the rendered image behind an SVG, so
importing a raster is a matter of skipping the SVG parse and feeding the image
straight to that path. These tests cover the parts that could quietly go wrong:
the fill-source decision, the auto fit that has no outlines to measure, and the
point count staying proportional to paper area over spacing squared.
"""

import importlib.util
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


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class RasterImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()
        folder = Path(tempfile.mkdtemp(prefix="raster-import-"))
        cls.photo = _write_test_photo(folder / "ramp.png")

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

    def _build(self, spacing_mm):
        self.window.fields["hatch_spacing_mm"].setText(str(spacing_mm))
        self.window.raw_cache_key = None
        self.window.raw_contours = None
        settings = self.window.fitted_settings_for_image(
            self.window.settings(), str(self.photo)
        )
        return settings, self.window.load_contours(str(self.photo), settings)

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
        first = self.window.fitted_settings_for_image(
            self.window.settings(), str(self.photo)
        ).scale
        stale = self.window.settings()
        stale = self.module.dataclasses.replace(stale, scale=0.05)
        second = self.window.fitted_settings_for_image(stale, str(self.photo)).scale
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


if __name__ == "__main__":
    unittest.main()
