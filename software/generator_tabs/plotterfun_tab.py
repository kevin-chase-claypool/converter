"""Plotterfun tab: the vendored mitxela/plotterfun web app.

Plotterfun is a 22-algorithm image-to-vector web app (MIT). Porting it to
Python would duplicate the existing fills and lose its interactive workflow,
so the upstream static site is vendored under ``software/plotterfun_vendor``
and embedded with QtWebEngine, following the Kaleidoscope Maps-tab pattern.
Interaction (image loading, algorithm, sliders, live SVG) happens inside the
page; **Export SVG to plot** captures the current ``<svg>`` with
``XMLSerializer`` and hands it to the Convert artwork pipeline.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ._tab_common import write_svg_document


TITLE = "Plotterfun"
ORDER = 130

VENDOR_PAGE = (
    Path(__file__).resolve().parents[1] / "plotterfun_vendor" / "main.htm"
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView

    HAVE_WEBENGINE = True
except Exception:  # pragma: no cover - depends on the PySide6 wheel
    HAVE_WEBENGINE = False


class PlotterfunTab(QWidget):
    GROUP = "Photo-based"
    DESCRIPTION = "The full Plotterfun web app (22 algorithms), vendored."

    def __init__(self, host):
        super().__init__()
        self.host = host
        self._last_export = ""
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        hint = QLabel(
            "Load an image and choose an algorithm inside Plotterfun, then "
            "press Export SVG to plot. The captured SVG opens in Convert."
        )
        hint.setWordWrap(True)
        row.addWidget(hint, 1)
        self.export_button = QPushButton("Export SVG to plot")
        self.export_button.clicked.connect(self.export_svg)
        row.addWidget(self.export_button)
        layout.addLayout(row)
        if HAVE_WEBENGINE and VENDOR_PAGE.exists():
            self.view = QWebEngineView()
            self.view.setMinimumHeight(420)
            self.view.load(QUrl.fromLocalFile(str(VENDOR_PAGE)))
            layout.addWidget(self.view, 1)
        else:
            self.view = None
            self.export_button.setEnabled(False)
            message = QLabel(
                "QtWebEngine is required for the embedded Plotterfun app. "
                "Install the full PySide6 wheel (PySide6-Addons) and restart. "
                f"The vendored page is at {VENDOR_PAGE}."
            )
            message.setWordWrap(True)
            layout.addWidget(message, 1)

    def export_svg(self):
        if self.view is None:
            return
        self.view.page().runJavaScript(
            "new XMLSerializer().serializeToString("
            "document.querySelector('svg'))",
            self._svg_captured,
        )

    def _svg_captured(self, svg_text):
        if not svg_text or "<svg" not in svg_text:
            QMessageBox.warning(
                self,
                "Plotterfun export",
                "The page has no SVG yet; load an image and let Plotterfun "
                "finish drawing first.",
            )
            return
        path = str(write_svg_document("plotterfun", svg_text))
        self._last_export = path
        if self.host is not None:
            self.host.adopt_artwork(path)

    def build_svg(self):
        """The static Preview button rebuilds the last Plotterfun export."""
        if self._last_export:
            return self._last_export
        raise ValueError(
            "Plotterfun owns its own image loading and preview; use the "
            "Export SVG to plot button above."
        )


def create_tab(host):
    return PlotterfunTab(host)
