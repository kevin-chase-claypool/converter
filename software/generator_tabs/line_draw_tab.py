"""Line Draw generator tab.

Algorithm re-implemented in Python from the MIT-licensed LingDong-/linedraw
(https://github.com/LingDong-/linedraw): raster image -> blurred luminance ->
Sobel edge map (non-maximum suppressed) traced into contour paths, plus
luminance-driven hatch runs in the dark regions, with optional sketch jitter.

This is edge-detection line art, not the converter's tone-derived terrain
contours or gradient waves. Output is SVG; G-code stays in the Convert tab.
"""

from __future__ import annotations

import math
import os
import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
)

from ._tab_common import (
    GeneratorTab,
    double_spin,
    int_spin,
    scale_polylines,
)


TITLE = "Line Draw"
ORDER = 20

NEIGHBOURS = (
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
)


def _fit_grid(width_mm, height_mm, margin_mm, image_w, image_h, max_px=900):
    draw_w = max(5.0, width_mm - 2 * margin_mm)
    draw_h = max(5.0, height_mm - 2 * margin_mm)
    scale = min(draw_w / image_w, draw_h / image_h)
    w_px = max(8, int(image_w * scale))
    h_px = max(8, int(image_h * scale))
    if max(w_px, h_px) > max_px:
        shrink = max_px / max(w_px, h_px)
        w_px = max(8, int(w_px * shrink))
        h_px = max(8, int(h_px * shrink))
    mm_per_px = min(draw_w / w_px, draw_h / h_px)
    off_x = (width_mm - w_px * mm_per_px) / 2.0
    off_y = (height_mm - h_px * mm_per_px) / 2.0
    return w_px, h_px, off_x, off_y, mm_per_px


def _sobel(data):
    import numpy as np

    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    kernel_y = kernel_x.T
    padded = np.pad(data, 1, mode="edge")
    gx = np.zeros_like(data)
    gy = np.zeros_like(data)
    for row in range(3):
        for col in range(3):
            window = padded[row:row + data.shape[0], col:col + data.shape[1]]
            gx += kernel_x[row, col] * window
            gy += kernel_y[row, col] * window
    return gx, gy


def _suppress_edges(gx, gy, threshold):
    import numpy as np

    magnitude = np.hypot(gx, gy)
    if not magnitude.any():
        return np.zeros_like(magnitude, dtype=bool)
    peak = float(np.percentile(magnitude, 99.0))
    if peak <= 1e-9:
        return np.zeros_like(magnitude, dtype=bool)
    magnitude = magnitude / peak
    angle = (np.degrees(np.arctan2(gy, gx)) + 180.0) % 180.0
    keep = np.zeros_like(magnitude, dtype=bool)
    rows, cols = magnitude.shape
    for y in range(1, rows - 1):
        for x in range(1, cols - 1):
            if magnitude[y, x] < threshold:
                continue
            direction = angle[y, x]
            if direction < 22.5 or direction >= 157.5:
                a, b = magnitude[y, x - 1], magnitude[y, x + 1]
            elif direction < 67.5:
                a, b = magnitude[y - 1, x + 1], magnitude[y + 1, x - 1]
            elif direction < 112.5:
                a, b = magnitude[y - 1, x], magnitude[y + 1, x]
            else:
                a, b = magnitude[y - 1, x - 1], magnitude[y + 1, x + 1]
            if magnitude[y, x] >= a and magnitude[y, x] >= b:
                keep[y, x] = True
    return keep


def _simplify(points, epsilon):
    if len(points) < 3:
        return points
    start, end = points[0], points[-1]
    dx, dy = end[0] - start[0], end[1] - start[1]
    norm = math.hypot(dx, dy)
    worst, index = -1.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if norm < 1e-9:
            distance = math.hypot(px - start[0], py - start[1])
        else:
            distance = abs(dy * px - dx * py + end[0] * start[1] - end[1] * start[0]) / norm
        if distance > worst:
            worst, index = distance, i
    if worst <= epsilon:
        return [start, end]
    left = _simplify(points[: index + 1], epsilon)
    right = _simplify(points[index:], epsilon)
    return left[:-1] + right


def _trace_edges(
    mask, mm_per_px, off_x, off_y, min_length_mm, jitter, rng, simplify_px
):
    rows, cols = mask.shape
    pixels = [(x, y) for y in range(rows) for x in range(cols) if mask[y, x]]
    if not pixels:
        return []
    unused = set(pixels)
    degree = {}
    for x, y in pixels:
        degree[(x, y)] = sum(
            1 for dx, dy in NEIGHBOURS if (x + dx, y + dy) in unused
        )
    paths = []
    while unused:
        ends = [p for p in sorted(unused) if degree.get(p, 0) <= 1]
        start = ends[0] if ends else min(unused)
        chain = [start]
        unused.discard(start)
        current = start
        while True:
            nxt = None
            for dx, dy in NEIGHBOURS:
                candidate = (current[0] + dx, current[1] + dy)
                if candidate in unused:
                    nxt = candidate
                    break
            if nxt is None:
                break
            unused.discard(nxt)
            chain.append(nxt)
            current = nxt
        if len(chain) < 2:
            continue
        simplified = _simplify(chain, max(0.1, float(simplify_px)))
        length_mm = sum(
            math.hypot(
                (simplified[i + 1][0] - simplified[i][0]) * mm_per_px,
                (simplified[i + 1][1] - simplified[i][1]) * mm_per_px,
            )
            for i in range(len(simplified) - 1)
        )
        if length_mm < min_length_mm:
            continue
        points = []
        for px, py in simplified:
            x = off_x + (px + 0.5) * mm_per_px + rng.uniform(-jitter, jitter)
            y = off_y + (py + 0.5) * mm_per_px + rng.uniform(-jitter, jitter)
            points.append((x, y))
        paths.append(points)
    return paths


