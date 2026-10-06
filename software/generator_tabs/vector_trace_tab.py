"""Vector Trace generator tab.

High-quality outline tracing for logos, silhouettes, and line art: the image
is thresholded (Otsu or manual), dark regions are traced as closed contours
with marching squares, simplified and smoothed, and optionally hatch-filled at
any angle. This is a boundary trace, not the edge-sketching style of the Line
Draw tool.
"""

from __future__ import annotations

import math

from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel

from ._raster import chaikin, marching_squares, otsu_threshold, simplify_path
from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Vector Trace"
ORDER = 190


def _polygon_area(points):
    area = 0.0
    for index, (x0, y0) in enumerate(points):
        x1, y1 = points[(index + 1) % len(points)]
        area += x0 * y1 - x1 * y0
    return abs(area) / 2.0


def _simplify_closed(points, epsilon):
    """Douglas-Peucker for a closed loop.

    The open-path algorithm is degenerate when the first and last points are
    identical (every point appears collinear), so the loop is split at the
    point farthest from the start and each half is simplified separately. The
    returned path is explicitly closed.
    """
    loop = list(points)
    if len(loop) >= 2 and loop[0] == loop[-1]:
        loop = loop[:-1]
    if len(loop) < 3:
        return loop + [loop[0]] if loop else []
    if epsilon <= 0:
        return loop + [loop[0]]
    start = loop[0]
    far = max(
        range(len(loop)),
        key=lambda index: (loop[index][0] - start[0]) ** 2
        + (loop[index][1] - start[1]) ** 2,
    )
    first_chain = simplify_path(loop[: far + 1], epsilon)
    second_chain = simplify_path(loop[far:] + [loop[0]], epsilon)
    result = first_chain[:-1] + second_chain
    if result and result[0] != result[-1]:
        result.append(result[0])
    return result


def _hatch_mask(mask, spacing_px, angle_deg):
    import numpy as np

    rows, cols = mask.shape
    angle = math.radians(angle_deg)
    ux, uy = math.cos(angle), math.sin(angle)
    nx, ny = -uy, ux
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return []
    offsets = xs * nx + ys * ny
    positions = xs * ux + ys * uy
    offset_min, offset_max = float(offsets.min()), float(offsets.max())
    position_min, position_max = float(positions.min()), float(positions.max())
    step = max(1.0, float(spacing_px))
    paths = []
    offset = offset_min
    while offset <= offset_max:
        runs = []
        run_start = None
        position = position_min
        while position <= position_max:
            px = offset * nx + position * ux
            py = offset * ny + position * uy
            inside = (
                0.0 <= px < cols
                and 0.0 <= py < rows
                and bool(mask[int(py), int(px)])
            )
            if inside and run_start is None:
                run_start = position
            elif not inside and run_start is not None:
                runs.append((run_start, position))
                run_start = None
            position += 1.0
        if run_start is not None:
            runs.append((run_start, position_max))
        for first, second in runs:
            if second - first < 1.5:
                continue
            paths.append(
                [
                    (
                        offset * nx + first * ux,
                        offset * ny + first * uy,
                    ),
                    (
                        offset * nx + second * ux,
                        offset * ny + second * uy,
                    ),
                ]
            )
        offset += step
    return paths


