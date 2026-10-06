"""Shared widgets and SVG output for generator tabs.

Every generator tab is a left control column plus a QPainter preview and one
action that hands a generated SVG to the Convert tab. This module owns that
scaffolding so the tabs only contain their own algorithm and parameters.
"""

from __future__ import annotations

import tempfile
import time
import uuid
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


OUTPUT_DIR = Path(tempfile.gettempdir()) / "theta_generator_tabs"


def _fmt(value: float) -> str:
    text = f"{value:.3f}"
    return text.rstrip("0").rstrip(".")


def polylines_to_svg(
    polylines,
    width_mm,
    height_mm,
    stroke_mm=0.3,
    background="#ffffff",
    extra_svg="",
):
    """Return an SVG document with one polyline per point sequence."""
    body = []
    for points in polylines:
        if len(points) < 2:
            continue
        pairs = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in points)
        body.append(f'<polyline points="{pairs}"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt(width_mm)}mm" '
        f'height="{_fmt(height_mm)}mm" viewBox="0 0 {_fmt(width_mm)} {_fmt(height_mm)}">\n'
        f'<rect x="0" y="0" width="{_fmt(width_mm)}" height="{_fmt(height_mm)}" '
        f'fill="{background}"/>\n'
        f'<g fill="none" stroke="#111111" stroke-width="{_fmt(stroke_mm)}" '
        'stroke-linecap="round" stroke-linejoin="round">\n'
        + "\n".join(body)
        + "\n</g>\n"
        + (extra_svg + "\n" if extra_svg else "")
        + "</svg>\n"
    )


def write_svg_document(name, document):
    """Write an SVG document to a unique temp path and return it."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = f"{int(time.time() * 1000):d}-{uuid.uuid4().hex[:6]}"
    path = OUTPUT_DIR / f"{name}-{stamp}.svg"
    path.write_text(document, encoding="utf-8")
    return path


def double_spin(value, low, high, step, decimals=2, suffix=""):
    widget = QDoubleSpinBox()
    widget.setRange(low, high)
    widget.setDecimals(decimals)
    widget.setSingleStep(step)
    widget.setValue(value)
    if suffix:
        widget.setSuffix(suffix)
    return widget


def int_spin(value, low, high, step=1):
    widget = QSpinBox()
    widget.setRange(low, high)
    widget.setSingleStep(step)
    widget.setValue(value)
    return widget


def file_picker(line_edit, on_pick, title, filters):
    button = QPushButton("Browse")

    def pick():
        path, _ = QFileDialog.getOpenFileName(None, title, "", filters)
        if path:
            line_edit.setText(path)
            on_pick(path)

    button.clicked.connect(pick)
    return button


class PreviewCanvas(QWidget):
    """Fits the generated page into the tab and draws its polylines."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(360, 300)
        self._polylines = []
        self._width_mm = 200.0
        self._height_mm = 200.0
        self._background = None
        self._color = QColor("#111111")

    def set_page(self, width_mm, height_mm, polylines, background=None, color=None):
        self._width_mm = max(1.0, float(width_mm))
        self._height_mm = max(1.0, float(height_mm))
        self._polylines = polylines
        self._background = background
        if color is not None:
            self._color = QColor(color)
        self.update()

    def clear(self):
        self._polylines = []
        self._background = None
        self.update()

    def _transform(self):
        margin = 12.0
        scale = min(
            (self.width() - 2 * margin) / self._width_mm,
            (self.height() - 2 * margin) / self._height_mm,
        )
        scale = max(scale, 0.01)
        offset_x = (self.width() - self._width_mm * scale) / 2.0
        offset_y = (self.height() - self._height_mm * scale) / 2.0
        return scale, offset_x, offset_y

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#eef1f5"))
        if self._background is not None:
            painter.drawImage(
                QRectF(0, 0, self.width(), self.height()),
                self._background,
            )
        scale, offset_x, offset_y = self._transform()

        def to_screen(x, y):
            return QPointF(offset_x + x * scale, offset_y + y * scale)

        page = QRectF(
            offset_x,
            offset_y,
            self._width_mm * scale,
            self._height_mm * scale,
        )
        painter.fillRect(page, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#9aa4b2"), 1))
        painter.drawRect(page)
        painter.setPen(QPen(self._color, 1.2))
        painter.setRenderHint(QPainter.Antialiasing, True)
        for points in self._polylines:
            if len(points) < 2:
                continue
            last = to_screen(points[0][0], points[0][1])
            for x, y in points[1:]:
                current = to_screen(x, y)
                painter.drawLine(last, current)
                last = current
        painter.end()


class GeneratorTab(QWidget):
    """Left control column, right preview, and the one Convert hand-off."""

    TITLE = "Generator"
    NAME = "generator"

    def __init__(self, host):
        super().__init__()
        self.host = host
        self._svg_path = ""
        outer = QHBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        self.controls = QWidget()
        self.controls_layout = QVBoxLayout(self.controls)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(6)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.controls)
        scroll.setMaximumWidth(340)
        outer.addWidget(scroll)

        right = QVBoxLayout()
        self.preview = PreviewCanvas()
        right.addWidget(self.preview, 1)
        self.status = QLabel("Configure the generator, then generate.")
        self.status.setWordWrap(True)
        right.addWidget(self.status)
        self.use_button = QPushButton("Use in Convert")
        self.use_button.setEnabled(False)
        self.use_button.clicked.connect(self.use_in_convert)
        right.addWidget(self.use_button)
        outer.addLayout(right, 1)

    def add_group(self, title):
        box = QGroupBox(title)
        form = QFormLayout(box)
        form.setLabelAlignment(Qt.AlignRight)
        form.setHorizontalSpacing(6)
        form.setVerticalSpacing(3)
        self.controls_layout.addWidget(box)
        return form

    def add_raw(self, widget):
        self.controls_layout.addWidget(widget)

    def finish_controls(self):
        self.controls_layout.addStretch(1)

    def set_result(self, polylines, width_mm, height_mm, stroke_mm, message, background=None):
        document = polylines_to_svg(polylines, width_mm, height_mm, stroke_mm)
        self._svg_path = str(write_svg_document(self.NAME, document))
        self.preview.set_page(width_mm, height_mm, polylines, background=background)
        self.use_button.setEnabled(bool(polylines))
        self.status.setText(message)
        if self.host is not None:
            self.host.generator_status(message)

    def use_in_convert(self):
        if not self._svg_path:
            return
        self.host.use_svg(self._svg_path)

    def report_error(self, message):
        self.status.setText(message)
        if self.host is not None:
            self.host.generator_status(message)


def preview_background(image_path, width_px=700):
    """Load an image scaled for the preview canvas, or None."""
    if not image_path:
        return None
    image = QImage(str(image_path))
    if image.isNull():
        return None
    return image.scaled(
        width_px,
        max(1, int(width_px * image.height() / max(1, image.width()))),
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )
