"""Shared QtWebEngine host for bundled Plotterfun-family applications."""

from __future__ import annotations

import dataclasses
import mimetypes
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ._plotterfun_simple import PlotterfunSimpleWorkflowMixin
from ._tab_common import write_svg_document


try:
    from PySide6.QtWebEngineWidgets import QWebEngineView

    HAVE_WEBENGINE = True
except Exception:  # pragma: no cover - depends on the PySide6 wheel
    HAVE_WEBENGINE = False


class _LocalStaticServer:
    """Serve one vendored app from loopback for Chromium module workers."""

    def __init__(self, root, artwork_path_getter=None):
        self.root = Path(root).resolve()
        self._artwork_path_getter = artwork_path_getter
        self._artwork_path = ""
        outer = self

        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, _format, *_args):
                return

            def do_GET(self):
                if urlsplit(self.path).path == "/current-artwork":
                    self._serve_current_artwork()
                    return
                super().do_GET()

            def _serve_current_artwork(self):
                path = outer.current_artwork
                if not path or not Path(path).is_file():
                    self.send_error(404, "No current artwork")
                    return
                payload = Path(path).read_bytes()
                content_type = (
                    mimetypes.guess_type(path)[0]
                    or "application/octet-stream"
                )
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(payload)

        self._server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            partial(Handler, directory=str(self.root)),
        )
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="plotterfun-extended-http",
            daemon=True,
        )
        self._thread.start()

    @property
    def url(self):
        return (
            f"http://127.0.0.1:{self._server.server_port}/index.html"
        )

    @property
    def current_artwork(self):
        if self._artwork_path_getter is not None:
            try:
                value = self._artwork_path_getter()
            except Exception:
                value = ""
            if value:
                self._artwork_path = str(value)
        return self._artwork_path

    def close(self):
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2.0)
        self._server = None


