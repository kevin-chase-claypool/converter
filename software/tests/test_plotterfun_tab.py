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

import converter_core as converter
from generator_tabs import (
    _plotterfun_simple,
    _plotterfun_web,
    plotterfun_extended_tab,
    plotterfun_tab,
)


try:
    from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


class FakeHost:
    def __init__(self):
        self.adopted = []
        self.statuses = []
        self.preview_panel = None
        self.main_split = None

    def adopt_artwork(self, path):
        self.adopted.append(path)

    def generator_status(self, message):
        self.statuses.append(message)

    def settings_for_source(self, _tab):
        return converter.Settings()


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

    def test_extended_simple_workflow_hides_full_page_until_advanced(self):
        original = _plotterfun_web.HAVE_WEBENGINE
        _plotterfun_web.HAVE_WEBENGINE = False
        try:
            tab = plotterfun_extended_tab.create_tab(FakeHost())
            self.addCleanup(tab.deleteLater)
            self.assertTrue(tab.simple_workflow)
            self.assertEqual(
                [tab.style_combo.itemData(index) for index in range(tab.style_combo.count())],
                [
                    "flowfield.js",
                    "contours.js",
                    "linedraw.js",
                    "stipple.js",
                    "crosshatch.js",
                    "halftone.js",
                    "squiggle.js",
                ],
            )
            self.assertIn("Create Y/M/C/K", tab.export_cmyk_button.text())
            self.assertEqual(
                tab.style_combo.currentData(),
                "flowfield.js",
            )
            self.assertTrue(tab.export_button.isHidden())
            tab.advanced_button.setEnabled(True)
            tab.advanced_button.click()
            self.assertTrue(tab._advanced_mode)
            self.assertFalse(tab.export_button.isHidden())
            self.assertEqual(
                tab.advanced_button.text(),
                "Hide advanced controls",
            )
        finally:
            _plotterfun_web.HAVE_WEBENGINE = original

    def test_simple_workflow_uses_full_workspace_and_restores_preview(self):
        original = _plotterfun_web.HAVE_WEBENGINE
        _plotterfun_web.HAVE_WEBENGINE = False

        class FakeSplit:
            def __init__(self):
                self.restored_sizes = None

            def sizes(self):
                return [920, 360]

            def setSizes(self, sizes):
                self.restored_sizes = list(sizes)

        try:
            host = FakeHost()
            host.preview_panel = QWidget()
            host.preview_panel.show()
            host.main_split = FakeSplit()
            tab = plotterfun_extended_tab.create_tab(host)
            self.addCleanup(tab.deleteLater)
            self.addCleanup(host.preview_panel.deleteLater)
            tab.show()
            self.app.processEvents()
            self.assertFalse(host.preview_panel.isVisible())

            tab.advanced_button.setChecked(True)
            self.app.processEvents()
            self.assertTrue(host.preview_panel.isVisible())
            self.assertEqual(host.main_split.restored_sizes, [920, 360])

            tab.hide()
            self.app.processEvents()
        finally:
            _plotterfun_web.HAVE_WEBENGINE = original

    def test_cancelled_cmyk_folder_does_not_capture_or_write(self):
        original = _plotterfun_web.HAVE_WEBENGINE
        _plotterfun_web.HAVE_WEBENGINE = False
        try:
            host = FakeHost()
            host.artwork_path = lambda: r"C:\art\portrait.png"
            tab = plotterfun_extended_tab.create_tab(host)
            self.addCleanup(tab.deleteLater)

            class FakePage:
                calls = []

                def runJavaScript(self, *args):
                    self.calls.append(args)

            class FakeView:
                def __init__(self):
                    self.pages = FakePage()

                def page(self):
                    return self.pages

            tab.view = FakeView()
            tab.export_cmyk_button.setEnabled(True)
            with mock.patch.object(
                _plotterfun_simple.QFileDialog,
                "getExistingDirectory",
                return_value="",
            ):
                tab.export_cmyk_gcode_set()
        finally:
            _plotterfun_web.HAVE_WEBENGINE = original
        self.assertIn("cancelled", tab.simple_status.text())
        self.assertEqual(tab.view.pages.calls, [])
        self.assertTrue(tab.export_cmyk_button.isEnabled())

    def test_cmyk_capture_writes_internal_svgs_and_starts_gcode_worker(self):
        original = _plotterfun_web.HAVE_WEBENGINE
        _plotterfun_web.HAVE_WEBENGINE = False
        try:
            host = FakeHost()
            tab = plotterfun_extended_tab.create_tab(host)
            self.addCleanup(tab.deleteLater)
            with tempfile.TemporaryDirectory(prefix="plotterfun-ui-") as folder:
                intermediate = Path(folder) / "internal-svg"
                tab._pending_cmyk_folder = Path(folder)
                tab._pending_cmyk_base = "portrait"
                tab._pending_cmyk_source = r"C:\art\portrait.png"
                tab._pending_cmyk_algorithm = "flowfield.js"
                tab._pending_cmyk_settings = converter.Settings()
                with (
                    mock.patch.object(
                        _plotterfun_simple.tempfile,
                        "mkdtemp",
                        return_value=str(intermediate),
                    ),
                    mock.patch.object(tab, "_start_gcode_worker") as start,
                ):
                    tab._cmyk_svg_captured(
                        '<svg xmlns="http://www.w3.org/2000/svg" width="8in" '
                        'height="6in" viewBox="0 0 800 600">'
                        '<g id="cyan"><path d="M0,0 L1,1"/></g>'
                        '<g id="magenta"><path d="M0,1 L1,0"/></g>'
                        '<g id="yellow"><path d="M10,10 L20,20"/></g>'
                        '<g id="black"><path d="M20,20 L30,30"/></g>'
                        "</svg>"
                    )
                start.assert_called_once()
                svg_export = start.call_args.args[0]
                names = sorted(
                    path.name for path in intermediate.glob("*.svg")
                )
                public_svgs = list(Path(folder).glob("portrait-*.svg"))
        finally:
            _plotterfun_web.HAVE_WEBENGINE = original
        self.assertEqual(
            names,
            [
                "portrait-01-yellow.svg",
                "portrait-02-magenta.svg",
                "portrait-03-cyan.svg",
                "portrait-04-black.svg",
            ],
        )
        self.assertEqual(svg_export.layers[0].ink, "yellow")
        self.assertEqual(public_svgs, [])


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
