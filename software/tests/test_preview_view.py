"""Preview zoom and pan: the view transform used by the kaleidoscope window.

The preview draws in design millimetres and lets the operator zoom and pan the
camera the way the main converter's preview does. These tests pin the transform
down without needing a visible window: screen and design coordinates must round
trip, a wheel zoom must keep the point under the cursor, panning must follow the
drag, and an image drag must shrink in millimetres as the view is zoomed in.
"""

import importlib.util
import math
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


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class SourceSizeTests(unittest.TestCase):
    """The source size is a free number; the fit radius bounds the plot."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()

    def test_source_size_has_no_practical_cap(self):
        window = self.module.KaleidoscopeWindow()
        self.assertGreaterEqual(window.source_size.maximum(), 100000.0)

    def test_huge_source_size_is_fitted_to_the_bound(self):
        window = self.module.KaleidoscopeWindow()
        window.seed.setValue(6)
        window.intricacy.setValue(3)
        window.random_mode.setChecked(True)
        window.source_size.setValue(250000.0)
        window.rebuild(refit=True)
        self.assertTrue(window.design)
        radius = max(
            math.hypot(x, y) for contour in window.design for x, y in contour
        )
        target = float(window.fit_radius.value())
        self.assertAlmostEqual(radius, target, delta=target * 0.01)


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class TypedNumberTests(unittest.TestCase):
    """Typed settings must survive seed, intricacy and division changes."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()

    def setUp(self):
        self.window = self.module.KaleidoscopeWindow()
        self.window.seed.setValue(5)
        self.window.intricacy.setValue(4)
        self.window.random_mode.setChecked(True)
        self.window.source_size.setValue(500.0)
        self.window.feed_rate.setValue(1234.0)
        self.window.tolerance.setValue(0.4)
        self.window.fit_radius.setValue(120.0)
        self.window.rebuild()

    def test_seed_change_keeps_the_typed_numbers(self):
        before = self.typed_values()
        old_seed = self.window.seed.value()
        self.window.roll_seed()
        self.assertNotEqual(self.window.seed.value(), old_seed, "the seed itself changes")
        self.assertEqual(self.typed_values(), before)
        self.assertAlmostEqual(
            self.design_radius(), 120.0, delta=1.2, msg="auto-fit still applies"
        )

    def test_intricacy_and_division_changes_keep_the_typed_numbers(self):
        before = self.typed_values()
        self.window.intricacy.setValue(7)
        self.window.divisions.setValue(9)
        self.assertEqual(self.typed_values(), before)
        self.assertAlmostEqual(self.design_radius(), 120.0, delta=1.2)

    def test_auto_fit_does_not_write_the_size_back(self):
        self.window.source_size.setValue(777.0)
        self.window.rebuild()
        self.assertEqual(self.window.source_size.value(), 777.0)
        self.assertNotAlmostEqual(self.window.fit_scale, 1.0, places=3)

    def test_fit_button_is_the_one_that_writes_the_size(self):
        self.window.source_size.setValue(777.0)
        self.window.fit_to_bounds()
        self.assertAlmostEqual(self.window.source_size.value(), 120.0, delta=1.2)
        self.assertAlmostEqual(self.window.fit_scale, 1.0, places=6)

    def typed_values(self):
        """The settings a seed/intricacy/division change must never rewrite."""
        window = self.window
        return {
            "source_size": window.source_size.value(),
            "feed_rate": window.feed_rate.value(),
            "theta_speed": window.theta_speed.value(),
            "tolerance": window.tolerance.value(),
            "fill_spacing": window.fill_spacing.value(),
            "threshold": window.threshold.value(),
            "trace_detail": window.trace_detail.value(),
            "bed_diameter": window.bed_diameter.value(),
            "bed_margin": window.bed_margin.value(),
            "reach_radius": window.reach_radius.value(),
            "fit_radius": window.fit_radius.value(),
        }

    def design_radius(self):
        return max(
            math.hypot(x, y) for contour in self.window.design for x, y in contour
        )


if __name__ == "__main__":
    unittest.main()
