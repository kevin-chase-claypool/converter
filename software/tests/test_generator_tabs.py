"""The generator-tab shell: discovery, ordering, and failure isolation."""

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication, QTabBar

    HAVE_QT = True
except Exception:  # pragma: no cover - the app needs Qt, the core does not
    HAVE_QT = False


def _load_app_module():
    path = Path(__file__).resolve().parents[1] / "qt_svg_to_gcode.pyw"
    spec = importlib.util.spec_from_file_location("qt_svg_to_gcode_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class GeneratorTabShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()

    def test_convert_is_the_first_tab(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        self.assertIsInstance(window.tab_bar, QTabBar)
        self.assertEqual(window.tab_bar.tabText(0), "Convert")
        self.assertIs(window.stack.widget(0), window.convert_root)
        self.assertGreaterEqual(window.tab_bar.count(), 1)

    def test_tab_bar_sits_above_the_import_row(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.resize(1500, 950)
        window.show()
        self.app.processEvents()
        bar_y = window.tab_bar.mapTo(window, QPoint(0, 0)).y()
        import_y = window.svg_path.mapTo(window, QPoint(0, 0)).y()
        self.assertLess(bar_y, import_y)

    def test_generator_tab_order(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        titles = [
            window.tab_bar.tabText(index)
            for index in range(window.tab_bar.count())
        ]
        self.assertEqual(
            titles,
            [
                "Convert",
                "Flow Field",
                "Line Draw",
                "3D Wireframe",
                "Harmonograph",
                "Snowflake",
                "Truchet",
            ],
        )

    def test_settings_pane_has_no_dead_strip(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.resize(1500, 950)
        window.show()
        self.app.processEvents()
        self.assertLessEqual(
            window.stack.width() - window.sidebar_scroll.width(), 4
        )

    def test_generator_controls_fill_the_settings_pane(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.resize(630, 1000)
        window.show()
        window.tab_bar.setCurrentIndex(1)
        self.app.processEvents()
        tab = window.stack.currentWidget()
        self.assertGreaterEqual(tab.width(), 280)
        # The 6 px margins on each side are the only width the controls leave.
        self.assertLessEqual(tab.width() - tab.controls_scroll.width(), 16)
        self.assertGreaterEqual(
            tab.status.y(), tab.controls_scroll.y() + tab.controls_scroll.height()
        )

    def test_every_generator_tab_has_an_artwork_scale(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        for index in range(window.tab_bar.count()):
            window.tab_bar.setCurrentIndex(index)
            page = window.stack.currentWidget()
            if page is window.convert_root:
                continue
            label = window.tab_bar.tabText(index)
            self.assertTrue(hasattr(page, "scale_pct"), label)
            self.assertEqual(page.scale_pct.value(), 100, label)

    def test_generator_sources_plot_at_manual_1to1(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.tab_bar.setCurrentIndex(1)
        flow = window.stack.currentWidget()
        generator_settings = window.settings_for_source(flow)
        self.assertEqual(generator_settings.fit_mode, "manual")
        self.assertEqual(generator_settings.scale, 1.0)
        convert_settings = window.settings_for_source(window.convert_root)
        self.assertEqual(convert_settings.fit_mode, window.settings().fit_mode)

    def test_artwork_scale_survives_the_generator_pipeline(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.tab_bar.setCurrentIndex(1)
        flow = window.stack.currentWidget()
        flow.page_w.setValue(120)
        flow.page_h.setValue(120)
        flow.spacing.setValue(8.0)
        flow.step.setValue(2.0)
        flow.max_steps.setValue(40)
        flow.scale.setValue(20)
        flow.margin.setValue(4)

        def drawn_width():
            path, _tab = window.resolve_active_source()
            contours = window.load_contours(
                path, window.settings_for_source(flow)
            )
            xs = [point[0] for contour in contours for point in contour]
            return max(xs) - min(xs)

        full = drawn_width()
        flow.scale_pct.setValue(50)
        half = drawn_width()
        self.assertAlmostEqual(half / full, 0.5, delta=0.05)

    def test_import_export_and_preview_stay_outside_the_tabs(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        for widget in (
            window.svg_path,
            window.gcode_path,
            window.preview_button,
            window.save_button,
            window.gl_preview,
            window.slider,
        ):
            self.assertFalse(
                window.stack.isAncestorOf(widget),
                f"{widget} is hidden with the tab it lives in",
            )

    def test_preview_and_cancel_live_in_the_preview_panel(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        self.assertTrue(window.preview_panel.isAncestorOf(window.preview_button))
        self.assertTrue(
            window.preview_panel.isAncestorOf(window.cancel_preview_button)
        )
        self.assertFalse(window.preview_panel.isAncestorOf(window.save_button))

    def test_command_list_is_removed_and_preview_fills_the_rest(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        self.assertFalse(hasattr(window, "command_list"))
        self.assertEqual(window.main_split.count(), 2)
        self.assertIs(window.main_split.widget(0), window.stack)
        self.assertIs(window.main_split.widget(1), window.preview_panel)
        window.resize(1500, 950)
        window.show()
        self.app.processEvents()
        tabs_width, preview_width = window.main_split.sizes()
        self.assertLessEqual(tabs_width, 420)
        self.assertGreater(preview_width, tabs_width * 2)

    def test_resolve_active_source_returns_the_convert_artwork(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        handle = tempfile.NamedTemporaryFile(
            suffix=".svg", delete=False, mode="w", encoding="utf-8"
        )
        handle.write('<svg xmlns="http://www.w3.org/2000/svg"/>')
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        window.svg_path.setText(handle.name)
        path, tab = window.resolve_active_source()
        self.assertEqual(path, handle.name)
        self.assertIs(tab, window.convert_root)

    def test_switching_tabs_marks_the_preview_stale(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.moves = [{"gcode": "G1"}]
        window.preview_tab = window.convert_root
        window.tab_bar.setCurrentIndex(1)
        self.assertTrue(window.tab_preview_stale)
        self.assertFalse(window.stale_warning.isHidden())
        window.tab_bar.setCurrentIndex(0)
        self.assertFalse(window.tab_preview_stale)
        self.assertTrue(window.stale_warning.isHidden())

    def test_generator_svg_runs_through_the_converter_pipeline(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.tab_bar.setCurrentIndex(1)
        flow = window.stack.currentWidget()
        flow.page_w.setValue(60)
        flow.page_h.setValue(60)
        flow.spacing.setValue(8.0)
        flow.step.setValue(2.0)
        flow.max_steps.setValue(40)
        flow.scale.setValue(20)
        flow.margin.setValue(4)
        path, tab = window.resolve_active_source()
        self.assertIs(tab, flow)
        contours = window.load_contours(path, window.settings())
        self.assertGreater(len(contours), 0)


if __name__ == "__main__":
    unittest.main()
