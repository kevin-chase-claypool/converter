"""SquiggleCam generator tab.

Algorithm ported from the MIT-licensed msurguy/SquiggleCam
(https://github.com/msurguy/SquiggleCam): one continuous squiggle per row,
where each pixel's brightness feeds an accumulated phase and the local wave
amplitude. All upstream settings are exposed: frequency, amplitude, line
count, brightness, contrast, min/max brightness, pixel spacing, and the
black-background inversion.
"""

from __future__ import annotations

import math

from PySide6.QtWidgets import QCheckBox, QLabel

from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "SquiggleCam"
ORDER = 100


def squigglecam_polylines(
    image_path,
    width_mm=200.0,
    height_mm=200.0,
    margin_mm=6.0,
    line_count=50,
    frequency=150,
    amplitude=1.0,
    brightness=0.0,
    contrast=0.0,
    min_brightness=0.0,
    max_brightness=255.0,
    spacing=4.0,
    black=False,
    scale_pct=100.0,
    max_pixels=700,
):
    """Return one squiggle polyline per row, in page millimetres."""
    from PIL import Image

    image = Image.open(image_path).convert("L")
    draw_w = max(5.0, width_mm - 2 * margin_mm)
    draw_h = max(5.0, height_mm - 2 * margin_mm)
    scale = min(draw_w / image.width, draw_h / image.height)
    px_w = max(8, min(max_pixels, int(image.width * scale)))
    px_h = max(8, min(max_pixels, int(image.height * scale)))
    image = image.resize((px_w, px_h), Image.LANCZOS)
    pixels = image.load()
    mm_per_px = min(draw_w / px_w, draw_h / px_h)
    offset_x = (width_mm - px_w * mm_per_px) / 2.0
    offset_y = (height_mm - px_h * mm_per_px) / 2.0

    contrast = max(-255.0, min(255.0, float(contrast)))
    contrast_factor = (259.0 * (contrast + 255.0)) / (255.0 * (259.0 - contrast))
    line_count = max(2, int(line_count))
    frequency = max(1.0, float(frequency))
    amplitude = max(0.0, float(amplitude))
    spacing = max(1.0, float(spacing))
    row_step = px_h / line_count
    polylines = []
    row = 0.0
    while row < px_h:
        y = int(row)
        phase = 0.0
        points = [(offset_x, offset_y + y * mm_per_px)]
        x = spacing
        while x < px_w:
            value = float(pixels[int(x), y])
            if contrast != 0.0:
                value = contrast_factor * (value - 128.0) + 128.0
            value += float(brightness)
            if black:
                value = min(255.0 - min_brightness, 255.0 - value)
            else:
                value = max(min_brightness, value)
            drive = max(max_brightness - value, 0.0)
            radius = amplitude * drive / line_count
            phase += drive / frequency
            points.append(
                (
                    offset_x + x * mm_per_px,
                    offset_y + (y + math.sin(phase) * radius) * mm_per_px,
                )
            )
            x += spacing
        if len(points) >= 2:
            polylines.append(points)
        row += row_step
    return scale_polylines(
        polylines, float(scale_pct) / 100.0, width_mm, height_mm
    )


class SquiggleCamTab(GeneratorTab):
    NAME = "squigglecam"
    GROUP = "Line art"
    DESCRIPTION = "One continuous squiggle per row from image tone."

    def __init__(self, host):
        super().__init__(host)
        image_group = self.add_group("Image")
        self.image_label = QLabel()
        self.image_label.setWordWrap(True)
        image_group.addRow("Artwork", self.image_label)
        self.black = QCheckBox("Black background (invert)")
        image_group.addRow("", self.black)
        self.brightness = double_spin(0, -100, 100, 5, 0)
        image_group.addRow("Brightness", self.brightness)
        self.contrast = double_spin(0, -100, 100, 5, 0)
        image_group.addRow("Contrast", self.contrast)
        self.min_brightness = double_spin(0, 0, 255, 5, 0)
        image_group.addRow("Min brightness", self.min_brightness)
        self.max_brightness = double_spin(255, 0, 255, 5, 0)
        image_group.addRow("Max brightness", self.max_brightness)

        squiggle = self.add_group("Squiggle")
        self.line_count = int_spin(50, 10, 200)
        squiggle.addRow("Line count", self.line_count)
        self.frequency = double_spin(150, 5, 256, 5, 0)
        squiggle.addRow("Frequency", self.frequency)
        self.amplitude = double_spin(1.0, 0.1, 5.0, 0.1, 1)
        squiggle.addRow("Amplitude", self.amplitude)
        self.spacing = double_spin(4.0, 1.0, 16.0, 0.5, 1, " px")
        squiggle.addRow("Pixel spacing", self.spacing)
        self.resolution = int_spin(700, 100, 1400, 50)
        squiggle.addRow("Resolution px", self.resolution)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(6, 0, 60, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.line_width = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        page.addRow("Line width", self.line_width)
        self.scale_pct = double_spin(100, 10, 1000, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.finish_controls()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_artwork()

    def _refresh_artwork(self):
        import os

        path = ""
        if self.host is not None and hasattr(self.host, "artwork_path"):
            path = self.host.artwork_path()
        self._artwork = path
        self.image_label.setText(
            os.path.basename(path)
            if path
            else "(use File > Open Artwork)"
        )

    def build_svg(self):
        self._refresh_artwork()
        if not self._artwork:
            raise ValueError("Open an image with File > Open Artwork first.")
        polylines = squigglecam_polylines(
            self._artwork,
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            margin_mm=self.margin.value(),
            line_count=self.line_count.value(),
            frequency=self.frequency.value(),
            amplitude=self.amplitude.value(),
            brightness=self.brightness.value(),
            contrast=self.contrast.value(),
            min_brightness=self.min_brightness.value(),
            max_brightness=self.max_brightness.value(),
            spacing=self.spacing.value(),
            black=self.black.isChecked(),
            scale_pct=self.scale_pct.value(),
            max_pixels=self.resolution.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} squiggle rows.",
        )


def create_tab(host):
    return SquiggleCamTab(host)
