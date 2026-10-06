"""Flow Field generator tab.

Algorithm re-implemented in Python from the MIT-licensed msurguy/flow-lines
(https://github.com/msurguy/flow-lines), which follows Jobard & Lefer's
evenly-spaced streamline placement: seed points on a jittered grid, integrate
through a vector field, and stop when a candidate point breaks the minimum
separation, leaves the page, or reaches the step cap.

Output is SVG; the tab hands it to the Convert tab and never writes G-code.
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
    QPushButton,
)

from ._tab_common import GeneratorTab, double_spin, int_spin


TITLE = "Flow Field"


def _hash01(ix, iy, seed):
    value = (ix * 374761393 + iy * 668265263 + seed * 1442695040888963407) & 0xFFFFFFFF
    value = (value ^ (value >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((value ^ (value >> 16)) & 0xFFFFFF) / 0xFFFFFF


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def value_noise(x, y, seed):
    """Deterministic smooth value noise in [0, 1)."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = _smooth(x - ix), _smooth(y - iy)
    v00 = _hash01(ix, iy, seed)
    v10 = _hash01(ix + 1, iy, seed)
    v01 = _hash01(ix, iy + 1, seed)
    v11 = _hash01(ix + 1, iy + 1, seed)
    top = v00 + (v10 - v00) * fx
    bottom = v01 + (v11 - v01) * fx
    return top + (bottom - top) * fy


def noise_angle(x, y, scale_mm, seed, octaves=3):
    """Flow angle in radians from fractal value noise."""
    total = 0.0
    amplitude = 1.0
    weight = 0.0
    scale = max(1e-6, float(scale_mm))
    for octave in range(max(1, int(octaves))):
        total += amplitude * value_noise(
            x / scale, y / scale, seed + octave * 7919
        )
        weight += amplitude
        amplitude *= 0.5
        scale *= 0.5
    return 2.0 * math.pi * (total / max(weight, 1e-9))


class _ImageField:
    """Luminance gradient field, used when an image is the field source."""

    def __init__(self, path, invert=False, cutoff_pct=60):
        import numpy as np
        from PIL import Image, ImageFilter

        image = Image.open(path).convert("L")
        image.thumbnail((512, 512))
        image = image.filter(ImageFilter.GaussianBlur(1.2))
        data = np.asarray(image, dtype=np.float32) / 255.0
        self.width = image.width
        self.height = image.height
        gy, gx = np.gradient(data)
        self.gx = gx
        self.gy = gy
        self.luminance = data
        self.invert = bool(invert)
        self.cutoff = max(0.05, min(0.95, float(cutoff_pct) / 100.0))

    def _sample(self, grid, x, y, width_mm, height_mm):
        ix = min(self.width - 1, max(0, int(x / max(width_mm, 1e-6) * self.width)))
        iy = min(
            self.height - 1, max(0, int(y / max(height_mm, 1e-6) * self.height))
        )
        return grid[iy, ix]

    def active(self, x, y, width_mm, height_mm):
        lum = self._sample(self.luminance, x, y, width_mm, height_mm)
        return lum >= 1.0 - self.cutoff if self.invert else lum <= self.cutoff

    def angle(self, x, y, width_mm, height_mm, fallback):
        gx = self._sample(self.gx, x, y, width_mm, height_mm)
        gy = self._sample(self.gy, x, y, width_mm, height_mm)
        if self.invert:
            gx, gy = -gx, -gy
        angle = math.atan2(gx, -gy)  # perpendicular to the luminance gradient
        if math.cos(angle - fallback) < 0.0:
            angle += math.pi
        return angle


