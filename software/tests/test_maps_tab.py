"""The Maps tab: a vendored map tool that stays out of the kaleidoscope.

`piebro/plotting-maps` is a separate plotting function, so these tests pin
down two things only: the vendored page must not reach the network, and the
window must offer it as its own tab rather than folding it into the
kaleidoscope controls.
"""

import importlib.util
import os
import shutil
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


ROOT = Path(__file__).resolve().parents[1]
PLOTTING_MAPS_PAGE = ROOT / "plotting_maps" / "index.html"


def _load_app_module():
    path = ROOT / "qt_kaleidoscope.pyw"
    spec = importlib.util.spec_from_file_location("qt_kaleidoscope_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _temp_settings(test):
    folder = tempfile.mkdtemp(prefix="kaleido-maps-")
    test.addCleanup(shutil.rmtree, folder, ignore_errors=True)
    return str(Path(folder) / "settings.json")


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class MapsTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()

    def test_vendored_page_is_offline(self):
        text = PLOTTING_MAPS_PAGE.read_text(encoding="utf-8")
        self.assertIn('src="vendor/proj4.js"', text)
        self.assertIn('src="vendor/d3.v7.min.js"', text)
        self.assertNotIn("cdnjs.cloudflare.com", text)
        self.assertNotIn("plausible.io", text)
        self.assertNotIn("d3js.org/d3", text)

    def test_window_offers_a_separate_maps_tab(self):
        window = self.module.KaleidoscopeWindow(settings_file=_temp_settings(self))
        try:
            labels = [window.tabs.tabText(i) for i in range(window.tabs.count())]
            self.assertEqual(["Kaleidoscope", "Maps"], labels)
            self.assertIs(window.tabs.widget(1), window.maps_tab)
            self.assertIs(window.tabs.widget(0), window.tabs.currentWidget())
        finally:
            window.close()

    def test_maps_tab_defers_the_web_view(self):
        window = self.module.KaleidoscopeWindow(settings_file=_temp_settings(self))
        try:
            # Nothing web-engine shaped is built until the operator opens the
            # tab, so the kaleidoscope still starts quickly without WebEngine.
            self.assertIsNone(window.maps_tab._view)
        finally:
            window.close()


if __name__ == "__main__":
    unittest.main()
