"""Kaleidoscope Converter - import or generate artwork, mirror it, save G-code.

This is a focused sibling of `qt_svg_to_gcode.pyw`. It reuses the converter
core wholesale: `converter_core.kaleidoscope` builds the mirrored design and the
existing planner, polar kinematics and emitter produce the program, while
`converter_core.generative` can draw the source as a sequence-driven mandala.
Only the source handling, the design controls and a flat bed-frame preview are
new.
"""

import dataclasses
import json
import math
import os
import random
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))

import converter_core as converter


SOURCE_FILTER = (
    "Artwork (*.svg *.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;"
    "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;"
    "SVG (*.svg);;All files (*.*)"
)


class DesignPreview(QWidget):
    """Flat bed-frame view of the design, the bed circle and the reach circle."""

    dragged = Signal(float, float)
    viewChanged = Signal(float)

    def __init__(self):
        super().__init__()
        self.contours = []
        self.bed_radius = 457.2 / 2.0
        self.reach_radius = 185.0
        self.bounds_radius = 181.3
        self.wedge_deg = 15.0
        self.show_wedge = True
        self.zoom = 1.0
        self.pan = (0.0, 0.0)
        self._drag_from = None
        self._pan_from = None
        self.setMinimumSize(360, 360)
        self.setMouseTracking(True)
        self.setToolTip(
            "Wheel zooms, Shift-drag (or middle/right drag) pans, plain drag "
            "moves the image inside the frame."
        )

    def set_design(self, contours, wedge_deg):
        self.contours = contours
        self.wedge_deg = float(wedge_deg)
        self.update()

    # -- view transform ----------------------------------------------------

    def _base_scale(self):
        half = max(self.bed_radius, 1.0)
        return min(self.width(), self.height()) * 0.48 / half

    def _scale(self):
        """Millimetres to pixels at the current zoom."""
        return self._base_scale() * self.zoom

    def to_screen(self, point):
        scale = self._scale()
        cx, cy = self.width() / 2.0, self.height() / 2.0
        return QPointF(
            cx + (point[0] - self.pan[0]) * scale,
            cy - (point[1] - self.pan[1]) * scale,
        )

    def to_design(self, position):
        scale = max(self._scale(), 1e-9)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        return (
            (position.x() - cx) / scale + self.pan[0],
            (cy - position.y()) / scale + self.pan[1],
        )

    def screen_delta_to_mm(self, dx, dy):
        scale = max(self._scale(), 1e-9)
        return dx / scale, -dy / scale

    # -- zoom and pan, the same gestures as the main converter -------------

    def set_zoom(self, factor, anchor=None):
        factor = max(0.1, min(float(factor), 20.0))
        if abs(factor - self.zoom) < 1e-9:
            return
        if anchor is None:
            self.zoom = factor
        else:
            # Keep the design point under the cursor where it is.
            world = self.to_design(anchor)
            self.zoom = factor
            scale = max(self._scale(), 1e-9)
            cx, cy = self.width() / 2.0, self.height() / 2.0
            self.pan = (
                world[0] - (anchor.x() - cx) / scale,
                world[1] - (cy - anchor.y()) / scale,
            )
        self.viewChanged.emit(self.zoom)
        self.update()

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.25)

    def reset_view(self):
        self.zoom = 1.0
        self.pan = (0.0, 0.0)
        self.viewChanged.emit(self.zoom)
        self.update()

    def pan_by(self, dx, dy):
        """Pan the view by a screen-space delta in pixels."""
        scale = max(self._scale(), 1e-9)
        self.pan = (self.pan[0] - dx / scale, self.pan[1] + dy / scale)
        self.update()

    def wheelEvent(self, event):  # noqa: N802 - Qt naming
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        self.set_zoom(
            self.zoom * (1.15 if delta > 0 else 1.0 / 1.15), event.position()
        )
        event.accept()

    # -- dragging moves the source image inside the fixed design frame -----

    def mousePressEvent(self, event):  # noqa: N802 - Qt naming
        wants_pan = bool(event.modifiers() & Qt.ShiftModifier) or event.button() in (
            Qt.MiddleButton,
            Qt.RightButton,
        )
        if event.button() == Qt.LeftButton and not wants_pan:
            self._drag_from = event.position()
        elif wants_pan:
            self._pan_from = event.position()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):  # noqa: N802 - Qt naming
        position = event.position()
        if self._pan_from is not None:
            self.pan_by(
                position.x() - self._pan_from.x(), position.y() - self._pan_from.y()
            )
            self._pan_from = position
            return
        if self._drag_from is None:
            return
        dx, dy = self.screen_delta_to_mm(
            position.x() - self._drag_from.x(), position.y() - self._drag_from.y()
        )
        self.dragged.emit(dx, dy)
        self._drag_from = position

    def mouseReleaseEvent(self, event):  # noqa: N802 - Qt naming
        self._drag_from = None
        self._pan_from = None
        self.unsetCursor()

    def paintEvent(self, event):  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        scale = self._scale()
        origin = self.to_screen((0.0, 0.0))

        def circle(radius):
            r = radius * scale
            return QRectF(origin.x() - r, origin.y() - r, 2.0 * r, 2.0 * r)

        painter.setPen(QPen(QColor(205, 205, 205), 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(circle(self.bed_radius))
        painter.setPen(QPen(QColor(230, 180, 120), 1.2, Qt.DashLine))
        painter.drawEllipse(circle(self.reach_radius))
        painter.setPen(QPen(QColor(120, 160, 220), 1.4, Qt.DashLine))
        painter.drawEllipse(circle(self.bounds_radius))
        if self.show_wedge:
            painter.setPen(QPen(QColor(170, 200, 240), 1.0, Qt.DashLine))
            reach = self.reach_radius
            for angle in (0.0, self.wedge_deg):
                radians = math.radians(angle)
                painter.drawLine(
                    origin,
                    self.to_screen(
                        (reach * math.cos(radians), reach * math.sin(radians))
                    ),
                )
        painter.setPen(QPen(QColor(225, 225, 225), 1.0))
        painter.drawLine(
            QPointF(origin.x(), 0.0), QPointF(origin.x(), self.height())
        )
        painter.drawLine(QPointF(0.0, origin.y()), QPointF(self.width(), origin.y()))
        painter.setPen(QPen(QColor(30, 30, 30), 0.9))
        for contour in self.contours:
            if len(contour) < 2:
                continue
            painter.drawPolyline([self.to_screen(point) for point in contour])
        painter.setPen(QPen(QColor(120, 120, 120), 1.0))
        painter.setFont(QFont(painter.font().family(), 8))
        painter.drawText(
            8,
            self.height() - 8,
            "design contours: %d   bed %.0f mm   reach %.0f mm   design bound %.1f mm   "
            "zoom %.0f%%   drag moves the image - wheel zooms - Shift/middle "
            "drag pans"
            % (
                len(self.contours),
                self.bed_radius * 2.0,
                self.reach_radius,
                self.bounds_radius,
                self.zoom * 100.0,
            ),
        )


class KaleidoscopeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kaleidoscope Converter")
        self.source_path = ""
        self.design = []
        self.motif_folder = ""
        self.motif_paths = []
        self.motif_cache = {}
        self.fit_scale = 1.0
        self._settings_file = None

        self.preview = DesignPreview()
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(self.preview, 1)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(400)
        self.log.setFixedHeight(120)
        right_layout.addWidget(self.log)

        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.addWidget(self._source_group())
        panel_layout.addWidget(self._design_group())
        panel_layout.addWidget(self._bounds_group())
        panel_layout.addWidget(self._output_group())
        panel_layout.addStretch(1)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addWidget(panel)
        layout.addWidget(right, 1)
        self.setCentralWidget(central)
        self.preview.dragged.connect(self.on_image_dragged)
        self.zoom_in_button.clicked.connect(self.preview.zoom_in)
        self.zoom_out_button.clicked.connect(self.preview.zoom_out)
        self.reset_view_button.clicked.connect(self.preview.reset_view)
        self.preview.viewChanged.connect(self.on_view_changed)
        self._in_rebuild = False
        self._loading = True
        self.resize(1100, 720)
        self.say(
            "Open an SVG, PNG or JPG - or tick Generate a random pattern - "
            "set the divisions, then Build preview."
        )
        self.say(
            "Preview: wheel zooms, Shift-drag or middle/right-drag pans, plain "
            "drag moves the image inside the frame."
        )
        self.apply_settings()
        self._loading = False
        self._update_source_mode()
        if self._has_source():
            self.rebuild()

    # -- UI construction -------------------------------------------------

    def _source_group(self):
        box = QGroupBox("Source")
        form = QFormLayout(box)
        self.seed = QSpinBox()
        self.seed.setRange(0, 99999)
        self.seed.setValue(7)
        self.seed.setToolTip("The same seed always draws the same pattern.")
        self.seed_button = QPushButton("New seed")
        self.seed_button.setToolTip("Roll a fresh seed and redraw.")
        self.intricacy = QSpinBox()
        self.intricacy.setRange(1, 10)
        self.intricacy.setValue(5)
        self.intricacy.setToolTip(
            "More bands, finer waves and longer bead strings. Driven by golden-angle, "
            "Weyl, van der Corput, Fibonacci and prime sequences."
        )
        self.random_mode = QCheckBox("Generate a random pattern instead of artwork")
        self.random_mode.toggled.connect(self.on_source_mode_changed)
        seed_row = QHBoxLayout()
        seed_row.addWidget(self.seed)
        seed_row.addWidget(self.seed_button)
        form.addRow(self.random_mode)
        form.addRow("Seed", seed_row)
        form.addRow("Intricacy", self.intricacy)
        self.use_motifs = QCheckBox("Use natural motifs in patterns")
        self.use_motifs.setToolTip(
            "Fill the shape rings with traced copies of the motif folder's "
            "black-and-white images instead of the drawn shapes."
        )
        self.motif_button = QPushButton("Motif folder...")
        self.motif_button.setToolTip(
            "A folder of PNG/JPG shapes - leaves, shells, fish. Traced with the "
            "threshold, invert and trace-detail settings above."
        )
        self.motif_label = QLabel("(none)")
        self.motif_label.setWordWrap(True)
        motifs_row = QHBoxLayout()
        motifs_row.addWidget(self.motif_button)
        motifs_row.addWidget(self.motif_label, 1)
        form.addRow(self.use_motifs)
        form.addRow(motifs_row)
        self.use_motifs.toggled.connect(self.on_source_mode_changed)
        self.motif_button.clicked.connect(self.choose_motif_folder)
        self.seed.valueChanged.connect(self.on_design_changed)
        self.seed_button.clicked.connect(self.roll_seed)
        self.intricacy.valueChanged.connect(self.on_design_changed)
        self.open_button = QPushButton("Open artwork...")
        self.open_button.clicked.connect(self.open_source)
        self.path_label = QLabel("(none)")
        self.path_label.setWordWrap(True)
        form.addRow(self.open_button)
        form.addRow(self.path_label)
        self.source_size = QDoubleSpinBox()
        # No practical cap: the fit radius is what keeps the plot on the bed, so
        # the source may be any size and is scaled to the frame afterwards.
        self.source_size.setRange(0.1, 1000000.0)
        self.source_size.setValue(300.0)
        self.source_size.setSuffix(" mm")
        self.source_size.setToolTip(
            "Longest side of the source (or the pattern radius in random mode). "
            "Any size: the design is fitted to the Fit radius before plotting."
        )
        self.source_size.valueChanged.connect(self.on_controls_changed)
        form.addRow("Source size", self.source_size)
        self.center_x = QDoubleSpinBox()
        self.center_y = QDoubleSpinBox()
        for widget in (self.center_x, self.center_y):
            widget.setRange(-100000.0, 100000.0)
            widget.setDecimals(1)
            widget.setSuffix(" mm")
            widget.valueChanged.connect(self.on_offset_changed)
        centre_row = QHBoxLayout()
        centre_row.addWidget(self.center_x)
        centre_row.addWidget(self.center_y)
        form.addRow("Image offset X/Y", centre_row)
        hint = QLabel("Drag the preview or type millimetres of the finished design.")
        hint.setWordWrap(True)
        form.addRow(hint)
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0.05, 0.95)
        self.threshold.setSingleStep(0.05)
        self.threshold.setValue(0.5)
        self.threshold.valueChanged.connect(self.on_controls_changed)
        self.invert = QCheckBox("Treat light pixels as ink")
        self.invert.toggled.connect(self.on_controls_changed)
        self.trace_detail = QDoubleSpinBox()
        self.trace_detail.setRange(0.1, 6.0)
        self.trace_detail.setValue(1.0)
        self.trace_detail.setSuffix(" px")
        self.trace_detail.valueChanged.connect(self.on_controls_changed)
        form.addRow("Image threshold", self.threshold)
        form.addRow(self.invert)
        form.addRow("Trace detail", self.trace_detail)
        self.source_size.setToolTip(
            "Artwork: the longest side in millimetres. Random pattern: the outer radius."
        )
        self._update_source_mode()
        return box

    def _design_group(self):
        box = QGroupBox("Kaleidoscope")
        form = QFormLayout(box)
        self.divisions = QSpinBox()
        self.divisions.setRange(2, 64)
        self.divisions.setValue(12)
        self.divisions.valueChanged.connect(self.on_design_changed)
        self.mirror = QCheckBox("Mirror alternate sectors")
        self.mirror.setChecked(True)
        self.mirror.toggled.connect(self.on_design_changed)
        self.rotation = QDoubleSpinBox()
        self.rotation.setRange(-360.0, 360.0)
        self.rotation.setValue(0.0)
        self.rotation.setSuffix(" deg")
        self.rotation.valueChanged.connect(self.on_design_changed)
        self.show_wedge = QCheckBox("Show sampled wedge")
        self.show_wedge.setChecked(True)
        self.show_wedge.toggled.connect(self.on_preview_toggle)
        form.addRow("Divisions", self.divisions)
        form.addRow(self.mirror)
        form.addRow("Rotate source", self.rotation)
        form.addRow(self.show_wedge)
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.setFixedWidth(28)
        self.zoom_out_button.setToolTip("Zoom the preview out (Ctrl+-).")
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.setFixedWidth(28)
        self.zoom_in_button.setToolTip("Zoom the preview in (Ctrl++).")
        self.reset_view_button = QPushButton("Reset view")
        self.reset_view_button.setToolTip("Back to the whole bed (Ctrl+0).")
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(46)
        view_row = QHBoxLayout()
        view_row.addWidget(self.zoom_out_button)
        view_row.addWidget(self.zoom_in_button)
        view_row.addWidget(self.reset_view_button)
        view_row.addWidget(self.zoom_label)
        form.addRow("Preview view", view_row)
        return box

    def _bounds_group(self):
        box = QGroupBox("Printable bounds")
        form = QFormLayout(box)
        self.bed_diameter = QDoubleSpinBox()
        self.bed_diameter.setRange(10.0, 100000.0)
        self.bed_diameter.setValue(457.2)
        self.bed_diameter.setSuffix(" mm")
        self.bed_margin = QDoubleSpinBox()
        self.bed_margin.setRange(0.0, 10000.0)
        self.bed_margin.setValue(6.35)
        self.bed_margin.setSuffix(" mm")
        self.reach_radius = QDoubleSpinBox()
        self.reach_radius.setRange(1.0, 100000.0)
        self.reach_radius.setValue(185.0)
        self.reach_radius.setSuffix(" mm")
        self.fit_radius = QDoubleSpinBox()
        self.fit_radius.setRange(0.5, 100000.0)
        self.fit_radius.setValue(181.3)
        self.fit_radius.setSuffix(" mm")
        self.fit_radius.setToolTip(
            "Radius the design is fitted to and clipped at. Default 181.3 = 0.98 x the 185 mm reach."
        )
        self.auto_fit = QCheckBox("Auto-fit after a division or rotation change")
        self.auto_fit.setChecked(True)
        self.auto_fit.setToolTip(
            "Scale the design to the Fit radius while you work without "
            "overwriting the Source size you typed. "
            "Fit design to bounds is the button that writes the fitted size "
            "into Source size."
        )
        self.fit_button = QPushButton("Fit design to bounds")
        self.fit_button.clicked.connect(self.fit_to_bounds)
        self.bounds_note = QLabel("")
        self.bounds_note.setWordWrap(True)
        for widget in (
            self.bed_diameter,
            self.bed_margin,
            self.reach_radius,
            self.fit_radius,
        ):
            widget.valueChanged.connect(self.on_bounds_changed)
        form.addRow("Bed diameter", self.bed_diameter)
        form.addRow("Bed margin", self.bed_margin)
        form.addRow("Gantry reach radius", self.reach_radius)
        form.addRow("Fit radius", self.fit_radius)
        form.addRow(self.fit_button)
        form.addRow(self.auto_fit)
        form.addRow(self.bounds_note)
        self.update_bounds_note()
        return box

    def _output_group(self):
        box = QGroupBox("Output")
        form = QFormLayout(box)
        self.tolerance = QDoubleSpinBox()
        self.tolerance.setRange(0.05, 5.0)
        self.tolerance.setSingleStep(0.05)
        self.tolerance.setValue(0.25)
        self.tolerance.setSuffix(" mm")
        self.tolerance.valueChanged.connect(self.on_controls_changed)
        self.fill_spacing = QDoubleSpinBox()
        self.fill_spacing.setRange(0.0, 20.0)
        self.fill_spacing.setSingleStep(0.25)
        self.fill_spacing.setValue(0.0)
        self.fill_spacing.setSuffix(" mm")
        self.fill_spacing.setToolTip("0 = outlines only. A coarse spacing leaves short fragments inside small shapes.")
        self.fill_spacing.valueChanged.connect(self.on_controls_changed)
        self.feed_rate = QDoubleSpinBox()
        self.feed_rate.setRange(50.0, 6000.0)
        self.feed_rate.setValue(700.0)
        self.feed_rate.setSuffix(" mm/min")
        self.feed_rate.valueChanged.connect(self.on_controls_changed)
        self.theta_speed = QDoubleSpinBox()
        self.theta_speed.setRange(50.0, 6000.0)
        self.theta_speed.setValue(700.0)
        self.theta_speed.setSuffix(" mm/min")
        self.theta_speed.valueChanged.connect(self.on_controls_changed)
        self.build_button = QPushButton("Build preview")
        self.build_button.clicked.connect(self.rebuild)
        self.save_button = QPushButton("Save G-code...")
        self.save_button.clicked.connect(self.save_gcode)
        self.save_button.setEnabled(False)
        form.addRow("Tolerance", self.tolerance)
        form.addRow("Fill spacing", self.fill_spacing)
        form.addRow("Feed rate", self.feed_rate)
        form.addRow("Theta tangential speed", self.theta_speed)
        form.addRow(self.build_button)
        form.addRow(self.save_button)
        return box

    # -- behaviour -------------------------------------------------------

    def say(self, message):
        self.log.appendPlainText(message)

    # -- remembered settings ----------------------------------------------

    def settings_path(self):
        if self._settings_file:
            return Path(self._settings_file)
        return Path(__file__).resolve().parent / "kaleidoscope_settings.json"

    def default_motif_folder(self):
        """Where the motif button points before the operator picks a folder.

        The repo's scratch PNG folder wins when it exists - it is where the
        owner keeps the images they actually plot - otherwise the shipped set.
        """
        root = Path(__file__).resolve().parents[1]
        scratch = root / "samples" / "png"
        if scratch.is_dir():
            return str(scratch)
        shipped = root / "motifs" / "nature"
        if shipped.is_dir():
            return str(shipped)
        return ""

    def apply_settings(self):
        """Restore the last session before the first build."""
        try:
            data = json.loads(self.settings_path().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        numbers = (
            ("seed", self.seed, int),
            ("intricacy", self.intricacy, int),
            ("divisions", self.divisions, int),
            ("source_size", self.source_size, float),
            ("center_x", self.center_x, float),
            ("center_y", self.center_y, float),
            ("threshold", self.threshold, float),
            ("trace_detail", self.trace_detail, float),
            ("rotation", self.rotation, float),
            ("bed_diameter", self.bed_diameter, float),
            ("bed_margin", self.bed_margin, float),
            ("reach_radius", self.reach_radius, float),
            ("fit_radius", self.fit_radius, float),
            ("tolerance", self.tolerance, float),
            ("fill_spacing", self.fill_spacing, float),
            ("feed_rate", self.feed_rate, float),
            ("theta_speed", self.theta_speed, float),
        )
        for key, widget, cast in numbers:
            if key not in data:
                continue
            try:
                widget.setValue(cast(data[key]))
            except (TypeError, ValueError):
                pass
        toggles = (
            ("mirror", self.mirror),
            ("show_wedge", self.show_wedge),
            ("invert", self.invert),
            ("auto_fit", self.auto_fit),
            ("use_motifs", self.use_motifs),
            ("random_mode", self.random_mode),
        )
        for key, widget in toggles:
            if key in data:
                widget.setChecked(bool(data[key]))

        folder = data.get("motif_folder") or self.default_motif_folder()
        loaded = False
        if folder:
            loaded = self.load_motif_folder(folder, announce=False)
        # First run with a motif folder: come up ready to pattern with it
        # instead of making the operator set the same two ticks every launch.
        if loaded and "use_motifs" not in data:
            self.use_motifs.setChecked(True)
        if loaded and "random_mode" not in data:
            self.random_mode.setChecked(True)
        source = data.get("source_path", "")
        if source and Path(source).is_file():
            self.source_path = source
            self.path_label.setText(os.path.basename(source))

    def save_settings(self):
        data = {
            "motif_folder": self.motif_folder,
            "source_path": self.source_path,
            "seed": int(self.seed.value()),
            "intricacy": int(self.intricacy.value()),
            "divisions": int(self.divisions.value()),
            "source_size": float(self.source_size.value()),
            "center_x": float(self.center_x.value()),
            "center_y": float(self.center_y.value()),
            "threshold": float(self.threshold.value()),
            "trace_detail": float(self.trace_detail.value()),
            "rotation": float(self.rotation.value()),
            "bed_diameter": float(self.bed_diameter.value()),
            "bed_margin": float(self.bed_margin.value()),
            "reach_radius": float(self.reach_radius.value()),
            "fit_radius": float(self.fit_radius.value()),
            "tolerance": float(self.tolerance.value()),
            "fill_spacing": float(self.fill_spacing.value()),
            "feed_rate": float(self.feed_rate.value()),
            "theta_speed": float(self.theta_speed.value()),
            "mirror": self.mirror.isChecked(),
            "show_wedge": self.show_wedge.isChecked(),
            "invert": self.invert.isChecked(),
            "auto_fit": self.auto_fit.isChecked(),
            "use_motifs": self.use_motifs.isChecked(),
            "random_mode": self.random_mode.isChecked(),
        }
        try:
            self.settings_path().write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            self.say("Could not save settings: %s" % exc)

    def closeEvent(self, event):  # noqa: N802 - Qt naming
        self.save_settings()
        super().closeEvent(event)

    def on_view_changed(self, zoom):
        self.zoom_label.setText("%.0f%%" % (float(zoom) * 100.0))

    def keyPressEvent(self, event):  # noqa: N802 - Qt naming
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_0:
                self.preview.reset_view()
                event.accept()
                return
            if event.key() in (Qt.Key_Plus, Qt.Key_Equal):
                self.preview.zoom_in()
                event.accept()
                return
            if event.key() == Qt.Key_Minus:
                self.preview.zoom_out()
                event.accept()
                return
        super().keyPressEvent(event)

    def _has_source(self):
        return self.random_mode.isChecked() or bool(self.source_path)

    def _update_source_mode(self):
        generated = self.random_mode.isChecked()
        motifs_on = generated and self.use_motifs.isChecked()
        self.open_button.setEnabled(not generated)
        for widget in (self.threshold, self.invert, self.trace_detail):
            widget.setEnabled(not generated or motifs_on)
        for widget in (self.seed, self.seed_button, self.intricacy, self.use_motifs):
            widget.setEnabled(generated)
        if generated:
            seed = int(self.seed.value())
            label = "seed %d, intricacy %d (%s)" % (
                seed,
                int(self.intricacy.value()),
                converter.style_for(seed),
            )
            if motifs_on:
                label += " + %d motifs" % len(self.motif_paths)
        elif self.source_path:
            label = os.path.basename(self.source_path)
        else:
            label = "(none)"
        self.path_label.setText(label)

    def on_source_mode_changed(self, _checked=False):
        self._update_source_mode()
        if self._in_rebuild or getattr(self, "_loading", False):
            return
        if self._has_source():
            self.rebuild()
        else:
            self.save_button.setEnabled(False)

    def roll_seed(self):
        self.seed.setValue(random.SystemRandom().randrange(0, 100000))

    def choose_motif_folder(self):
        start = self.motif_folder or self.default_motif_folder()
        folder = QFileDialog.getExistingDirectory(
            self, "Choose a motif folder", start
        )
        if not folder:
            return
        self.load_motif_folder(folder)

    def load_motif_folder(self, folder, announce=True):
        """Point the motif mode at *folder*; remember it for next launch."""
        paths = sorted(
            str(path)
            for path in Path(folder).iterdir()
            if path.is_file() and converter.is_raster_source(path)
        )
        if not paths:
            if announce:
                QMessageBox.information(
                    self, "No motifs", "That folder has no PNG or JPG images."
                )
            return False
        self.motif_folder = str(folder)
        self.motif_paths = paths
        self.motif_cache = {}
        names = ", ".join(os.path.basename(path) for path in paths[:3])
        self.motif_label.setText(
            "%d file%s: %s%s"
            % (len(paths), "" if len(paths) == 1 else "s", names, ", ..." if len(paths) > 3 else "")
        )
        self.motif_label.setToolTip(str(folder))
        if not announce:
            return True
        self.use_motifs.setChecked(True)
        self.say("Loaded %d motif images from %s." % (len(paths), folder))
        self._update_source_mode()
        self.save_settings()
        if self._has_source() and not self._in_rebuild:
            self.rebuild()
        return True

    def _motif(self, index):
        """Traced, centred, unit-sized contours for one motif image."""
        path = self.motif_paths[index]
        try:
            stamp = os.path.getmtime(path)
        except OSError:
            stamp = 0.0
        key = (
            path,
            stamp,
            round(float(self.threshold.value()), 4),
            self.invert.isChecked(),
            round(float(self.trace_detail.value()), 4),
        )
        if key not in self.motif_cache:
            traced = converter.trace_raster(
                path,
                max_side=512,
                threshold=float(self.threshold.value()),
                invert=self.invert.isChecked(),
                tolerance=float(self.trace_detail.value()),
            )
            contours = (
                converter.normalize_source(traced, 1.0, flip_y=True)[0]
                if traced
                else []
            )
            points = sum(len(contour) for contour in contours)
            if len(contours) > 200 or points > 4000:
                # A motif has to be one shape. A whole drawing in the folder
                # would otherwise tile into hundreds of thousands of contours.
                self.say(
                    "Skipped %s as a motif: %d contours / %d points is artwork, "
                    "not a single shape."
                    % (os.path.basename(path), len(contours), points)
                )
                contours = []
            self.motif_cache[key] = contours
        return self.motif_cache[key]

    def _motifs(self):
        """One traced motif per file, or None when the mode is off.

        Only the motifs the current seed will place are traced, so a large
        folder does not pay for images the design never uses.
        """
        if not (
            self.random_mode.isChecked()
            and self.use_motifs.isChecked()
            and self.motif_paths
        ):
            return None
        plan = converter.motif_plan(
            int(self.seed.value()), int(self.intricacy.value()), len(self.motif_paths)
        )
        wanted = {index for pool in plan for index in pool}
        return [
            self._motif(index) if index in wanted else None
            for index in range(len(self.motif_paths))
        ]

    def on_preview_toggle(self, checked):
        self.preview.show_wedge = bool(checked)
        self.preview.update()

    def on_controls_changed(self, *_args):
        self.save_button.setEnabled(False)
        if self._in_rebuild or getattr(self, "_loading", False):
            return
        if self._has_source():
            self.rebuild(refit=False)

    def on_design_changed(self, *_args):
        self.save_button.setEnabled(False)
        if self._in_rebuild or getattr(self, "_loading", False):
            return
        self._update_source_mode()
        if self._has_source():
            self.rebuild()

    def on_offset_changed(self, *_args):
        self.save_button.setEnabled(False)
        if self._in_rebuild or getattr(self, "_loading", False):
            return
        if self._has_source():
            self.rebuild(refit=False)

    def on_bounds_changed(self, *_args):
        self.update_bounds_note()
        self.save_button.setEnabled(False)
        if self._in_rebuild or getattr(self, "_loading", False):
            return
        if self._has_source():
            # With auto-fit on, following the fit radius is what the operator
            # expects; the typed numbers still stay put either way.
            self.rebuild(refit=self.auto_fit.isChecked())

    def update_bounds_note(self):
        bed = max(
            float(self.bed_diameter.value()) / 2.0 - float(self.bed_margin.value()),
            0.0,
        )
        reach = float(self.reach_radius.value())
        note = (
            "Bed allows %.1f mm from centre and the reach circle allows %.1f mm. "
            "The design is fitted to, and clipped at, the Fit radius."
            % (bed, reach)
        )
        if abs(self.fit_scale - 1.0) > 1e-4:
            note += " Auto-fit is scaling the drawing by %.3f; Source size stays at %.1f mm." % (
                self.fit_scale,
                float(self.source_size.value()),
            )
        self.bounds_note.setText(note)

    def open_source(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open artwork", "", SOURCE_FILTER)
        if not path:
            return
        if self.random_mode.isChecked():
            self._in_rebuild = True
            try:
                self.random_mode.setChecked(False)
            finally:
                self._in_rebuild = False
            self._update_source_mode()
        self.source_path = path
        self.path_label.setText(os.path.basename(path))
        self.say(
            "Loaded %s (%s source)."
            % (os.path.basename(path), "raster" if converter.is_raster_source(path) else "SVG")
        )
        self.rebuild()

    def output_settings(self):
        base = converter.Settings()
        return dataclasses.replace(
            base,
            tolerance=float(self.tolerance.value()),
            hatch_spacing_mm=float(self.fill_spacing.value()),
            feed_rate=float(self.feed_rate.value()),
            theta_tangential_speed_mm_min=float(self.theta_speed.value()),
            bed_diameter_mm=float(self.bed_diameter.value()),
            bed_margin_mm=float(self.bed_margin.value()),
            machine_reach_radius_mm=float(self.reach_radius.value()),
            fit_mode="manual",
            scale=1.0,
            flip_y=False,
        )

    def _image_offset(self):
        return float(self.center_x.value()), float(self.center_y.value())

    def _source_contours(self, settings, size_mm):
        """Centred source in design millimetres, y up, with the image offset applied."""
        path = self.source_path
        size_mm = max(float(size_mm), 1.0)
        if self.random_mode.isChecked():
            contours = converter.random_pattern(
                seed=int(self.seed.value()),
                intricacy=int(self.intricacy.value()),
                radius_mm=size_mm,
                wedge_deg=180.0 / max(int(self.divisions.value()), 1),
                motifs=self._motifs(),
            )
        elif converter.is_raster_source(path):
            traced = converter.trace_raster(
                path,
                max_side=900,
                threshold=float(self.threshold.value()),
                invert=self.invert.isChecked(),
                tolerance=float(self.trace_detail.value()),
            )
            if not traced:
                raise ValueError("Nothing dark enough to trace - lower the threshold or invert it.")
            contours = converter.normalize_source(traced, size_mm, flip_y=True)[0]
        else:
            probe = dataclasses.replace(
                settings, scale=1.0, hatch_spacing_mm=0.0, fit_mode="manual", flip_y=False
            )
            raw = converter.read_svg(path, probe)
            if not raw:
                raise ValueError("The SVG has no drawable geometry.")
            min_x, min_y, max_x, max_y = converter.contour_bounds(raw)
            base_x = (min_x + max_x) / 2.0
            base_y = (min_y + max_y) / 2.0
            span = max(max_x - min_x, max_y - min_y, 1e-9)
            scale = size_mm / span
            fitted = dataclasses.replace(settings, scale=scale, fit_mode="manual", flip_y=False)
            scaled = converter.read_svg(path, fitted)
            contours = [
                [(x - base_x * scale, -(y - base_y * scale)) for x, y in contour]
                for contour in scaled
            ]
        offset_x, offset_y = self._image_offset()
        if abs(offset_x) > 1e-9 or abs(offset_y) > 1e-9:
            contours = [
                [(x + offset_x, y + offset_y) for x, y in contour]
                for contour in contours
            ]
        return contours

    def _build(self, settings, size_mm, clip_radius):
        source = self._source_contours(settings, size_mm)
        return converter.kaleidoscope(
            source,
            divisions=int(self.divisions.value()),
            mirror=self.mirror.isChecked(),
            angle_offset_deg=float(self.rotation.value()),
            radius=clip_radius,
        )

    def build_design(self, size_mm=None, clip_radius=None):
        if not self._has_source():
            raise ValueError("Open an artwork or switch on the random pattern first.")
        settings = self.output_settings()
        size = float(self.source_size.value()) if size_mm is None else float(size_mm)
        return settings, self._build(settings, size, clip_radius)

    def rebuild(self, refit=None):
        if not self._has_source():
            return
        if refit is None:
            refit = self.auto_fit.isChecked()
        self._in_rebuild = True
        try:
            target = max(float(self.fit_radius.value()), 1.0)
            size = float(self.source_size.value())
            self.fit_scale = 1.0
            if refit:
                _, natural = self.build_design(size, clip_radius=None)
                radius = max(
                    (math.hypot(x, y) for contour in natural for x, y in contour),
                    default=0.0,
                )
                if radius > 0.0:
                    # Auto-fit only scales the design for this build. Writing
                    # the fitted size back into the spin box is what used to
                    # wipe out a typed Source size whenever the seed, the
                    # intricacy or the divisions changed.
                    self.fit_scale = target / radius
                    size = max(size * self.fit_scale, self.source_size.minimum())
            settings, design = self.build_design(size, clip_radius=target)
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            self.say("Build failed: %s" % exc)
            return
        finally:
            self._in_rebuild = False
        self.design = design
        self.settings = settings
        self.preview.reach_radius = float(settings.machine_reach_radius_mm)
        self.preview.bed_radius = float(settings.bed_diameter_mm) / 2.0
        self.preview.bounds_radius = target
        wedge = 180.0 / max(int(self.divisions.value()), 1)
        self.preview.set_design(design, wedge)
        radius = max((math.hypot(x, y) for contour in design for x, y in contour), default=0.0)
        self.save_button.setEnabled(bool(design))
        offset_x, offset_y = self._image_offset()
        if self.random_mode.isChecked():
            seed = int(self.seed.value())
            source = "random pattern, seed %d, intricacy %d, %s style" % (
                seed,
                int(self.intricacy.value()),
                converter.style_for(seed),
            )
            if self.use_motifs.isChecked() and self.motif_paths:
                source += ", %d motifs" % len(self.motif_paths)
        else:
            source = os.path.basename(self.source_path)
        self.say(
            "Design (%s): %d divisions%s, %d contours, outer radius %.1f mm of the %.1f mm bound "
            "(reach %.1f mm, image offset %.1f, %.1f)."
            % (
                source,
                int(self.divisions.value()),
                " mirrored" if self.mirror.isChecked() else "",
                len(design),
                radius,
                target,
                float(settings.machine_reach_radius_mm),
                offset_x,
                offset_y,
            )
        )
        if abs(self.fit_scale - 1.0) > 1e-4:
            self.say(
                "Auto-fit: scaled the drawing by %.3f for this build; Source size "
                "stays at %.1f mm. Press Fit design to bounds to bake the fitted "
                "size into the number."
                % (self.fit_scale, float(self.source_size.value()))
            )
        self.update_bounds_note()
        if target > float(settings.machine_reach_radius_mm):
            self.say(
                "Fit radius exceeds the reach circle; the planner will clip the program at %.1f mm."
                % float(settings.machine_reach_radius_mm)
            )

    def fit_to_bounds(self):
        if not self._has_source():
            return
        try:
            target = max(float(self.fit_radius.value()), 1.0)
            size = float(self.source_size.value())
            _, natural = self.build_design(size, clip_radius=None)
            radius = max(
                (math.hypot(x, y) for contour in natural for x, y in contour),
                default=0.0,
            )
        except Exception as exc:  # noqa: BLE001
            self.say("Fit failed: %s" % exc)
            return
        if radius <= 0.0:
            return
        self._in_rebuild = True
        try:
            self.source_size.setValue(
                max(size * target / radius, self.source_size.minimum())
            )
        finally:
            self._in_rebuild = False
        self.rebuild(refit=False)

    def on_image_dragged(self, dx, dy):
        """Move the source image inside the fixed design frame."""
        if not self._has_source() or self._in_rebuild:
            return
        self._in_rebuild = True
        try:
            self.center_x.setValue(float(self.center_x.value()) + float(dx))
            self.center_y.setValue(float(self.center_y.value()) + float(dy))
        finally:
            self._in_rebuild = False
        self.rebuild(refit=False)

    def save_gcode(self):
        if not self.design:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save G-code", "kaleidoscope.gcode", "G-code (*.gcode *.nc *.tap);;All files (*.*)"
        )
        if not path:
            return
        try:
            settings = self.settings
            plan = converter.plan_program(self.design, settings)
            gcode = converter.contours_to_gcode(self.design, settings, plan)
            Path(path).write_text(gcode, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))
            self.say("Save failed: %s" % exc)
            return
        blocks = gcode.count("\nM3")
        self.say("Saved %s: %d lines, %d pen cycles." % (os.path.basename(path), gcode.count("\n") + 1, blocks))


def main():
    app = QApplication(sys.argv)
    window = KaleidoscopeWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
