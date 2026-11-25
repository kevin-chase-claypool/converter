"""Plotterfun tab: vendored assets, metadata, and the missing-WebEngine path."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.request import urlopen


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs import _plotterfun_web, plotterfun_extended_tab, plotterfun_tab


try:
    from PySide6.QtWidgets import QApplication, QMessageBox

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


class FakeHost:
    def __init__(self):
        self.adopted = []
        self.statuses = []

    def adopt_artwork(self, path):
        self.adopted.append(path)

    def generator_status(self, message):
        self.statuses.append(message)


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

    def test_extended_assets_are_complete_and_pinned(self):
        vendor = plotterfun_extended_tab.VENDOR_PAGE.parent
        self.assertTrue((vendor / "index.html").exists())
        self.assertTrue((vendor / "assets").is_dir())
        self.assertTrue(
            list((vendor / "assets").glob("flowfield-*.js"))
        )
        self.assertFalse(list((vendor / "assets").glob("*-*.wasm")))
        self.assertFalse(
            list((vendor / "assets").glob("transformers*.js"))
        )
        bundle_bytes = sum(
            path.stat().st_size
            for path in vendor.rglob("*")
            if path.is_file()
        )
        self.assertLess(bundle_bytes, 6_000_000)
        license_text = (vendor / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", license_text)
        notice = (
            Path(__file__).resolve().parents[1]
            / "generator_tabs"
            / "plotterfun_extended_NOTICE.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "00bf56dd872db8797486e021c26345929463e985",
            notice,
        )
        self.assertEqual(
            plotterfun_extended_tab.TITLE,
            "Plotterfun Extended",
        )


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class PlotterfunFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_missing_webengine_disables_the_export_button(self):
        original = _plotterfun_web.HAVE_WEBENGINE
        _plotterfun_web.HAVE_WEBENGINE = False
        try:
            tab = plotterfun_tab.create_tab(FakeHost())
            self.addCleanup(tab.deleteLater)
            self.assertFalse(tab.export_button.isEnabled())
            with self.assertRaises(ValueError):
                tab.build_svg()
            extended = plotterfun_extended_tab.create_tab(FakeHost())
            self.addCleanup(extended.deleteLater)
            self.assertFalse(extended.export_button.isEnabled())
            self.assertFalse(extended.use_current_button.isEnabled())
            with self.assertRaises(ValueError):
                extended.build_svg()
        finally:
            _plotterfun_web.HAVE_WEBENGINE = original

    def test_extended_export_and_current_artwork_status(self):
        original = _plotterfun_web.HAVE_WEBENGINE
        _plotterfun_web.HAVE_WEBENGINE = False
        host = FakeHost()
        try:
            tab = plotterfun_extended_tab.create_tab(host)
            self.addCleanup(tab.deleteLater)
            tab._svg_captured(
                '<svg xmlns="http://www.w3.org/2000/svg" '
                'width="10" height="10"></svg>'
            )
            tab._report_current_artwork(True)
        finally:
            _plotterfun_web.HAVE_WEBENGINE = original

        self.assertEqual(len(host.adopted), 1)
        self.assertTrue(Path(host.adopted[0]).exists())
        self.assertIn("loaded the current artwork", host.statuses[-1])

    def test_empty_export_reports_instead_of_silently_failing(self):
        original = _plotterfun_web.HAVE_WEBENGINE
        _plotterfun_web.HAVE_WEBENGINE = False
        try:
            tab = plotterfun_extended_tab.create_tab(FakeHost())
            self.addCleanup(tab.deleteLater)
            with mock.patch.object(QMessageBox, "warning") as warning:
                tab._svg_captured("")
        finally:
            _plotterfun_web.HAVE_WEBENGINE = original
        warning.assert_called_once()


class PlotterfunLocalServerTests(unittest.TestCase):
    def test_server_serves_extended_page_and_current_artwork(self):
        with tempfile.TemporaryDirectory(prefix="plotterfun-http-") as folder:
            image = Path(folder) / "source.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
            expected = image.read_bytes()
            server = _plotterfun_web._LocalStaticServer(
                plotterfun_extended_tab.VENDOR_PAGE.parent,
                artwork_path_getter=lambda: image,
            )
            self.addCleanup(server.close)

            with urlopen(server.url, timeout=5) as response:
                page = response.read().decode("utf-8")
            with urlopen(
                server.url.replace("index.html", "current-artwork"),
                timeout=5,
            ) as response:
                payload = response.read()

        self.assertIn("Plotterfun Extended", page)
        self.assertEqual(payload, expected)
