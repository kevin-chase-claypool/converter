"""Plotterfun tab: vendored assets, metadata, and the missing-WebEngine path."""

import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs import plotterfun_tab


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


class FakeHost:
    def __init__(self):
        self.adopted = []

    def adopt_artwork(self, path):
        self.adopted.append(path)


class PlotterfunVendorTests(unittest.TestCase):
    def test_vendored_assets_and_license(self):
        vendor = plotterfun_tab.VENDOR_PAGE.parent
        self.assertTrue((vendor / "main.htm").exists())
        self.assertTrue((vendor / "helpers.js").exists())
        self.assertTrue((vendor / "peano.js").exists())
        self.assertTrue((vendor / "woven.js").exists())
        license_text = (vendor / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT", license_text)
        self.assertEqual(plotterfun_tab.TITLE, "Plotterfun")
        self.assertEqual(plotterfun_tab.ORDER, 130)


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class PlotterfunFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_missing_webengine_disables_the_export_button(self):
        original = plotterfun_tab.HAVE_WEBENGINE
        plotterfun_tab.HAVE_WEBENGINE = False
        try:
            tab = plotterfun_tab.create_tab(FakeHost())
            self.addCleanup(tab.deleteLater)
            self.assertFalse(tab.export_button.isEnabled())
            with self.assertRaises(ValueError):
                tab.build_svg()
        finally:
            plotterfun_tab.HAVE_WEBENGINE = original