def flow_field_polylines(
    width_mm=200.0,
    height_mm=200.0,
    spacing_mm=3.0,
    step_mm=1.0,
    max_steps=400,
    noise_scale_mm=60.0,
    seed=7,
    octaves=3,
    margin_mm=6.0,
    image_path=None,
    invert=False,
    cutoff_pct=60,
    max_points=250_000,
):
    """Place evenly spaced streamlines; returns a list of (x, y) polylines."""
    width_mm = max(10.0, float(width_mm))
    height_mm = max(10.0, float(height_mm))
    spacing = max(0.5, float(spacing_mm))
    step = max(0.25, float(step_mm))
    margin = max(0.0, min(float(margin_mm), min(width_mm, height_mm) / 2.0 - 1.0))
    left, right = margin, width_mm - margin
    top, bottom = margin, height_mm - margin
    separation = spacing * 0.9
    field = None
    if image_path:
        try:
            field = _ImageField(image_path, invert=invert, cutoff_pct=cutoff_pct)
        except Exception:
            field = None

    accepted_points = 0
    cell = max(0.25, separation)
    segments = {}

    def _cell_key(x, y):
        return int(x // cell), int(y // cell)

    def _point_segment_distance(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        length_sq = dx * dx + dy * dy
        if length_sq < 1e-12:
            return math.hypot(px - ax, py - ay)
        t = ((px - ax) * dx + (py - ay) * dy) / length_sq
        t = max(0.0, min(1.0, t))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

    def blocked(x, y):
        cx, cy = _cell_key(x, y)
        for ix in range(cx - 1, cx + 2):
            for iy in range(cy - 1, cy + 2):
                for ax, ay, bx, by in segments.get((ix, iy), ()):
                    if _point_segment_distance(x, y, ax, ay, bx, by) < separation:
                        return True
        return False

    def remember_line(line):
        for index in range(len(line) - 1):
            ax, ay = line[index]
            bx, by = line[index + 1]
            mid_x, mid_y = (ax + bx) / 2.0, (ay + by) / 2.0
            segments.setdefault(_cell_key(mid_x, mid_y), []).append(
                (ax, ay, bx, by)
            )

    def angle_at(x, y):
        fallback = noise_angle(x, y, noise_scale_mm, seed, octaves)
        if field is not None:
            return field.angle(x, y, width_mm, height_mm, fallback)
        return fallback

    def integrate(start):
        points = [start]
        x, y = start
        for _ in range(int(max_steps)):
            angle = angle_at(x, y)
            nx = x + math.cos(angle) * step
            ny = y + math.sin(angle) * step
            if not (left <= nx <= right and top <= ny <= bottom):
                break
            if field is not None and not field.active(nx, ny, width_mm, height_mm):
                break
            if blocked(nx, ny):
                break
            points.append((nx, ny))
            x, y = nx, ny
        return points

    rng = random.Random(int(seed))
    jitter = spacing * 0.35
    y = top + spacing / 2.0
    while y <= bottom and accepted_points < max_points:
        x = left + spacing / 2.0
        while x <= right and accepted_points < max_points:
            sx = x + rng.uniform(-jitter, jitter)
            sy = y + rng.uniform(-jitter, jitter)
            if (
                left <= sx <= right
                and top <= sy <= bottom
                and (field is None or field.active(sx, sy, width_mm, height_mm))
                and not blocked(sx, sy)
            ):
                forward = integrate((sx, sy))
                # The same integrator is deterministic, so the backward pass is
                # made distinct only by walking the opposite initial angle.
                backward = _reverse_walk(
                    (sx, sy), angle_at, left, right, top, bottom, step,
                    int(max_steps), field, width_mm, height_mm, blocked,
                )
                line = list(reversed(backward[:-1])) + forward
                remember_line(line)
                accepted_points += len(line)
                if len(line) >= 2:
                    yield line
            x += spacing
        y += spacing


def _reverse_walk(
    start, angle_at, left, right, top, bottom, step, max_steps, field,
    width_mm, height_mm, blocked,
):
    points = [start]
    x, y = start
    for _ in range(max_steps):
        angle = angle_at(x, y) + math.pi
        nx = x + math.cos(angle) * step
        ny = y + math.sin(angle) * step
        if not (left <= nx <= right and top <= ny <= bottom):
            break
        if field is not None and not field.active(nx, ny, width_mm, height_mm):
            break
        if blocked(nx, ny):
            break
        points.append((nx, ny))
        x, y = nx, ny
    return points


class FlowFieldTab(GeneratorTab):
    NAME = "flow-field"

    def __init__(self, host):
        super().__init__(host)
        shape = self.add_group("Field")
        self.source = QComboBox()
        self.source.addItem("Procedural noise", "noise")
        self.source.addItem("Image edges", "image")
        shape.addRow("Source", self.source)
        self.image_label = QLabel()
        self.image_label.setWordWrap(True)
        shape.addRow("Artwork", self.image_label)
        self.invert = QCheckBox("Invert image tone")
        shape.addRow("", self.invert)
        self.cutoff = double_spin(60, 5, 95, 5, 0, " %")
        shape.addRow("Image cutoff", self.cutoff)
        self.seed = int_spin(7, 0, 999_999)
        shape.addRow("Seed", self.seed)
        self.scale = double_spin(60, 10, 300, 5, 0, " mm")
        shape.addRow("Noise scale", self.scale)
        self.octaves = int_spin(3, 1, 5)
        shape.addRow("Octaves", self.octaves)

        lines = self.add_group("Streamlines")
        self.spacing = double_spin(3.0, 0.8, 12.0, 0.2, 2, " mm")
        lines.addRow("Spacing", self.spacing)
        self.step = double_spin(1.0, 0.25, 4.0, 0.25, 2, " mm")
        lines.addRow("Step", self.step)
        self.max_steps = int_spin(400, 40, 4000, 20)
        lines.addRow("Max steps", self.max_steps)
        self.stroke = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        lines.addRow("Line width", self.stroke)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(6, 0, 50, 1, 0, " mm")
        page.addRow("Margin", self.margin)

        generate = QPushButton("Generate flow field")
        generate.clicked.connect(self.generate)
        self.add_raw(generate)
        self.finish_controls()
        self.source.currentIndexChanged.connect(self._sync_source)
        self._sync_source()

    def _sync_source(self):
        image_mode = self.source.currentData() == "image"
        self.image_label.setEnabled(image_mode)
        self.invert.setEnabled(image_mode)
        self.cutoff.setEnabled(image_mode)

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

    def generate(self):
        self._refresh_artwork()
        image_mode = self.source.currentData() == "image"
        if image_mode and not self._artwork:
            self.report_error("Import an image with the Artwork row above first.")
            return
        QGuiApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            polylines = list(
                flow_field_polylines(
                    width_mm=self.page_w.value(),
                    height_mm=self.page_h.value(),
                    spacing_mm=self.spacing.value(),
                    step_mm=self.step.value(),
                    max_steps=self.max_steps.value(),
                    noise_scale_mm=self.scale.value(),
                    seed=self.seed.value(),
                    octaves=self.octaves.value(),
                    margin_mm=self.margin.value(),
                    image_path=self._artwork if image_mode else None,
                    invert=self.invert.isChecked(),
                    cutoff_pct=self.cutoff.value(),
                )
            )
        except Exception as exc:
            self.report_error(f"Flow field failed: {exc}")
            return
        finally:
            QGuiApplication.restoreOverrideCursor()
        points = sum(len(line) for line in polylines)
        self.set_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.stroke.value(),
            f"{len(polylines)} streamlines, {points} points.",
        )


def create_tab(host):
    return FlowFieldTab(host)