def _hatch_patches(
    luminance,
    patch_px,
    mm_per_px,
    off_x,
    off_y,
    light_threshold,
    mid_threshold,
    dark_threshold,
    jitter_mm,
):
    """Upstream linedraw hatch: fixed L and anti-diagonal strokes per patch.

    Ported from `hatch()` in LingDong-/linedraw: patches above the light
    threshold hatch nothing, the mid level adds one horizontal stroke, the
    dark level adds a second horizontal stroke, and levels below the mid
    threshold add the anti-diagonal. Coordinates follow the upstream
    ``(x, y+sc/4)`` geometry with the patch size as the scale.
    """
    rows, cols = luminance.shape
    sc = max(1, int(patch_px))
    light = max(0.0, min(255.0, float(light_threshold))) / 255.0
    mid = max(0.0, min(255.0, float(mid_threshold))) / 255.0
    dark = max(0.0, min(255.0, float(dark_threshold))) / 255.0
    horizontal = []
    diagonal = []
    for y0 in range(0, rows, sc):
        for x0 in range(0, cols, sc):
            value = float(luminance[y0, x0])
            if value > light:
                continue
            x = x0
            y = y0
            if value > mid:
                horizontal.append([(x, y + sc / 4.0), (x + sc, y + sc / 4.0)])
            elif value > dark:
                horizontal.append([(x, y + sc / 4.0), (x + sc, y + sc / 4.0)])
                diagonal.append([(x + sc, y), (x, y + sc)])
            else:
                horizontal.append([(x, y + sc / 4.0), (x + sc, y + sc / 4.0)])
                horizontal.append(
                    [(x, y + sc / 2.0 + sc / 4.0), (x + sc, y + sc / 2.0 + sc / 4.0)]
                )
                diagonal.append([(x + sc, y), (x, y + sc)])
    # Upstream merges chains whose end meets another's start.
    for group in (horizontal, diagonal):
        for _ in range(2):
            for first in group:
                if not first:
                    continue
                for second in group:
                    if second and second is not first and first[-1] == second[0]:
                        first.extend(second[1:])
                        second.clear()
        group[:] = [line for line in group if line]
    paths = []
    for group in (horizontal, diagonal):
        for line in group:
            points = []
            for index, (px, py) in enumerate(line):
                shake_x = 0.0
                shake_y = 0.0
                if jitter_mm:
                    shake_x = (rng_noise(px * 0.05, py * 0.05) - 0.5) * 2.0 * jitter_mm
                    shake_y = (rng_noise(px * 0.05, py * 0.05 + 17.0) - 0.5) * 2.0 * jitter_mm
                points.append(
                    (
                        off_x + px * mm_per_px + shake_x,
                        off_y + py * mm_per_px + shake_y,
                    )
                )
            paths.append(points)
    return paths


