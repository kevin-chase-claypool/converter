"""CMYK separation tab: one screened layer per ink pen.

RGB -> CMYK separation (with gray-component replacement) and the per-channel
halftone/stipple screening live in ``converter_core/cmyk.py``; the separation
math follows the MIT-licensed ohnorobo/cmyk-splitter. The tab builds four
layer SVGs, lets the shared OpenGL preview show any combination of them
through the layer checkboxes, and asks the host to analyze/save one complete
G-code program per ink.

The G-code itself is produced by the converter's normal pipeline - including
the r-theta axis-cost solver - so each file carries the same cost-efficient
motion planning as a Convert-tab program.
"""

from __future__ import annotations

import os
import threading

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

import converter_core as converter

from ._tab_common import GeneratorTab, double_spin, int_spin, write_svg_document


TITLE = "CMYK"
ORDER = 25


def format_seconds(seconds):
    """Short h/m/s form used by the cost table."""
    seconds = max(0, int(round(float(seconds))))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def format_cost_table(results):
    """Monospace table of the per-ink x_theta/y_theta cost split."""
    header = (
        f"{'Ink':<8}{'marks':>7}{'moves':>7}{'x_theta':>9}"
        f"{'y_theta':>9}{'draw mm':>10}{'est':>9}"
    )
    lines = [header, "-" * len(header)]
    total_seconds = 0.0
    total_marks = 0
    total_x = 0
    total_y = 0
    for channel in converter.CHANNELS:
        record = results.get(channel)
        if not record:
            continue
        total_seconds += float(record["seconds"])
        total_marks += int(record["marks"])
        total_x += int(record["x_count"])
        total_y += int(record["y_count"])
        lines.append(
            f"{converter.CHANNEL_LABELS[channel]:<8}{record['marks']:>7}"
            f"{record['moves']:>7}{record['x_count']:>9}{record['y_count']:>9}"
            f"{record['draw_mm']:>10.1f}{format_seconds(record['seconds']):>9}"
        )
    if len(lines) > 2:
        lines.append("-" * len(header))
        lines.append(
            f"{'Total':<8}{total_marks:>7}{'':>7}{total_x:>9}{total_y:>9}"
            f"{'':>10}{format_seconds(total_seconds):>9}"
        )
    return "\n".join(lines)


class ProgramAnalysisWorker(QObject):
    """Plan one program per ink on a worker thread via the host analyzer."""

    progress = Signal(int, str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, host, settings, scale, entries):
        super().__init__()
        self.host = host
        self.settings = settings
        self.scale = float(scale)
        self.entries = list(entries)
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def is_cancelled(self):
        return self.cancel_event.is_set()

    def run(self):
        try:
            results = {}
            total = max(1, len(self.entries))
            for index, (channel, svg_path) in enumerate(self.entries):
                if self.is_cancelled():
                    self.cancelled.emit()
                    return
                self.progress.emit(
                    int(100 * index / total),
                    f"Planning {converter.CHANNEL_LABELS[channel]}...",
                )
                data = self.host.analyze_program(
                    svg_path, self.settings, self.is_cancelled
                )
                moves = data["moves"]
                estimate = converter.estimate_program_time(moves, self.scale)
                counts = estimate["strategy_counts"]
                lengths = estimate["strategy_mm"]
                results[channel] = {
                    "marks": len(data["contours"]),
                    "moves": len(moves),
                    "gcode": data["gcode"],
                    "lines": len(data["gcode"].splitlines()),
                    "x_count": counts.get("x_theta", 0),
                    "y_count": counts.get("y_theta", 0),
                    "x_mm": lengths.get("x_theta", 0.0),
                    "y_mm": lengths.get("y_theta", 0.0),
                    "draw_mm": estimate["draw_mm"],
                    "seconds": estimate["total_seconds"],
                }
            self.finished.emit(results)
        except converter.OperationCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 - surfaced to the tab status
            self.failed.emit(str(exc))