class PlotterfunWebTab(PlotterfunSimpleWorkflowMixin, QWidget):
    """Embed a local Plotterfun page and export its current SVG."""

    def __init__(
        self,
        host,
        *,
        title,
        description,
        page_path,
        export_slug,
        serve_http=False,
        allow_current_artwork=False,
        simple_workflow=False,
    ):
        super().__init__()
        self.host = host
        self.title = title
        self.description = description
        self.page_path = Path(page_path)
        self.export_slug = export_slug
        self.simple_workflow = bool(simple_workflow)
        self._last_export = ""
        self._server = None
        self.view = None
        self._advanced_mode = False
        self._last_cmyk_folder = ""
        self._pending_cmyk_folder = None
        self._pending_cmyk_base = ""
        self._pending_cmyk_source = ""
        self._pending_cmyk_algorithm = ""
        self._pending_cmyk_settings = None
        self._cmyk_capture_polls = 0
        self._current_artwork_polls = 0
        self._use_image_polls = 0
        self._saved_workspace_sizes = None
        self._gcode_thread = None
        self._gcode_worker = None

        layout = QVBoxLayout(self)
        self.simple_status = None
        self.style_combo = None
        self.export_cmyk_button = None
        self.advanced_button = None
        if self.simple_workflow:
            self._build_simple_controls(layout)
        else:
            self._build_standard_controls(
                layout,
                allow_current_artwork=allow_current_artwork,
            )

        if HAVE_WEBENGINE and self.page_path.exists():
            self.view = QWebEngineView()
            self.view.setMinimumHeight(420)
            self.view.loadFinished.connect(self._web_load_finished)
            if serve_http:
                self._server = _LocalStaticServer(
                    self.page_path.parent,
                    artwork_path_getter=(
                        self._current_artwork_path
                        if allow_current_artwork
                        else None
                    ),
                )
                self.view.load(QUrl(self._server.url))
            else:
                self.view.load(QUrl.fromLocalFile(str(self.page_path)))
            layout.addWidget(self.view, 1)
        else:
            self.export_button.setEnabled(False)
            if self.use_current_button is not None:
                self.use_current_button.setEnabled(False)
            if self.export_cmyk_button is not None:
                self.export_cmyk_button.setEnabled(False)
            if self.advanced_button is not None:
                self.advanced_button.setEnabled(False)
            message = QLabel(
                "QtWebEngine is required for the embedded Plotterfun app. "
                "Install the full PySide6 wheel (PySide6-Addons) and restart. "
                f"The vendored page is at {self.page_path}."
            )
            message.setWordWrap(True)
            layout.addWidget(message, 1)

    def _build_standard_controls(self, layout, *, allow_current_artwork):
        row = QHBoxLayout()
        hint = QLabel(
            "Load an image and choose an algorithm inside the page, then "
            "press Export SVG to plot. The captured SVG opens in Convert."
        )
        hint.setWordWrap(True)
        row.addWidget(hint, 1)
        if allow_current_artwork:
            self.use_current_button = QPushButton("Use current artwork")
            self.use_current_button.setToolTip(
                "Send the image currently selected in the converter's Artwork "
                "row into the embedded app."
            )
            self.use_current_button.clicked.connect(
                self.use_current_artwork
            )
            row.addWidget(self.use_current_button)
        else:
            self.use_current_button = None
        self.export_button = QPushButton("Export SVG to plot")
        self.export_button.clicked.connect(self.export_svg)
        row.addWidget(self.export_button)
        layout.addLayout(row)

    def _set_status(self, message):
        if self.simple_status is not None:
            self.simple_status.setText(str(message))
        status = getattr(self.host, "generator_status", None)
        if callable(status):
            status(str(message))

    def _web_load_finished(self, ok):
        if not ok:
            self._set_status(f"{self.title} could not load its local page.")
            return
        if self.simple_workflow:
            QTimer.singleShot(200, self._apply_simple_page_mode)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._update_workspace_focus)

    def hideEvent(self, event):
        self._update_workspace_focus()
        super().hideEvent(event)

    def _current_artwork_path(self):
        getter = getattr(self.host, "artwork_path", None)
        value = getter() if callable(getter) else getter
        return str(value or "").strip()

    def apply_tab_settings(self, settings):
        """Auto-fit the shared page frame for Plotterfun's pixel viewBox."""
        if not self.simple_workflow:
            return settings
        return dataclasses.replace(
            settings,
            fit_mode="inside",
            scale=1.0,
            hatch_spacing_mm=0.0,
        )

    def use_current_artwork(self):
        if self.view is None:
            return
        path = self._current_artwork_path()
        if not path:
            QMessageBox.warning(
                self,
                f"{self.title} image",
                "Select an artwork image in the converter first.",
            )
            return
        self._current_artwork_polls = 0
        self._use_image_polls = 0
        self._set_status(f"{self.title} is loading the current artwork…")
        self.view.page().runJavaScript(
            """
            (async () => {
              const response = await fetch('./current-artwork', {
                cache: 'no-store'
              });
              if (!response.ok) throw new Error('Artwork fetch failed');
              const blob = await response.blob();
              const input = document.querySelector('input[type=file]');
              if (!input) throw new Error('Image input is not ready');
              const subtype = (blob.type.split('/')[1] || 'png')
                .replace('svg+xml', 'svg');
              const file = new File(
                [blob],
                `current-artwork.${subtype}`,
                {type: blob.type || 'image/png'}
              );
              const transfer = new DataTransfer();
              transfer.items.add(file);
              input.files = transfer.files;
              input.dispatchEvent(new Event('change', {bubbles: true}));
              return true;
            })()
            """,
            self._current_artwork_loaded,
        )

    def _current_artwork_loaded(self, _result):
        # QtWebEngine does not await the async fetch promise before invoking
        # this callback. Verify the hidden input after the browser event loop
        # has had a chance to process the synthetic file change.
        QTimer.singleShot(400, self._verify_current_artwork)

    def _verify_current_artwork(self):
        if self.view is None:
            return
        self.view.page().runJavaScript(
            "Boolean(document.querySelector('input[type=file]')?.files?.length)",
            self._current_artwork_verified,
        )

    def _current_artwork_verified(self, loaded):
        if loaded:
            self._report_current_artwork(True)
            return
        self._current_artwork_polls += 1
        if self._current_artwork_polls < 30:
            QTimer.singleShot(200, self._verify_current_artwork)
            return
        self._report_current_artwork(False)

    def _report_current_artwork(self, loaded):
        message = (
            f"{self.title} loaded the current artwork."
            if loaded
            else f"{self.title} could not load the current artwork."
        )
        self._set_status(message)
        if loaded and self.simple_workflow:
            self._use_image_polls = 0
            QTimer.singleShot(120, self._activate_page_image)

    def export_svg(self):
        if self.view is None:
            return
        self.view.page().runJavaScript(
            "(() => {"
            "const svg = document.querySelector('svg');"
            "return svg ? new XMLSerializer().serializeToString(svg) : '';"
            "})()",
            self._svg_captured,
        )

    def _svg_captured(self, svg_text):
        if not svg_text or "<svg" not in svg_text:
            QMessageBox.warning(
                self,
                f"{self.title} export",
                "The page has no SVG yet; load an image and let the selected "
                "algorithm finish drawing first.",
            )
            return
        path = str(write_svg_document(self.export_slug, svg_text))
        self._last_export = path
        if self.host is not None:
            self.host.adopt_artwork(path)

    def build_svg(self):
        """The static Preview button rebuilds the last embedded export."""
        if self._last_export:
            return self._last_export
        raise ValueError(
            f"{self.title} owns its own image loading and preview; use the "
            "Export SVG to plot button above."
        )

    def closeEvent(self, event):
        shutdown = getattr(self, "shutdown_background", None)
        if callable(shutdown):
            shutdown()
        if self._server is not None:
            self._server.close()
            self._server = None
        super().closeEvent(event)