def rng_noise(x, y):
    """Deterministic smooth value noise in [0, 1] for the hatch jitter."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    sx = fx * fx * (3.0 - 2.0 * fx)
    sy = fy * fy * (3.0 - 2.0 * fy)

    def hashed(px, py):
        value = (px * 374761393 + py * 668265263) & 0xFFFFFFFF
        value = (value ^ (value >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((value ^ (value >> 16)) & 0xFFFFFF) / 0xFFFFFF

    top = hashed(ix, iy) + (hashed(ix + 1, iy) - hashed(ix, iy)) * sx
    bottom = hashed(ix, iy + 1) + (hashed(ix + 1, iy + 1) - hashed(ix, iy + 1)) * sx
    return top + (bottom - top) * sy


def line_draw_polylines(
    image_path,
    mode="both",
    edge_threshold_pct=35,
    hatch_spacing_mm=2.0,
    hatch_light_threshold=144,
    hatch_mid_threshold=64,
    hatch_dark_threshold=16,
    jitter_mm=0.25,
    min_length_mm=1.2,
    invert=False,
    width_mm=200.0,
    height_mm=200.0,
    margin_mm=6.0,
    seed=7,
    resolution_px=900,
    simplify_px=0.75,
):
    """Return contour and/or hatch polylines in page millimetres."""
    import numpy as np
    from PIL import Image, ImageFilter

    image = Image.open(image_path).convert("L")
    w_px, h_px, off_x, off_y, mm_per_px = _fit_grid(
        width_mm, height_mm, margin_mm, image.width, image.height,
        max_px=max(200, int(resolution_px)),
    )
    image = image.resize((w_px, h_px), Image.LANCZOS)
    image = image.filter(ImageFilter.GaussianBlur(1.0))
    luminance = np.asarray(image, dtype=np.float32) / 255.0
    if invert:
        luminance = 1.0 - luminance

    rng = random.Random(int(seed))
    jitter = max(0.0, float(jitter_mm))
    paths = []
    if mode in ("contour", "both"):
        gx, gy = _sobel(luminance)
        mask = _suppress_edges(gx, gy, max(0.02, float(edge_threshold_pct) / 100.0))
        paths.extend(
            _trace_edges(
                mask, mm_per_px, off_x, off_y, min_length_mm, jitter, rng,
                simplify_px,
            )
        )
    if mode in ("hatch", "both"):
        patch_px = max(2, int(round(float(hatch_spacing_mm) / mm_per_px)))
        paths.extend(
            _hatch_patches(
                luminance,
                patch_px,
                mm_per_px,
                off_x,
                off_y,
                hatch_light_threshold,
                hatch_mid_threshold,
                hatch_dark_threshold,
                jitter,
            )
        )
    return paths


class LineDrawTab(GeneratorTab):
    NAME = "line-draw"
    GROUP = "Line art"
    DESCRIPTION = "Raster image to edge contours and hatch."

    def __init__(self, host):
        super().__init__(host)
        image_group = self.add_group("Image")
        self.image_label = QLabel()
        self.image_label.setWordWrap(True)
        image_group.addRow("Artwork", self.image_label)
        self.invert = QCheckBox("Invert tone")
        image_group.addRow("", self.invert)

        style = self.add_group("Line style")
        self.mode = QComboBox()
        self.mode.addItem("Contours + hatch", "both")
        self.mode.addItem("Contours only", "contour")
        self.mode.addItem("Hatch only", "hatch")
        style.addRow("Mode", self.mode)
        self.threshold = double_spin(35, 2, 95, 1, 0, " %")
        style.addRow("Edge threshold", self.threshold)
        self.hatch_spacing = double_spin(2.0, 0.6, 10.0, 0.2, 2, " mm")
        style.addRow("Hatch spacing", self.hatch_spacing)
        self.hatch_light = int_spin(144, 0, 255)
        style.addRow("Hatch light", self.hatch_light)
        self.hatch_mid = int_spin(64, 0, 255)
        style.addRow("Hatch mid", self.hatch_mid)
        self.hatch_dark = int_spin(16, 0, 255)
        style.addRow("Hatch dark", self.hatch_dark)
        self.jitter = double_spin(0.25, 0.0, 2.0, 0.05, 2, " mm")
        style.addRow("Sketch jitter", self.jitter)
        self.min_length = double_spin(1.2, 0.2, 20.0, 0.2, 2, " mm")
        style.addRow("Min length", self.min_length)
        self.simplify = double_spin(0.75, 0.1, 3.0, 0.05, 2, " px")
        style.addRow("Simplify", self.simplify)
        self.resolution = int_spin(900, 200, 1400, 50)
        style.addRow("Resolution px", self.resolution)
        self.stroke = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        style.addRow("Line width", self.stroke)
        self.seed = int_spin(7, 0, 999_999)
        style.addRow("Seed", self.seed)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(6, 0, 50, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.scale_pct = double_spin(100, 10, 1000, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

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

    def build_svg(self):
        self._refresh_artwork()
        path = self._artwork
        if not path:
            raise ValueError("Import an image with the Artwork row above first.")
        QGuiApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            polylines = line_draw_polylines(
                path,
                mode=self.mode.currentData(),
                edge_threshold_pct=self.threshold.value(),
                hatch_spacing_mm=self.hatch_spacing.value(),
                hatch_light_threshold=self.hatch_light.value(),
                hatch_mid_threshold=self.hatch_mid.value(),
                hatch_dark_threshold=self.hatch_dark.value(),
                jitter_mm=self.jitter.value(),
                min_length_mm=self.min_length.value(),
                invert=self.invert.isChecked(),
                width_mm=self.page_w.value(),
                height_mm=self.page_h.value(),
                margin_mm=self.margin.value(),
                seed=self.seed.value(),
                resolution_px=self.resolution.value(),
                simplify_px=self.simplify.value(),
            )
        finally:
            QGuiApplication.restoreOverrideCursor()
        polylines = scale_polylines(
            polylines,
            self.scale_pct.value() / 100.0,
            self.page_w.value(),
            self.page_h.value(),
        )
        width = self.page_w.value()
        height = self.page_h.value()
        result = self.write_result(
            polylines,
            width,
            height,
            self.stroke.value(),
            f"{len(polylines)} paths for Line Draw.",
        )
        return result


def create_tab(host):
    return LineDrawTab(host)