def vector_trace_polylines(
    image_path,
    threshold_mode="otsu",
    threshold=128,
    invert=False,
    simplify_px=1.0,
    smooth_passes=1,
    min_area_px=6.0,
    fill="outlines",
    hatch_spacing_mm=1.5,
    hatch_angle_deg=45.0,
    width_mm=200.0,
    height_mm=200.0,
    margin_mm=6.0,
    scale_pct=100.0,
    max_pixels=700,
):
    """Return traced outlines and optional hatch fill in page millimetres."""
    import numpy as np
    from PIL import Image

    image = Image.open(image_path).convert("L")
    draw_w = max(5.0, width_mm - 2 * margin_mm)
    draw_h = max(5.0, height_mm - 2 * margin_mm)
    fit = min(draw_w / image.width, draw_h / image.height)
    px_w = max(8, min(max_pixels, int(image.width * fit)))
    px_h = max(8, min(max_pixels, int(image.height * fit)))
    image = image.resize((px_w, px_h), Image.LANCZOS)
    gray = np.asarray(image, dtype=float)
    limit = (
        otsu_threshold(gray)
        if str(threshold_mode) == "otsu"
        else float(threshold)
    )
    mask = gray < limit
    if invert:
        mask = ~mask
    mm_per_px = min(draw_w / px_w, draw_h / px_h)
    offset_x = (width_mm - px_w * mm_per_px) / 2.0
    offset_y = (height_mm - px_h * mm_per_px) / 2.0

    paths = []
    if fill in ("outlines", "both"):
        for contour in marching_squares(mask.astype(float), 0.5):
            if len(contour) < 4:
                continue
            if _polygon_area(contour) < min_area_px:
                continue
            simplified = _simplify_closed(contour, max(0.0, simplify_px))
            smoothed = chaikin(simplified, max(0, min(4, smooth_passes)), closed=True)
            if smoothed[0] != smoothed[-1]:
                smoothed = smoothed + [smoothed[0]]
            paths.append(smoothed)
    if fill in ("hatch", "both"):
        spacing_px = max(1.0, hatch_spacing_mm / mm_per_px)
        paths.extend(_hatch_mask(mask, spacing_px, hatch_angle_deg))
    polylines = [
        [
            (offset_x + x * mm_per_px, offset_y + y * mm_per_px)
            for x, y in path
        ]
        for path in paths
    ]
    return scale_polylines(
        polylines, float(scale_pct) / 100.0, width_mm, height_mm
    )


class VectorTraceTab(GeneratorTab):
    NAME = "vector-trace"
    GROUP = "Photo-based"
    DESCRIPTION = "Clean outline and hatch tracing for logos and silhouettes."

    def __init__(self, host):
        super().__init__(host)
        source = self.add_group("Source")
        self.image_label = QLabel()
        self.image_label.setWordWrap(True)
        source.addRow("Artwork", self.image_label)
        self.mode = QComboBox()
        self.mode.addItem("Otsu (auto)", "otsu")
        self.mode.addItem("Manual threshold", "manual")
        source.addRow("Threshold", self.mode)
        self.threshold = int_spin(128, 1, 254, 1)
        source.addRow("Level", self.threshold)
        self.invert = QCheckBox("Trace the light regions")
        source.addRow("", self.invert)

        trace = self.add_group("Trace")
        self.simplify = double_spin(1.0, 0.0, 6.0, 0.25, 2, " px")
        trace.addRow("Simplify", self.simplify)
        self.smooth = int_spin(1, 0, 4, 1)
        trace.addRow("Smoothing", self.smooth)
        self.min_area = double_spin(6.0, 0.0, 500.0, 2.0, 1, " px2")
        trace.addRow("Min area", self.min_area)
        self.fill = QComboBox()
        self.fill.addItem("Outlines", "outlines")
        self.fill.addItem("Hatch fill", "hatch")
        self.fill.addItem("Outlines + hatch", "both")
        trace.addRow("Fill", self.fill)
        self.hatch_spacing = double_spin(1.5, 0.4, 10.0, 0.1, 2, " mm")
        trace.addRow("Hatch spacing", self.hatch_spacing)
        self.hatch_angle = double_spin(45, 0, 180, 5, 0, " deg")
        trace.addRow("Hatch angle", self.hatch_angle)

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
            os.path.basename(path) if path else "(use File > Open Artwork)"
        )

    def build_svg(self):
        self._refresh_artwork()
        if not self._artwork:
            raise ValueError("Open an image with File > Open Artwork first.")
        polylines = vector_trace_polylines(
            self._artwork,
            threshold_mode=self.mode.currentData(),
            threshold=self.threshold.value(),
            invert=self.invert.isChecked(),
            simplify_px=self.simplify.value(),
            smooth_passes=self.smooth.value(),
            min_area_px=self.min_area.value(),
            fill=self.fill.currentData(),
            hatch_spacing_mm=self.hatch_spacing.value(),
            hatch_angle_deg=self.hatch_angle.value(),
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            margin_mm=self.margin.value(),
            scale_pct=self.scale_pct.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} traced paths ({self.fill.currentText()}).",
        )


def create_tab(host):
    return VectorTraceTab(host)
