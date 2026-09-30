"""Kaleidoscope Converter - import or generate artwork, mirror it, save G-code.

This is a focused sibling of `qt_svg_to_gcode.pyw`. It reuses the converter
core wholesale: `converter_core.kaleidoscope` builds the mirrored design and the
existing planner, polar kinematics and emitter produce the program, while
`converter_core.generative` can draw the source as a sequence-driven mandala.
Only the source handling, the design controls and a flat bed-frame preview are
new.
"""

import dataclasses
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

    def __init__(self):
        super().__init__()
        self.contours = []
        self.bed_radius = 457.2 / 2.0
        self.reach_radius = 185.0
        self.bounds_radius = 181.3
        self.wedge_deg = 15.0
        self.show_wedge = True
        self._drag_from = None
        self.setMinimumSize(360, 360)

    def set_design(self, contours, wedge_deg):
        self.contours = contours
        self.wedge_deg = float(wedge_deg)
        self.update()

    # -- dragging moves the source image inside the fixed design frame -----

    def mousePressEvent(self, event):  # noqa: N802 - Qt naming
        if event.button() == Qt.LeftButton:
            self._drag_from = event.position()

    def mouseMoveEvent(self, event):  # noqa: N802 - Qt naming
        if self._drag_from is None:
            return
        position = event.position()
        scale = self._scale()
        self.dragged.emit(
            (position.x() - self._drag_from.x()) / scale,
            -(position.y() - self._drag_from.y()) / scale,
        )
        self._drag_from = position

    def mouseReleaseEvent(self, event):  # noqa: N802 - Qt naming
        self._drag_from = None

    def _scale(self):
        half = max(self.bed_radius, 1.0)
        return min(self.width(), self.height()) * 0.48 / half

    def paintEvent(self, event):  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        scale = self._scale()
        cx, cy = self.width() / 2.0, self.height() / 2.0

        def to_screen(point):
            return QPointF(cx + point[0] * scale, cy - point[1] * scale)

        bed = QRectF(
            cx - self.bed_radius * scale,
            cy - self.bed_radius * scale,
            self.bed_radius * scale * 2.0,
            self.bed_radius * scale * 2.0,
        )
        painter.setPen(QPen(QColor(205, 205, 205), 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(bed)
        painter.setPen(QPen(QColor(230, 180, 120), 1.2, Qt.DashLine))
        painter.drawEllipse(
            QRectF(
                cx - self.reach_radius * scale,
                cy - self.reach_radius * scale,
                self.reach_radius * scale * 2.0,
                self.reach_radius * scale * 2.0,
            )
        )
        painter.setPen(QPen(QColor(120, 160, 220), 1.4, Qt.DashLine))
        painter.drawEllipse(
            QRectF(
                cx - self.bounds_radius * scale,
                cy - self.bounds_radius * scale,
                self.bounds_radius * scale * 2.0,
                self.bounds_radius * scale * 2.0,
            )
        )
        if self.show_wedge:
            painter.setPen(QPen(QColor(170, 200, 240), 1.0, Qt.DashLine))
            reach = self.reach_radius
            for angle in (0.0, self.wedge_deg):
                radians = math.radians(angle)
                painter.drawLine(
                    to_screen((0.0, 0.0)),
                    to_screen((reach * math.cos(radians), reach * math.sin(radians))),
                )
        painter.setPen(QPen(QColor(30, 30, 30), 0.9))
        for contour in self.contours:
            if len(contour) < 2:
                continue
            painter.drawPolyline([to_screen(point) for point in contour])
        painter.setPen(QPen(QColor(120, 120, 120), 1.0))
        painter.setFont(QFont(painter.font().family(), 8))
        painter.drawText(
            8,
            self.height() - 8,
            "design contours: %d   bed %.0f mm   reach %.0f mm   design bound %.1f mm   "
            "drag to move the image inside the frame"
            % (
                len(self.contours),
                self.bed_radius * 2.0,
                self.reach_radius,
                self.bounds_radius,
            ),
        )


class KaleidoscopeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kaleidoscope Converter")
        self.source_path = ""
        self.design = []

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
        self._in_rebuild = False
        self.resize(1100, 720)
        self.say(
            "Open an SVG, PNG or JPG - or tick Generate a random pattern - "
            "set the divisions, then Build preview."
        )

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
        self.source_size.setRange(10.0, 400.0)
        self.source_size.setValue(300.0)
        self.source_size.setSuffix(" mm")
        self.source_size.valueChanged.connect(self.on_controls_changed)
        form.addRow("Source size", self.source_size)
        self.center_x = QDoubleSpinBox()
        self.center_y = QDoubleSpinBox()
        for widget in (self.center_x, self.center_y):
            widget.setRange(-500.0, 500.0)
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
        return box

    def _bounds_group(self):
        box = QGroupBox("Printable bounds")
        form = QFormLayout(box)
        self.bed_diameter = QDoubleSpinBox()
        self.bed_diameter.setRange(100.0, 1000.0)
        self.bed_diameter.setValue(457.2)
        self.bed_diameter.setSuffix(" mm")
        self.bed_margin = QDoubleSpinBox()
        self.bed_margin.setRange(0.0, 100.0)
        self.bed_margin.setValue(6.35)
        self.bed_margin.setSuffix(" mm")
        self.reach_radius = QDoubleSpinBox()
        self.reach_radius.setRange(10.0, 300.0)
        self.reach_radius.setValue(185.0)
        self.reach_radius.setSuffix(" mm")
        self.fit_radius = QDoubleSpinBox()
        self.fit_radius.setRange(5.0, 300.0)
        self.fit_radius.setValue(181.3)
        self.fit_radius.setSuffix(" mm")
        self.fit_radius.setToolTip(
            "Radius the design is fitted to and clipped at. Default 181.3 = 0.98 x the 185 mm reach."
        )
        self.auto_fit = QCheckBox("Auto-fit after a division or rotation change")
        self.auto_fit.setChecked(True)
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

    def _has_source(self):
        return self.random_mode.isChecked() or bool(self.source_path)

    def _update_source_mode(self):
        generated = self.random_mode.isChecked()
        for widget in (self.open_button, self.threshold, self.invert, self.trace_detail):
            widget.setEnabled(not generated)
        for widget in (self.seed, self.seed_button, self.intricacy):
            widget.setEnabled(generated)
        if generated:
            label = "seed %d, intricacy %d" % (
                int(self.seed.value()),
                int(self.intricacy.value()),
            )
        elif self.source_path:
            label = os.path.basename(self.source_path)
        else:
            label = "(none)"
        self.path_label.setText(label)

    def on_source_mode_changed(self, _checked=False):
        self._update_source_mode()
        if self._in_rebuild:
            return
        if self._has_source():
            self.rebuild()
        else:
            self.save_button.setEnabled(False)

    def roll_seed(self):
        self.seed.setValue(random.SystemRandom().randrange(0, 100000))

    def on_preview_toggle(self, checked):
        self.preview.show_wedge = bool(checked)
        self.preview.update()

    def on_controls_changed(self, *_args):
        self.save_button.setEnabled(False)
        if self._in_rebuild:
            return
        if self._has_source():
            self.rebuild(refit=False)

    def on_design_changed(self, *_args):
        self.save_button.setEnabled(False)
        if self._in_rebuild:
            return
        self._update_source_mode()
        if self._has_source():
            self.rebuild()

    def on_offset_changed(self, *_args):
        self.save_button.setEnabled(False)
        if self._in_rebuild:
            return
        if self._has_source():
            self.rebuild(refit=False)

    def on_bounds_changed(self, *_args):
        self.update_bounds_note()
        self.save_button.setEnabled(False)
        if self._in_rebuild:
            return
        if self._has_source():
            self.rebuild(refit=False)

    def update_bounds_note(self):
        bed = max(
            float(self.bed_diameter.value()) / 2.0 - float(self.bed_margin.value()),
            0.0,
        )
        reach = float(self.reach_radius.value())
        self.bounds_note.setText(
            "Bed allows %.1f mm from centre and the reach circle allows %.1f mm. "
            "The design is fitted to, and clipped at, the Fit radius."
            % (bed, reach)
        )

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
            if refit:
                _, natural = self.build_design(size, clip_radius=None)
                radius = max(
                    (math.hypot(x, y) for contour in natural for x, y in contour),
                    default=0.0,
                )
                if radius > 0.0:
                    size = min(max(size * target / radius, 10.0), 400.0)
                    self.source_size.setValue(size)
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
            source = "random pattern, seed %d, intricacy %d" % (
                int(self.seed.value()),
                int(self.intricacy.value()),
            )
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
            self.source_size.setValue(min(max(size * target / radius, 10.0), 400.0))
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