class CmykTab(GeneratorTab):
    NAME = "cmyk"
    GROUP = "Photo-based"
    DESCRIPTION = "Split an image into four ink layers, one G-code each."
    # The tab draws its own halftone marks; the Convert-tab fill must not
    # hatch every dot outline a second time.
    SELF_SCREENED = True

    def __init__(self, host):
        super().__init__(host)
        image = self.add_group("Image")
        self.image_label = QLabel()
        self.image_label.setWordWrap(True)
        image.addRow("Artwork", self.image_label)

        options = self.add_group("Image options")
        self.saturation = double_spin(100, 0, 200, 5, 0, " %")
        options.addRow("Saturation", self.saturation)
        self.contrast = double_spin(100, 25, 200, 5, 0, " %")
        options.addRow("Contrast", self.contrast)
        self.gamma = double_spin(1.0, 0.2, 3.0, 0.05, 2)
        options.addRow("Ink gamma", self.gamma)
        self.gcr = double_spin(100, 0, 150, 5, 0, " %")
        options.addRow("Black (GCR)", self.gcr)
        self.resolution = int_spin(700, 200, 1400, 50)
        options.addRow("Resolution px", self.resolution)
        self.weight_c = double_spin(100, 0, 150, 5, 0, " %")
        self.weight_m = double_spin(100, 0, 150, 5, 0, " %")
        self.weight_y = double_spin(100, 0, 150, 5, 0, " %")
        self.weight_k = double_spin(80, 0, 150, 5, 0, " %")
        options.addRow("Cyan weight", self.weight_c)
        options.addRow("Magenta weight", self.weight_m)
        options.addRow("Yellow weight", self.weight_y)
        options.addRow("Black weight", self.weight_k)

        screen = self.add_group("Screen")
        self.style = QComboBox()
        self.style.addItem("Halftone dots", "halftone")
        self.style.addItem("Stipple dots", "stipple")
        screen.addRow("Style", self.style)
        self.pitch = double_spin(3.0, 0.8, 8.0, 0.2, 2, " mm")
        screen.addRow("Dot pitch", self.pitch)
        self.dot_size = double_spin(100, 20, 140, 5, 0, " %")
        screen.addRow("Dot size", self.dot_size)
        self.pen_width = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        screen.addRow("Pen width", self.pen_width)
        self.max_marks = int_spin(5000, 200, 20000, 500)
        screen.addRow("Max marks/ink", self.max_marks)
        self.seed = int_spin(7, 0, 999_999)
        screen.addRow("Seed (stipple)", self.seed)

        layers = self.add_group("Layers")
        self.preview_boxes = {}
        preview_row = QWidget()
        preview_layout = QHBoxLayout(preview_row)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        for channel in converter.CHANNELS:
            box = QCheckBox(converter.CHANNEL_LABELS[channel][0])
            box.setChecked(True)
            box.setToolTip(f"Show {converter.CHANNEL_LABELS[channel]} in the preview")
            self.preview_boxes[channel] = box
            preview_layout.addWidget(box)
        layers.addRow("Preview", preview_row)
        self.write_boxes = {}
        write_row = QWidget()
        write_layout = QHBoxLayout(write_row)
        write_layout.setContentsMargins(0, 0, 0, 0)
        for channel in converter.CHANNELS:
            box = QCheckBox(converter.CHANNEL_LABELS[channel][0])
            box.setChecked(True)
            box.setToolTip(f"Write {converter.CHANNEL_LABELS[channel]} G-code")
            self.write_boxes[channel] = box
            write_layout.addWidget(box)
        layers.addRow("Write files", write_row)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(6, 0, 50, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.scale_pct = double_spin(100, 10, 1000, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        actions = self.add_group("G-code (4 files)")
        self.analyze_button = QPushButton("Analyze cost (4 files)")
        self.analyze_button.clicked.connect(self.start_analysis)
        actions.addRow("", self.analyze_button)
        self.save_button = QPushButton("Save 4 G-code files...")
        self.save_button.clicked.connect(self.save_all)
        actions.addRow("", self.save_button)
        self.cancel_button = QPushButton("Cancel analysis")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        actions.addRow("", self.cancel_button)
        self.cost_label = QLabel("Analyze to split x_theta vs y_theta per ink.")
        self.cost_label.setWordWrap(False)
        self.cost_label.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        actions.addRow("", self.cost_label)

        self._layers = {}
        self._layer_files = {}
        self._layers_key = None
        self._analysis = None
        self._analysis_key = None
        self._thread = None
        self._worker = None
        self._pending_save = False
        self.finish_controls()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_artwork()

    def _refresh_artwork(self):
        path = ""
        if self.host is not None and hasattr(self.host, "artwork_path"):
            path = self.host.artwork_path()
        self._artwork = path
        self.image_label.setText(
            os.path.basename(path)
            if path
            else "(use Browse in the Artwork row above)"
        )

    def _weights(self):
        return {
            "c": self.weight_c.value() / 100.0,
            "m": self.weight_m.value() / 100.0,
            "y": self.weight_y.value() / 100.0,
            "k": self.weight_k.value() / 100.0,
        }

    def _control_key(self):
        settings_key = ""
        if self.host is not None and hasattr(self.host, "settings_for_source"):
            settings_key = repr(self.host.settings_for_source(self))
        return (
            getattr(self, "_artwork", ""),
            self.page_w.value(),
            self.page_h.value(),
            self.margin.value(),
            self.scale_pct.value(),
            self.saturation.value(),
            self.contrast.value(),
            self.gamma.value(),
            self.gcr.value(),
            self.resolution.value(),
            tuple(self._weights().items()),
            self.style.currentData(),
            self.pitch.value(),
            self.dot_size.value(),
            self.pen_width.value(),
            self.max_marks.value(),
            self.seed.value(),
            tuple(
                channel
                for channel in converter.CHANNELS
                if self.write_boxes[channel].isChecked()
            ),
            settings_key,
        )

    def _preview_channels(self):
        return [
            channel
            for channel in converter.CHANNELS
            if self.preview_boxes[channel].isChecked()
        ]

    def _write_channels(self):
        return [
            channel
            for channel in converter.CHANNELS
            if self.write_boxes[channel].isChecked()
        ]

    def _ensure_layers(self):
        self._refresh_artwork()
        path = self._artwork
        if not path:
            raise ValueError("Import an image with the Artwork row above first.")
        key = self._control_key()
        if self._layers_key == key and self._layers:
            return
        tones, geometry = converter.prepare_image_tones(
            path,
            self.page_w.value(),
            self.page_h.value(),
            margin_mm=self.margin.value(),
            resolution_px=self.resolution.value(),
            saturation=self.saturation.value() / 100.0,
            contrast=self.contrast.value() / 100.0,
            gcr=self.gcr.value() / 100.0,
            weights=self._weights(),
            gamma=self.gamma.value(),
        )
        width = self.page_w.value()
        height = self.page_h.value()
        stroke = self.pen_width.value()
        style = self.style.currentData()
        layers = {}
        files = {}
        for index, channel in enumerate(converter.CHANNELS):
            marks = converter.screen_channel(
                tones[channel],
                geometry,
                style=style,
                spacing_mm=self.pitch.value(),
                dot_scale=self.dot_size.value() / 100.0,
                angle_deg=converter.SCREEN_ANGLES_DEG[channel],
                seed=self.seed.value() + index,
                max_marks=self.max_marks.value(),
                pen_diameter_mm=self.pen_width.value(),
            )
            layers[channel] = marks
            document = converter.svg_document(
                {channel: marks}, width, height, stroke, order=[channel]
            )
            files[channel] = str(
                write_svg_document(f"cmyk-{channel}", document)
            )
        self._layers = layers
        self._layer_files = files
        self._layers_key = key

    def build_svg(self):
        self._ensure_layers()
        visible = self._preview_channels()
        if not visible:
            raise ValueError("Tick at least one preview layer.")
        QGuiApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            document = converter.svg_document(
                {channel: self._layers[channel] for channel in visible},
                self.page_w.value(),
                self.page_h.value(),
                self.pen_width.value(),
                order=visible,
            )
            path = str(write_svg_document(f"{self.NAME}-preview", document))
        finally:
            QGuiApplication.restoreOverrideCursor()
        counts = ", ".join(
            f"{converter.CHANNEL_LABELS[channel]} {len(self._layers[channel])}"
            for channel in visible
        )
        self.status.setText(f"Screened marks: {counts}.")
        if self.host is not None:
            self.host.generator_status(f"CMYK screened: {counts}.")
        return path

    def start_analysis(self, _checked=False):
        del _checked
        if self._thread is not None:
            return
        if getattr(self.host, "preview_thread", None) is not None:
            self.report_error("Finish or cancel the running preview before analyzing.")
            return
        try:
            self._ensure_layers()
        except Exception as exc:  # noqa: BLE001 - user-facing setup error
            self.report_error(str(exc))
            return
        channels = self._write_channels()
        if not channels:
            self.report_error("Tick at least one ink to write.")
            return
        if self.host is None or not hasattr(self.host, "analyze_program"):
            self.report_error("The host window does not provide program analysis.")
            return
        entries = [(channel, self._layer_files[channel]) for channel in channels]
        settings = (
            self.host.settings_for_source(self)
            if hasattr(self.host, "settings_for_source")
            else converter.Settings()
        )
        scale = (
            self.host.motion_estimate_scale()
            if hasattr(self.host, "motion_estimate_scale")
            else converter.DEFAULT_MOTION_ESTIMATE_SCALE
        )
        self._analysis_key = self._control_key()
        self._worker = ProgramAnalysisWorker(self.host, settings, scale, entries)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.cancelled.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self.analyze_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.cost_label.setText("Planning...")
        self.status.setText("Analyzing the four ink programs...")
        self._thread.start()

    def cancel_analysis(self):
        if self._worker is not None:
            self._worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status.setText("Cancelling analysis...")

    def analysis_running(self):
        """True while the layer analysis worker is planning programs."""
        return self._thread is not None

    def _on_progress(self, percent, text):
        self.cost_label.setText(f"{text} {percent}%")
        self.status.setText(text)

    def _on_finished(self, results):
        self._analysis = results
        self.cost_label.setText(format_cost_table(results))
        summary = ", ".join(
            f"{converter.CHANNEL_LABELS[channel]} {format_seconds(record['seconds'])}"
            for channel, record in results.items()
        )
        message = f"CMYK cost analysis: {summary}."
        self.status.setText(message)
        if self.host is not None:
            self.host.generator_status(message)
            if hasattr(self.host, "log"):
                for channel, record in results.items():
                    self.host.log.append(
                        "CMYK %s: %d marks, x_theta %d / y_theta %d, "
                        "draw %.1f mm, estimate %s."
                        % (
                            converter.CHANNEL_LABELS[channel],
                            record["marks"],
                            record["x_count"],
                            record["y_count"],
                            record["draw_mm"],
                            format_seconds(record["seconds"]),
                        )
                    )
        if self._pending_save:
            self._pending_save = False
            self._write_files(results)

    def _on_failed(self, message):
        self.report_error(f"Analysis failed: {message}")
        self.cost_label.setText("Analysis failed.")
        self._pending_save = False

    def _on_cancelled(self):
        self.status.setText("Analysis cancelled.")
        self.cost_label.setText("Analysis cancelled; the last result is kept.")
        self._pending_save = False

    def _on_thread_finished(self):
        self._thread = None
        self._worker = None
        self.analyze_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def save_all(self, _checked=False):
        del _checked
        channels = self._write_channels()
        if not channels:
            self.report_error("Tick at least one ink to write.")
            return
        if self._analysis is None or self._analysis_key != self._control_key():
            self._pending_save = True
            self.status.setText("Analyzing before save...")
            self.start_analysis()
            return
        self._write_files(self._analysis)

    def _write_files(self, results):
        entries = [
            (converter.CHANNEL_LABELS[channel].lower(), results[channel]["gcode"])
            for channel in converter.CHANNELS
            if channel in results
        ]
        if not entries:
            self.report_error("Nothing to save; run the analysis first.")
            return
        base = ""
        if getattr(self, "_artwork", ""):
            stem = os.path.splitext(os.path.basename(self._artwork))[0]
            base = f"{stem}-cmyk.gcode"
        export = getattr(self.host, "export_program_set", None)
        if not callable(export):
            self.report_error("The host window does not provide batch saving.")
            return
        written = export(entries, None, base)
        if written:
            names = ", ".join(os.path.basename(path) for path in written)
            self.status.setText(
                f"Saved {len(written)} G-code files ({names})."
            )


def create_tab(host):
    return CmykTab(host)
