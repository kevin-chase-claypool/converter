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
    from PySide6.QtWidgets import QApplication, QTabWidget

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
        tabs = window.tabs
        self.assertIsInstance(tabs, QTabWidget)
        self.assertEqual(tabs.tabText(0), "Convert")
        self.assertIs(tabs.widget(0), window.convert_root)
        self.assertGreaterEqual(tabs.count(), 1)

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
                window.tabs.isAncestorOf(widget),
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
        window.tabs.setCurrentIndex(1)
        self.assertTrue(window.tab_preview_stale)
        self.assertFalse(window.stale_warning.isHidden())
        window.tabs.setCurrentIndex(0)
        self.assertFalse(window.tab_preview_stale)
        self.assertTrue(window.stale_warning.isHidden())

    def test_generator_svg_runs_through_the_converter_pipeline(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.tabs.setCurrentIndex(1)
        flow = window.tabs.currentWidget()
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
