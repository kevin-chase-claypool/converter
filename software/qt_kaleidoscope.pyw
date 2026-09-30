"""Kaleidoscope Converter - import an image, mirror it into N sectors, save G-code.

This is a focused sibling of `qt_svg_to_gcode.pyw`. It reuses the converter
core wholesale: `converter_core.kaleidoscope` builds the mirrored design and the
existing planner, polar kinematics and emitter produce the program. Only the
source handling, the design controls and a flat bed-frame preview are new.
"""

import dataclasses
import math
import os
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
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

    def __init__(self):
        super().__init__()
        self.contours = []
        self.bed_radius = 457.2 / 2.0
        self.reach_radius = 185.0
        self.wedge_deg = 15.0
        self.show_wedge = True
        self.setMinimumSize(360, 360)

    def set_design(self, contours, wedge_deg):
        self.contours = contours
        self.wedge_deg = float(wedge_deg)
        self.update()

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
            f"design contours: {len(self.contours)}   bed {self.bed_radius * 2:.0f} mm   reach {self.reach_radius:.0f} mm",
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
        panel_layout.addWidget(self._output_group())
        panel_layout.addStretch(1)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.addWidget(panel)
        layout.addWidget(right, 1)
        self.setCentralWidget(central)
        self.resize(1100, 720)
        self.say("Open an SVG, PNG or JPG, set the divisions, then Build preview.")

    # -- UI construction -------------------------------------------------

    def _source_group(self):
        box = QGroupBox("Source")
        form = QFormLayout(box)
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
            widget.valueChanged.connect(self.on_controls_changed)
        centre_row = QHBoxLayout()
        centre_row.addWidget(self.center_x)
        centre_row.addWidget(self.center_y)
        form.addRow("Apex offset X/Y", centre_row)
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
        return box

    def _design_group(self):
        box = QGroupBox("Kaleidoscope")
        form = QFormLayout(box)
        self.divisions = QSpinBox()
        self.divisions.setRange(2, 64)
        self.divisions.setValue(12)
        self.divisions.valueChanged.connect(self.on_controls_changed)
        self.mirror = QCheckBox("Mirror alternate sectors")
        self.mirror.setChecked(True)
        self.mirror.toggled.connect(self.on_controls_changed)
        self.rotation = QDoubleSpinBox()
        self.rotation.setRange(-360.0, 360.0)
        self.rotation.setValue(0.0)
        self.rotation.setSuffix(" deg")
        self.rotation.valueChanged.connect(self.on_controls_changed)
        self.show_wedge = QCheckBox("Show sampled wedge")
        self.show_wedge.setChecked(True)
        self.show_wedge.toggled.connect(self.on_preview_toggle)
        self.fit_button = QPushButton("Fit to reach circle")
        self.fit_button.clicked.connect(self.fit_to_reach)
        form.addRow("Divisions", self.divisions)
        form.addRow(self.mirror)
        form.addRow("Rotate source", self.rotation)
        form.addRow(self.fit_button)
        form.addRow(self.show_wedge)
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

    def on_preview_toggle(self, checked):
        self.preview.show_wedge = bool(checked)
        self.preview.update()

    def on_controls_changed(self, *_args):
        self.save_button.setEnabled(False)

    def open_source(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open artwork", "", SOURCE_FILTER)
        if not path:
            return
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
            fit_mode="manual",
            scale=1.0,
            flip_y=False,
        )

    def _center_override(self):
        x = float(self.center_x.value())
        y = float(self.center_y.value())
        return None if abs(x) < 1e-9 and abs(y) < 1e-9 else (x, y)

    def _source_contours(self, settings, size_mm):
        """Return the centred source in millimetres, y up, before repeating."""
        path = self.source_path
        center = self._center_override()
        size_mm = max(float(size_mm), 1.0)
        if converter.is_raster_source(path):
            traced = converter.trace_raster(
                path,
                max_side=900,
                threshold=float(self.threshold.value()),
                invert=self.invert.isChecked(),
                tolerance=float(self.trace_detail.value()),
            )
            if not traced:
                raise ValueError("Nothing dark enough to trace - lower the threshold or invert it.")
            return converter.normalize_source(traced, size_mm, center=center, flip_y=True)[0]
        probe = dataclasses.replace(
            settings, scale=1.0, hatch_spacing_mm=0.0, fit_mode="manual", flip_y=False
        )
        raw = converter.read_svg(path, probe)
        if not raw:
            raise ValueError("The SVG has no drawable geometry.")
        min_x, min_y, max_x, max_y = converter.contour_bounds(raw)
        base_x = (min_x + max_x) / 2.0 if center is None else float(center[0])
        base_y = (min_y + max_y) / 2.0 if center is None else float(center[1])
        span = max(max_x - min_x, max_y - min_y, 1e-9)
        scale = size_mm / span
        fitted = dataclasses.replace(settings, scale=scale, fit_mode="manual", flip_y=False)
        scaled = converter.read_svg(path, fitted)
        return [
            [(x - base_x * scale, -(y - base_y * scale)) for x, y in contour]
            for contour in scaled
        ]

    def build_design(self, size_mm=None):
        if not self.source_path:
            raise ValueError("Open an artwork first.")
        settings = self.output_settings()
        size = float(self.source_size.value()) if size_mm is None else float(size_mm)
        source = self._source_contours(settings, size)
        design = converter.kaleidoscope(
            source,
            divisions=int(self.divisions.value()),
            mirror=self.mirror.isChecked(),
            angle_offset_deg=float(self.rotation.value()),
        )
        return settings, design

    def rebuild(self):
        if not self.source_path:
            return
        try:
            settings, design = self.build_design()
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            self.say("Build failed: %s" % exc)
            return
        self.design = design
        self.settings = settings
        self.preview.reach_radius = float(settings.machine_reach_radius_mm)
        self.preview.bed_radius = float(settings.bed_diameter_mm) / 2.0
        wedge = 180.0 / max(int(self.divisions.value()), 1)
        self.preview.set_design(design, wedge)
        radius = max((math.hypot(x, y) for contour in design for x, y in contour), default=0.0)
        self.save_button.setEnabled(bool(design))
        self.say(
            "Design: %d divisions%s, %d contours, outer radius %.1f mm (reach %.1f mm)."
            % (
                int(self.divisions.value()),
                " mirrored" if self.mirror.isChecked() else "",
                len(design),
                radius,
                float(settings.machine_reach_radius_mm),
            )
        )
        if radius > float(settings.machine_reach_radius_mm):
            self.say(
                "Outer radius exceeds the reach circle - the planner will clip it. "
                "Use Fit to reach circle or lower Source size."
            )

    def fit_to_reach(self):
        if not self.source_path:
            return
        try:
            settings, design = self.build_design()
        except Exception as exc:  # noqa: BLE001
            self.say("Fit failed: %s" % exc)
            return
        radius = max((math.hypot(x, y) for contour in design for x, y in contour), default=0.0)
        reach = float(settings.machine_reach_radius_mm)
        if radius <= 0.0:
            return
        target = float(self.source_size.value()) * (reach * 0.98) / radius
        self.source_size.setValue(min(max(target, 10.0), 400.0))
        self.rebuild()

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
