"""Image-tone fill spacing is millimetres on paper, not SVG user units.

The tone path rasterises in SVG user units and `apply_geometry_settings` scales
the result by `settings.scale` afterwards, so the mm-to-user-unit crossing has
to happen once, at the top of `raster_shade_contours`. On a 1000-unit artwork
the old unconverted path generated a lattice about five times too dense and
then shrank it: seconds of generation and hundreds of thousands of points for a
4 mm fill, which is what made a gradient preview look hung.
"""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover - the app needs Qt, the core does not
    HAVE_QT = False


# 1000 x 700 user units with a gradient across most of it: the sizing an
# exported design usually arrives in, and the case where user units are not
# millimetres.
GRADIENT_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="700" '
    'viewBox="0 0 1000 700">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0">'
    '<stop offset="0" stop-color="#000000"/>'
    '<stop offset="1" stop-color="#ffffff"/></linearGradient></defs>'
    '<rect x="40" y="40" width="920" height="620" fill="url(#g)"/></svg>'
)


def _load_app_module():
    path = Path(__file__).resolve().parents[1] / "qt_svg_to_gcode.pyw"
    spec = importlib.util.spec_from_file_location("qt_svg_to_gcode_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class ToneFillScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()
        folder = tempfile.mkdtemp(prefix="tone-fill-scale-")
        cls.path = str(Path(folder) / "big-gradient.svg")
        Path(cls.path).write_text(GRADIENT_SVG, encoding="utf-8")

    def setUp(self):
        self.window = self.module.MainWindow()
        combo = self.window.fields["hatch_pattern"]
        combo.setCurrentIndex(combo.findData("sine_gradient"))
        self.window.update_pattern_settings()
        fit = self.window.fields["fit_mode"]
        fit.setCurrentIndex(fit.findData("manual"))
        self.window.fields["wave_size_mm"].setText("0")
        self.window.fields["hatch_angle_deg"].setText("0")

    def _build(self, spacing_mm, scale, connect_rows=False):
        self.window.sine_rows_connected.setChecked(connect_rows)
        self.window.fields["hatch_spacing_mm"].setText(str(spacing_mm))
        self.window.fields["scale"].setText(str(scale))
        settings = self.window.settings()
        self.assertEqual(settings.fill_source, "auto")
        return self.window.raster_shade_contours(self.path, settings)

    def test_rows_land_on_the_requested_paper_spacing(self):
        scale = 0.5
        contours = self._build(4.0, scale)
        self.assertGreater(len(contours), 5)
        baselines = sorted(
            sum(point[1] for point in contour) / len(contour) for contour in contours
        )
        pitches = [b - a for a, b in zip(baselines, baselines[1:])]
        median_pitch_mm = sorted(pitches)[len(pitches) // 2] * scale
        self.assertAlmostEqual(
            median_pitch_mm,
            4.0,
            delta=0.05,
            msg="4 mm on paper must be 8 user units at scale 0.5, not 4",
        )

    def test_point_count_follows_the_paper_spacing_not_the_view_box(self):
        first = sum(len(contour) for contour in self._build(4.0, 0.5))
        second = sum(len(contour) for contour in self._build(4.0, 1.0))
        self.assertGreater(first, 0)
        self.assertGreater(second, 0)
        # Halving the scale doubles the user-unit spacing, so the row count and
        # the samples per row both halve: about a quarter of the points.
        self.assertLess(first, second * 0.4)
        self.assertGreater(first, second * 0.2)

    def test_a_denser_request_still_scales_with_the_square(self):
        wide = sum(len(contour) for contour in self._build(6.0, 0.4))
        tight = sum(len(contour) for contour in self._build(3.0, 0.4))
        ratio = tight / max(wide, 1)
        self.assertGreater(ratio, 3.0, "halving the spacing roughly quarters the points")
        self.assertLess(ratio, 5.0)


if __name__ == "__main__":
    unittest.main()
