"""Shared widgets and SVG output for generator tabs.

A generator tab is a control column plus a status line. It does not own a
preview: the main window's shared preview panel builds the active tab through
``build_svg()`` when the static Preview button is pressed, and Save G-code
exports that same result.
"""

from __future__ import annotations

import tempfile
import time
import uuid
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
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
        + "\n</g>\n</svg>\n"
    )


def write_svg_document(name, document):
    """Write an SVG document to a unique temp path and return it."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = f"{int(time.time() * 1000):d}-{uuid.uuid4().hex[:6]}"
    path = OUTPUT_DIR / f"{name}-{stamp}.svg"
    path.write_text(document, encoding="utf-8")
    return path


def scale_polylines(polylines, factor, width_mm, height_mm):
    """Scale every point about the page centre; 1.0 returns the input."""
    factor = max(0.01, float(factor))
    if abs(factor - 1.0) < 1e-9:
        return polylines
    centre_x = width_mm / 2.0
    centre_y = height_mm / 2.0
    return [
        [
            (
                centre_x + (x - centre_x) * factor,
                centre_y + (y - centre_y) * factor,
            )
            for x, y in line
        ]
        for line in polylines
    ]


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


class GeneratorTab(QWidget):
    """Control column plus status; the shared preview builds ``build_svg()``."""

    TITLE = "Generator"
    NAME = "generator"
    GROUP = "Generators"
    DESCRIPTION = "Generator tab."

    def __init__(self, host):
        super().__init__()
        self.host = host
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        self.controls = QWidget()
        self.controls_layout = QVBoxLayout(self.controls)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(6)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.controls)
        self.controls_scroll = scroll
        outer.addWidget(scroll, 1)

        hint = QLabel(
            "Set this tab's controls, then press Preview. The shared preview "
            "panel draws this tab's result, and Save G-code exports it."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #475569;")
        outer.addWidget(hint)
        self.status = QLabel("Ready.")
        self.status.setWordWrap(True)
        outer.addWidget(self.status)

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

    def write_result(self, polylines, width_mm, height_mm, stroke_mm, message):
        """Write the generated geometry and return its SVG path."""
        document = polylines_to_svg(polylines, width_mm, height_mm, stroke_mm)
        path = str(write_svg_document(self.NAME, document))
        self.status.setText(message)
        if self.host is not None:
            self.host.generator_status(message)
        return path

    def build_svg(self):
        """Generate this tab's SVG and return its path (implemented by tabs)."""
        raise NotImplementedError(f"{type(self).__name__} has no build_svg()")
