"""Preview zoom and pan: the view transform used by the kaleidoscope window.

The preview draws in design millimetres and lets the operator zoom and pan the
camera the way the main converter's preview does. These tests pin the transform
down without needing a visible window: screen and design coordinates must round
trip, a wheel zoom must keep the point under the cursor, panning must follow the
drag, and an image drag must shrink in millimetres as the view is zoomed in.
"""

import importlib.util
import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from PySide6.QtCore import QPointF
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover - the app needs Qt, the core does not
    HAVE_QT = False


def _load_app_module():
    path = Path(__file__).resolve().parents[1] / "qt_kaleidoscope.pyw"
    spec = importlib.util.spec_from_file_location("qt_kaleidoscope_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class PreviewViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()

    def setUp(self):
        self.preview = self.module.DesignPreview()
        self.preview.resize(600, 600)

    def test_screen_and_design_coordinates_round_trip(self):
        for zoom, pan in ((1.0, (0.0, 0.0)), (4.0, (30.0, -12.0)), (0.35, (-8.0, 5.0))):
            self.preview.zoom = zoom
            self.preview.pan = pan
            for point in ((0.0, 0.0), (37.0, -64.0), (-150.0, 120.0)):
                back = self.preview.to_design(self.preview.to_screen(point))
                self.assertAlmostEqual(point[0], back[0], places=6)
                self.assertAlmostEqual(point[1], back[1], places=6)

    def test_zoom_keeps_the_design_point_under_the_cursor(self):
        anchor = QPointF(140.0, 420.0)
        before = self.preview.to_design(anchor)
        self.preview.set_zoom(4.0, anchor)
        after = self.preview.to_design(anchor)
        self.assertAlmostEqual(before[0], after[0], places=6)
        self.assertAlmostEqual(before[1], after[1], places=6)

    def test_zoom_is_clamped_to_the_converter_range(self):
        self.preview.set_zoom(1000.0)
        self.assertLessEqual(self.preview.zoom, 20.0)
        self.preview.set_zoom(0.0001)
        self.assertGreaterEqual(self.preview.zoom, 0.1)

    def test_image_drag_shrinks_in_millimetres_as_the_view_zooms(self):
        self.preview.zoom = 1.0
        plain = self.preview.screen_delta_to_mm(100.0, 50.0)
        self.preview.zoom = 4.0
        zoomed = self.preview.screen_delta_to_mm(100.0, 50.0)
        self.assertAlmostEqual(zoomed[0] * 4.0, plain[0], places=6)
        self.assertAlmostEqual(zoomed[1] * 4.0, plain[1], places=6)
        self.assertLess(plain[1], 0.0, "screen down is negative design y")

    def test_pan_follows_the_drag(self):
        self.preview.zoom = 2.0
        before = self.preview.to_screen((0.0, 0.0))
        self.preview.pan_by(40.0, -25.0)
        after = self.preview.to_screen((0.0, 0.0))
        self.assertAlmostEqual(after.x() - before.x(), 40.0, places=6)
        self.assertAlmostEqual(after.y() - before.y(), -25.0, places=6)

    def test_reset_view_returns_to_the_whole_bed(self):
        self.preview.set_zoom(6.0)
        self.preview.pan_by(120.0, 60.0)
        self.preview.reset_view()
        self.assertEqual(self.preview.zoom, 1.0)
        self.assertEqual(self.preview.pan, (0.0, 0.0))

    def test_view_changes_are_announced(self):
        seen = []
        self.preview.viewChanged.connect(seen.append)
        self.preview.zoom_in()
        self.preview.reset_view()
        self.assertGreaterEqual(len(seen), 2)
        self.assertAlmostEqual(seen[-1], 1.0)


if __name__ == "__main__":
    unittest.main()
