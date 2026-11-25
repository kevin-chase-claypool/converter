"""Simple CMYK workflow layered over the Plotterfun Extended web page."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QToolButton,
    QVBoxLayout,
)

from ._plotterfun_cmyk import (
    CmykSplitError,
    sanitize_base_name,
    write_cmyk_svg_set,
)
from ._plotterfun_gcode import (
    planned_gcode_paths,
    write_plotterfun_gcode_set,
)


STYLE_PRESETS = (
    (
        "Flow Field (recommended)",
        "flowfield.js",
        "Long contour-following strokes with dense marks in darker areas.",
    ),
    (
        "Contours",
        "contours.js",
        "Topographic lines that follow image tone and shape.",
    ),
    ("Linedraw", "linedraw.js", "Clean edge-focused line art."),
    (
        "Stipple",
        "stipple.js",
        "Tonal dots, with denser marks in darker areas.",
    ),
    ("Crosshatch", "crosshatch.js", "Layered engraving-style hatching."),
    ("Halftone", "halftone.js", "A classic variable-dot print screen."),
    (
        "Squiggle",
        "squiggle.js",
        "Continuous wavy rows generated from image tone.",
    ),
)


SIMPLE_PAGE_CSS = """
:root[data-theta-simple="true"] .app-header,
:root[data-theta-simple="true"] #sidebar,
:root[data-theta-simple="true"] .app-footer {
  display: none !important;
}
:root[data-theta-simple="true"] .app-body {
  display: block !important;
  min-height: 0 !important;
}
:root[data-theta-simple="true"] .canvas-stage {
  width: 100% !important;
  height: 100% !important;
  padding: 10px !important;
}
:root[data-theta-simple="true"] .canvas-shell {
  width: 100% !important;
  height: 100% !important;
  max-width: 100% !important;
  max-height: 100% !important;
  border-radius: 8px !important;
}
:root[data-theta-simple="true"] .status-pill {
  left: 16px !important;
  bottom: 16px !important;
}
"""


class PlotterfunGcodeWorker(QObject):
    """Build the four G-code programs away from the Qt event thread."""

    progress = Signal(int, str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(
        self,
        svg_export,
        folder,
        settings,
        *,
        analyze_program,
        source_artwork,
        algorithm,
    ):
        super().__init__()
        self.svg_export = svg_export
        self.folder = folder
        self.settings = settings
        self.analyze_program = analyze_program
        self.source_artwork = source_artwork
        self.algorithm = algorithm
        self._cancel_requested = False

    def request_cancel(self):
        self._cancel_requested = True

    @Slot()
    def run(self):
        try:
            result = write_plotterfun_gcode_set(
                self.svg_export,
                self.folder,
                self.settings,
                analyze_program=self.analyze_program,
                source_artwork=self.source_artwork,
                algorithm=self.algorithm,
                cancel_check=lambda: self._cancel_requested,
                progress=self.progress.emit,
            )
        except Exception as exc:
            if self._cancel_requested:
                self.cancelled.emit()
            else:
                self.failed.emit(str(exc))
            return
        self.finished.emit(result)


class PlotterfunSimpleWorkflowMixin:
    """Three-step UI and registered CMYK export for one web tab."""

    def _build_simple_controls(self, layout):
        card = QFrame()
        card.setObjectName("plotterfunSimpleCard")
        card.setStyleSheet(
            "QFrame#plotterfunSimpleCard {"
            "  background: palette(window);"
            "  border: 1px solid palette(mid);"
            "  border-radius: 8px;"
            "}"
            "QLabel#plotterfunSimpleTitle {"
            "  color: palette(text);"
            "  font-size: 13px;"
            "  font-weight: 700;"
            "}"
            "QLabel#plotterfunSimpleHint {"
            "  color: palette(text);"
            "  font-size: 11px;"
            "}"
            "QLabel#plotterfunSimpleStatus {"
            "  color: palette(text);"
            "  font-size: 11px;"
            "}"
            "QFrame#plotterfunSimpleCard QPushButton {"
            "  color: palette(button-text);"
            "}"
            "QFrame#plotterfunSimpleCard QComboBox {"
            "  color: palette(text);"
            "  background: palette(button);"
            "}"
        )
        body = QVBoxLayout(card)
        body.setContentsMargins(10, 9, 10, 9)
        body.setSpacing(6)

        title = QLabel("CMYK G-code set")
        title.setObjectName("plotterfunSimpleTitle")
        body.addWidget(title)
        hint = QLabel(
            "One page, four registered G-code files. Run them in this order: "
            "Yellow → Magenta → Cyan → Black."
        )
        hint.setObjectName("plotterfunSimpleHint")
        hint.setWordWrap(True)
        body.addWidget(hint)

        self.use_current_button = QPushButton("1. Use current artwork")
        self.use_current_button.setObjectName("plotterfunPrimaryButton")
        self.use_current_button.setToolTip(
            "Load the converter's current image and start drawing automatically."
        )
        self.use_current_button.clicked.connect(self.use_current_artwork)
        body.addWidget(self.use_current_button)

        style_label = QLabel("2. Style")
        style_label.setObjectName("plotterfunSimpleHint")
        body.addWidget(style_label)
        self.style_combo = QComboBox()
        self.style_combo.setToolTip("Choose the mark-making style.")
        self.style_combo.blockSignals(True)
        for label, algorithm, description in STYLE_PRESETS:
            self.style_combo.addItem(label, algorithm)
            self.style_combo.setItemData(
                self.style_combo.count() - 1,
                description,
                Qt.ToolTipRole,
            )
        self.style_combo.blockSignals(False)
        self.style_combo.currentIndexChanged.connect(self._style_changed)
        body.addWidget(self.style_combo)

        self.export_cmyk_button = QPushButton(
            "3. Create Y/M/C/K G-code files…"
        )
        self.export_cmyk_button.setObjectName("plotterfunPrimaryButton")
        self.export_cmyk_button.setToolTip(
            "Choose one folder. Four ready-to-run, page-registered G-code "
            "files and a print manifest will be written there."
        )
        self.export_cmyk_button.clicked.connect(self.export_cmyk_gcode_set)
        body.addWidget(self.export_cmyk_button)

        advanced_row = QHBoxLayout()
        advanced_row.addStretch(1)
        self.advanced_button = QToolButton()
        self.advanced_button.setText("Advanced controls")
        self.advanced_button.setCheckable(True)
        self.advanced_button.setArrowType(Qt.RightArrow)
        self.advanced_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )
        self.advanced_button.toggled.connect(self._set_advanced_mode)
        advanced_row.addWidget(self.advanced_button)
        body.addLayout(advanced_row)

        self.simple_status = QLabel(
            "Ready. Load the current artwork, choose a style, then create "
            "the G-code set."
        )
        self.simple_status.setObjectName("plotterfunSimpleStatus")
        self.simple_status.setWordWrap(True)
        body.addWidget(self.simple_status)
        layout.addWidget(card)

        # The combined export remains available when advanced controls are
        # open, but it no longer competes with the four-file action by default.
        self.export_button = QPushButton("Open combined SVG in Convert")
        self.export_button.clicked.connect(self.export_svg)
        self.export_button.hide()
        layout.addWidget(self.export_button)

    def _update_workspace_focus(self):
        """Use the full workspace for the simplified embedded preview."""
        if not self.simple_workflow:
            return
        panel = getattr(self.host, "preview_panel", None)
        split = getattr(self.host, "main_split", None)
        focus_embedded = self.isVisible() and not self._advanced_mode
        if panel is None:
            return
        if focus_embedded:
            if panel.isVisible():
                self._saved_workspace_sizes = (
                    split.sizes() if split is not None else None
                )
                panel.hide()
            return
        if not panel.isVisible():
            panel.show()
            if (
                split is not None
                and self._saved_workspace_sizes is not None
            ):
                split.setSizes(self._saved_workspace_sizes)

    def _apply_simple_page_mode(self):
        if self.view is None or not self.simple_workflow:
            return
        enabled = not self._advanced_mode
        css = json.dumps(SIMPLE_PAGE_CSS)
        self.view.page().runJavaScript(
            f"""
            (() => {{
              let style = document.getElementById('theta-simple-mode-style');
              if (!style) {{
                style = document.createElement('style');
                style.id = 'theta-simple-mode-style';
                document.head.appendChild(style);
              }}
              style.textContent = {css};
              document.documentElement.dataset.thetaSimple =
                {json.dumps("true" if enabled else "false")};
            }})()
            """
        )
        if enabled:
            self._apply_simple_page_defaults()

    def _apply_simple_page_defaults(self, *, use_style=True):
        if self.view is None or not self.simple_workflow:
            return
        wanted_algorithm = (
            str(
                self.style_combo.currentData()
                if self.style_combo is not None
                else "flowfield.js"
            )
            if use_style
            else None
        )
        self.view.page().runJavaScript(
            f"""
            (() => {{
              const wantedAlgorithm = {json.dumps(wanted_algorithm)};
              let attempts = 0;
              const apply = () => {{
                const algorithm = document.querySelector('#algorithmTop');
                const colorMode = document.querySelector('#colorMode');
                if (!algorithm || !colorMode) {{
                  if (attempts++ < 40) window.setTimeout(apply, 200);
                  return;
                }}
                if (
                  wantedAlgorithm !== null &&
                  algorithm.value !== wantedAlgorithm
                ) {{
                  algorithm.value = wantedAlgorithm;
                  algorithm.dispatchEvent(
                    new Event('change', {{bubbles: true}})
                  );
                }}
                if (colorMode.value !== 'cmyk') {{
                  colorMode.value = 'cmyk';
                  colorMode.dispatchEvent(
                    new Event('change', {{bubbles: true}})
                  );
                }}
                window.setTimeout(() => {{
                  const includeBlack =
                    document.querySelector('#includeBlack');
                  if (includeBlack && !includeBlack.checked) {{
                    includeBlack.click();
                  }}
                }}, 120);
              }};
              apply();
            }})()
            """
        )

    def _style_changed(self, _index):
        if (
            self.view is None
            or not self.simple_workflow
            or self._advanced_mode
        ):
            return
        self._apply_simple_page_defaults()
        self._set_status(
            f"Style: {self.style_combo.currentText()}. "
            "Use current artwork to generate it."
        )

    def _set_advanced_mode(self, enabled):
        self._advanced_mode = bool(enabled)
        if self.advanced_button is not None:
            self.advanced_button.setArrowType(
                Qt.DownArrow if enabled else Qt.RightArrow
            )
            self.advanced_button.setText(
                "Hide advanced controls"
                if enabled
                else "Advanced controls"
            )
        self.export_button.setVisible(bool(enabled))
        self._apply_simple_page_mode()
        self._update_workspace_focus()
        self._set_status(
            "Advanced Plotterfun controls are visible below."
            if enabled
            else "Simple CMYK workflow restored."
        )

    def _activate_page_image(self):
        if self.view is None:
            return
        self.view.page().runJavaScript(
            """
            (() => {
              const preview = document.querySelector('.preview-canvas');
              if (!preview || preview.width < 2 || preview.height < 2) {
                return false;
              }
              const context = preview.getContext('2d');
              if (!context) return false;
              const pixels = context.getImageData(
                0,
                0,
                preview.width,
                preview.height
              ).data;
              const stride = Math.max(
                4,
                Math.floor(pixels.length / 2048 / 4) * 4
              );
              let imageReady = false;
              for (let index = 3; index < pixels.length; index += stride) {
                if (pixels[index] !== 0) {
                  imageReady = true;
                  break;
                }
              }
              if (!imageReady) return false;
              const button = Array.from(
                document.querySelectorAll('button')
              ).find(
                (item) =>
                  item.textContent.trim().toLowerCase() === 'use image'
              );
              if (!button) return false;
              button.click();
              return true;
            })()
            """,
            self._page_image_activated,
        )

    def _page_image_activated(self, activated):
        if activated:
            self._apply_simple_page_defaults(
                use_style=not self._advanced_mode
            )
            style = (
                self.style_combo.currentText()
                if self.style_combo is not None
                else "selected style"
            )
            self._set_status(
                f"Artwork loaded. Building the {style} CMYK preview…"
            )
            return
        self._use_image_polls += 1
        if self._use_image_polls < 30:
            QTimer.singleShot(200, self._activate_page_image)
            return
        self._set_status(
            "Artwork loaded, but Plotterfun did not accept it. "
            "Open Advanced controls and press Use image."
        )

    def export_cmyk_gcode_set(self):
        """Write four ready-to-run programs from the current CMYK drawing."""
        if self.view is None:
            return
        if self._gcode_thread is not None:
            self._set_status(
                "The CMYK G-code set is already being generated."
            )
            return
        source = self._current_artwork_path()
        base_name = sanitize_base_name(
            source or "plotterfun-extended"
        )
        initial = self._last_cmyk_folder
        if not initial and source:
            initial = str(Path(source).parent)
        if not initial:
            initial = str(Path.home())
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose one folder for the Y/M/C/K G-code set",
            initial,
        )
        if not folder:
            self._set_status("CMYK G-code export cancelled.")
            return
        folder = Path(folder)
        existing = [
            path
            for path in planned_gcode_paths(folder, base_name)
            if path.exists()
        ]
        if existing:
            answer = QMessageBox.question(
                self,
                "Replace existing CMYK G-code set?",
                (
                    f"{len(existing)} matching file(s) already exist in "
                    f"{folder}. Replace them with the new Y/M/C/K "
                    "G-code set?"
                ),
                (
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                ),
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self._set_status("CMYK G-code export cancelled.")
                return

        settings_for_source = getattr(
            self.host,
            "settings_for_source",
            None,
        )
        if not callable(settings_for_source):
            QMessageBox.warning(
                self,
                f"{self.title} G-code export",
                "The converter host cannot provide G-code settings.",
            )
            return
        try:
            settings = settings_for_source(self)
        except Exception as exc:
            QMessageBox.warning(
                self,
                f"{self.title} G-code export",
                f"The current G-code settings are invalid: {exc}",
            )
            return
        self._last_cmyk_folder = str(folder)
        self._pending_cmyk_folder = folder
        self._pending_cmyk_base = base_name
        self._pending_cmyk_source = source
        self._pending_cmyk_settings = settings
        self._pending_cmyk_algorithm = str(
            self.style_combo.currentData() or ""
        )
        self._cmyk_capture_polls = 0
        if self.export_cmyk_button is not None:
            self.export_cmyk_button.setEnabled(False)
        self._set_status(
            "Preparing four page-registered CMYK G-code files…"
        )
        self._apply_simple_page_defaults(use_style=not self._advanced_mode)
        QTimer.singleShot(300, self._capture_cmyk_export)

    def _capture_cmyk_export(self):
        if self.view is None:
            return
        self.view.page().runJavaScript(
            """
            (() => {
              const svg =
                document.querySelector('svg.plot-output') ||
                document.querySelector('svg');
              const buffer = document.querySelector('#buffering');
              const buffering = Boolean(
                buffer &&
                window.getComputedStyle(buffer).visibility !== 'hidden'
              );
              const canvasReady = Boolean(
                document.querySelector('#colorMode')
              );
              const pathCount = svg
                ? svg.querySelectorAll(
                    '#yellow path, #magenta path, #cyan path, #black path'
                  ).length
                : 0;
              return JSON.stringify({
                svg: svg
                  ? new XMLSerializer().serializeToString(svg)
                  : '',
                buffering,
                canvasReady,
                pathCount,
                algorithm:
                  document.querySelector('#algorithmTop')?.value || ''
              });
            })()
            """,
            self._cmyk_page_captured,
        )

    def _cmyk_page_captured(self, payload):
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {"svg": payload}
        if not isinstance(payload, dict):
            payload = {"svg": str(payload or "")}
        self._cmyk_capture_polls += 1
        ready = bool(payload.get("canvasReady"))
        buffering = bool(payload.get("buffering"))
        path_count = int(payload.get("pathCount") or 0)
        waiting = (
            not ready
            or buffering
            or (path_count == 0 and self._cmyk_capture_polls < 40)
        )
        if waiting and self._cmyk_capture_polls < 480:
            if not ready:
                message = "Waiting for the Plotterfun page to become ready…"
            elif buffering:
                message = "Waiting for Plotterfun to finish the CMYK drawing…"
            else:
                message = "Waiting for the first CMYK strokes…"
            self._set_status(message)
            QTimer.singleShot(250, self._capture_cmyk_export)
            return
        if not ready or path_count == 0:
            if self.export_cmyk_button is not None:
                self.export_cmyk_button.setEnabled(True)
            QMessageBox.warning(
                self,
                f"{self.title} CMYK export",
                (
                    "There are no finished CMYK strokes to export yet. "
                    "Use the current artwork, wait for the drawing to finish, "
                    "then export again."
                ),
            )
            self._set_status("CMYK G-code export needs a finished drawing.")
            return
        self._pending_cmyk_algorithm = str(
            payload.get("algorithm")
            or self._pending_cmyk_algorithm
            or ""
        )
        self._cmyk_svg_captured(str(payload.get("svg") or ""))

    def _cmyk_svg_captured(self, svg_text):
        folder = self._pending_cmyk_folder
        if folder is None:
            if self.export_cmyk_button is not None:
                self.export_cmyk_button.setEnabled(True)
            self._set_status("Choose a destination folder before exporting.")
            return
        try:
            intermediate = Path(
                tempfile.mkdtemp(prefix="theta-plotterfun-cmyk-")
            )
            svg_export = write_cmyk_svg_set(
                str(svg_text or ""),
                intermediate,
                base_name=self._pending_cmyk_base,
                source_artwork=self._pending_cmyk_source,
                algorithm=self._pending_cmyk_algorithm,
            )
        except (CmykSplitError, OSError, ValueError) as exc:
            if self.export_cmyk_button is not None:
                self.export_cmyk_button.setEnabled(True)
            QMessageBox.warning(
                self,
                f"{self.title} CMYK export",
                str(exc),
            )
            self._set_status(f"CMYK G-code export failed: {exc}")
            return
        self._start_gcode_worker(svg_export)

    def _start_gcode_worker(self, svg_export):
        if self._pending_cmyk_settings is None:
            if self.export_cmyk_button is not None:
                self.export_cmyk_button.setEnabled(True)
            self._set_status("The converter did not provide G-code settings.")
            return
        analyze_program = getattr(self.host, "analyze_program", None)
        if not callable(analyze_program):
            if self.export_cmyk_button is not None:
                self.export_cmyk_button.setEnabled(True)
            self._set_status(
                "The converter cannot generate registered G-code."
            )
            return
        self._gcode_thread = QThread(self)
        self._gcode_worker = PlotterfunGcodeWorker(
            svg_export,
            self._pending_cmyk_folder,
            self._pending_cmyk_settings,
            analyze_program=analyze_program,
            source_artwork=self._pending_cmyk_source,
            algorithm=self._pending_cmyk_algorithm,
        )
        self._gcode_worker.moveToThread(self._gcode_thread)
        self._gcode_thread.started.connect(self._gcode_worker.run)
        self._gcode_worker.progress.connect(self._gcode_progress)
        self._gcode_worker.finished.connect(self._gcode_finished)
        self._gcode_worker.failed.connect(self._gcode_failed)
        self._gcode_worker.cancelled.connect(self._gcode_cancelled)
        self._gcode_worker.finished.connect(self._gcode_thread.quit)
        self._gcode_worker.failed.connect(self._gcode_thread.quit)
        self._gcode_worker.cancelled.connect(self._gcode_thread.quit)
        self._gcode_worker.finished.connect(self._gcode_worker.deleteLater)
        self._gcode_worker.failed.connect(self._gcode_worker.deleteLater)
        self._gcode_worker.cancelled.connect(self._gcode_worker.deleteLater)
        self._gcode_thread.finished.connect(self._gcode_thread.deleteLater)
        self._gcode_thread.finished.connect(self._gcode_thread_done)
        self._set_status("Creating the four CMYK G-code files…")
        self._gcode_thread.start()

    def _gcode_progress(self, index, message):
        self._set_status(message)

    def _gcode_finished(self, exported):
        order = " → ".join(
            f"{layer.order} {layer.label}" for layer in exported.layers
        )
        message = (
            f"Saved 4 CMYK G-code files in {exported.folder}. Run {order}. "
            f"Manifest: {exported.manifest_path.name}"
        )
        if exported.missing_inks:
            message += (
                " Blank artwork layers: "
                + ", ".join(exported.missing_inks)
                + "."
            )
        self._set_status(message)
        log = getattr(self.host, "log", None)
        if log is not None and callable(getattr(log, "append", None)):
            for layer in exported.layers:
                log.append(
                    f"CMYK G-code {layer.order}/4 {layer.label}: "
                    f"{layer.path}"
                )
            log.append(f"CMYK G-code set manifest: {exported.manifest_path}")

    def _gcode_failed(self, message):
        if self.export_cmyk_button is not None:
            self.export_cmyk_button.setEnabled(True)
        QMessageBox.warning(
            self,
            f"{self.title} CMYK G-code export",
            message,
        )
        self._set_status(f"CMYK G-code export failed: {message}")

    def _gcode_cancelled(self):
        if self.export_cmyk_button is not None:
            self.export_cmyk_button.setEnabled(True)
        self._set_status("CMYK G-code export cancelled.")

    def _gcode_thread_done(self):
        self._gcode_thread = None
        self._gcode_worker = None
        if self.export_cmyk_button is not None:
            self.export_cmyk_button.setEnabled(True)

    def save_all(self):
        self.export_cmyk_gcode_set()

    def shutdown_background(self):
        if self._gcode_worker is not None:
            self._gcode_worker.request_cancel()
        thread = self._gcode_thread
        if thread is not None:
            thread.quit()
            thread.wait(5000)
