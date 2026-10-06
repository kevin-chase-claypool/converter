"""The generator-tab shell: discovery, ordering, and failure isolation."""

import importlib.util
import os
import sys
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
        tabs = window.centralWidget()
        self.assertIsInstance(tabs, QTabWidget)
        self.assertEqual(tabs.tabText(0), "Convert")
        self.assertIs(tabs.widget(0), window.convert_root)
        self.assertGreaterEqual(tabs.count(), 1)

    def test_use_svg_rejects_missing_output(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.use_svg("definitely-not-a-real-file.svg")
        self.assertNotEqual(window.svg_path.text(), "definitely-not-a-real-file.svg")


if __name__ == "__main__":
    unittest.main()
