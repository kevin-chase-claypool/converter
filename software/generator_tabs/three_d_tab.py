"""3D Wireframe generator tab.

Re-implemented in Python from the MIT-licensed fogleman/ln
(https://github.com/fogleman/ln) hidden-line approach and the MIT-licensed
Viewport.js (https://github.com/RobMakesThings/Viewport.js): load an OBJ or
STL mesh, project it orthographically, then depth-test sampled edges against a
z-buffer of the projected triangles and keep only the visible runs.

The app has no other 3D input path; output is SVG for the Convert tab.
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QComboBox, QLineEdit

from ._tab_common import (
    GeneratorTab,
    double_spin,
    file_picker,
    scale_polylines,
)


TITLE = "3D Wireframe"
ORDER = 30


def load_obj(text):
    """Parse OBJ text into (vertices Nx3 float list, triangles Mx3 int list)."""
    vertices = []
    triangles = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("v "):
            parts = line.split()
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif line.startswith("f "):
            face = []
            for token in line.split()[1:]:
                index = token.split("/")[0]
                face.append(int(index) - 1 if int(index) > 0 else len(vertices) + int(index))
            for i in range(1, len(face) - 1):
                triangles.append((face[0], face[i], face[i + 1]))
    return vertices, triangles


def load_stl(data):
    """Parse binary or ASCII STL bytes into (vertices, triangles)."""
    if len(data) >= 84:
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + count * 50 == len(data):
            vertices = []
            triangles = []
            offset = 84
            for _ in range(count):
                values = struct.unpack_from("<12f", data, offset)
                base = len(vertices)
                vertices.extend(
                    [
                        (values[3], values[4], values[5]),
                        (values[6], values[7], values[8]),
                        (values[9], values[10], values[11]),
                    ]
                )
                triangles.append((base, base + 1, base + 2))
                offset += 50
            return vertices, triangles
    text = data.decode("utf-8", errors="replace")
    vertices = []
    triangles = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0].lower() == "vertex":
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
    for i in range(0, len(vertices) - 2, 3):
        triangles.append((i, i + 1, i + 2))
    return vertices, triangles


def _rotation(yaw_deg, pitch_deg, roll_deg):
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    roll = math.radians(roll_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    return (
        (cy * cr + sy * sp * sr, -cy * sr + sy * sp * cr, sy * cp),
        (cp * sr, cp * cr, -sp),
        (-sy * cr + cy * sp * sr, sy * sr + cy * sp * cr, cy * cp),
    )


def project_vertices(
    vertices, yaw, pitch, roll, width_mm, height_mm, margin_mm,
    target_width_mm=None,
):
    """Orthographic projection to page millimetres; returns (points, depth)."""
    matrix = _rotation(yaw, pitch, roll)
    rotated = []
    for x, y, z in vertices:
        rotated.append(
            (
                matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z,
                matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z,
                matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z,
            )
        )
    if not rotated:
        return [], []
    xs = [p[0] for p in rotated]
    ys = [-p[1] for p in rotated]
    depth = [p[2] for p in rotated]
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)
    draw_w = max(5.0, width_mm - 2 * margin_mm)
    draw_h = max(5.0, height_mm - 2 * margin_mm)
    scale = min(
        draw_w / span_x if span_x > 1e-9 else float("inf"),
        draw_h / span_y if span_y > 1e-9 else float("inf"),
    )
    if not math.isfinite(scale):
        scale = 1.0
    if target_width_mm:
        scale = min(scale, float(target_width_mm) / max(span_x, 1e-9))
    centre_x = (max(xs) + min(xs)) / 2.0
    centre_y = (max(ys) + min(ys)) / 2.0
    page_x = width_mm / 2.0
    page_y = height_mm / 2.0
    points = [
        (page_x + (x - centre_x) * scale, page_y + (y - centre_y) * scale)
        for x, y in zip(xs, ys)
    ]
    return points, depth


def _unique_edges(triangles):
    edges = {}
    for index, (a, b, c) in enumerate(triangles):
        for first, second in ((a, b), (b, c), (c, a)):
            key = (first, second) if first < second else (second, first)
            edges.setdefault(key, []).append(index)
    return edges


def _face_normals(vertices, triangles):
    normals = []
    for a, b, c in triangles:
        ax, ay, az = vertices[a]
        bx, by, bz = vertices[b]
        cx, cy, cz = vertices[c]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        normals.append((nx / length, ny / length, nz / length))
    return normals


def _rasterize(points, depth, triangles, width_mm, height_mm, px_per_mm=3.0):
    """Return (z_buffer, px_per_mm, origin) for visibility testing."""
    import numpy as np

    width_px = max(8, int(width_mm * px_per_mm))
    height_px = max(8, int(height_mm * px_per_mm))
    zbuffer = np.full((height_px, width_px), -1e30, dtype=np.float64)
    for a, b, c in triangles:
        pa, pb, pc = points[a], points[b], points[c]
        za, zb, zc = depth[a], depth[b], depth[c]
        min_x = max(0, int(min(pa[0], pb[0], pc[0]) * px_per_mm))
        max_x = min(width_px - 1, int(max(pa[0], pb[0], pc[0]) * px_per_mm) + 1)
        min_y = max(0, int(min(pa[1], pb[1], pc[1]) * px_per_mm))
        max_y = min(height_px - 1, int(max(pa[1], pb[1], pc[1]) * px_per_mm) + 1)
        if min_x > max_x or min_y > max_y:
            continue
        xs = (np.arange(min_x, max_x + 1) + 0.5) / px_per_mm
        ys = (np.arange(min_y, max_y + 1) + 0.5) / px_per_mm
        grid_x, grid_y = np.meshgrid(xs, ys)
        denominator = (
            (pb[1] - pc[1]) * (pa[0] - pc[0])
            + (pc[0] - pb[0]) * (pa[1] - pc[1])
        )
        if abs(denominator) < 1e-12:
            continue
        w_a = (
            (pb[1] - pc[1]) * (grid_x - pc[0])
            + (pc[0] - pb[0]) * (grid_y - pc[1])
        ) / denominator
        w_b = (
            (pc[1] - pa[1]) * (grid_x - pc[0])
            + (pa[0] - pc[0]) * (grid_y - pc[1])
        ) / denominator
        w_c = 1.0 - w_a - w_b
        inside = (w_a >= -1e-6) & (w_b >= -1e-6) & (w_c >= -1e-6)
        if not inside.any():
            continue
        z = w_a * za + w_b * zb + w_c * zc
        region = zbuffer[min_y:max_y + 1, min_x:max_x + 1]
        np.maximum(region, np.where(inside, z, -1e30), out=region)
    return zbuffer, px_per_mm


def three_d_polylines(
    model_path,
    style="hidden",
    yaw=35.0,
    pitch=-25.0,
    roll=0.0,
    width_mm=200.0,
    height_mm=200.0,
    margin_mm=8.0,
    sample_mm=0.7,
    silhouette_deg=25.0,
    max_triangles=40_000,
    target_width_mm=None,
):
    """Return visible-edge polylines in page millimetres."""
    data = Path(model_path).read_bytes()
    if model_path.lower().endswith(".stl"):
        vertices, triangles = load_stl(data)
    else:
        vertices, triangles = load_obj(data.decode("utf-8", errors="replace"))
    if not vertices or not triangles:
        raise ValueError("No triangles found in the model.")
    if len(triangles) > max_triangles:
        raise ValueError(
            f"Model has {len(triangles)} triangles; the tab caps at {max_triangles}."
        )
    points, depth = project_vertices(
        vertices, yaw, pitch, roll, width_mm, height_mm, margin_mm,
        target_width_mm=target_width_mm,
    )
    edges = _unique_edges(triangles)
    normals = _face_normals(
        [(p[0], p[1], d) for p, d in zip(points, depth)], triangles
    )
    if style == "silhouette":
        threshold = math.cos(math.radians(silhouette_deg))
        selected = []
        for edge, faces in edges.items():
            if len(faces) == 1:
                selected.append(edge)
            else:
                first, second = normals[faces[0]], normals[faces[1]]
                if sum(a * b for a, b in zip(first, second)) < threshold:
                    selected.append(edge)
    else:
        selected = list(edges)
    if style == "all":
        return [
            [points[edge[0]], points[edge[1]]]
            for edge in sorted(selected)
        ]

    zbuffer, px_per_mm = _rasterize(
        points, depth, triangles, width_mm, height_mm
    )
    depth_values = [d for d in depth]
    span = max(depth_values) - min(depth_values)
    bias = max(1e-6, span * 0.004)
    sample_step = max(0.2, float(sample_mm))
    rows, cols = zbuffer.shape
    polylines = []
    for edge in sorted(selected):
        first, second = edge
        (x0, y0), (x1, y1) = points[first], points[second]
        z0, z1 = depth[first], depth[second]
        length = math.hypot(x1 - x0, y1 - y0)
        count = max(2, int(length / sample_step) + 1)
        run = []
        for step in range(count + 1):
            t = step / count
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            z = z0 + (z1 - z0) * t
            px = min(cols - 1, max(0, int(x * px_per_mm)))
            py = min(rows - 1, max(0, int(y * px_per_mm)))
            # Look at the 3x3 neighbourhood so an edge that projects exactly
            # onto a silhouette boundary still sees the face it belongs to.
            nearest = float(
                zbuffer[
                    max(0, py - 1): min(rows, py + 2),
                    max(0, px - 1): min(cols, px + 2),
                ].max()
            )
            visible = z >= nearest - bias
            if visible:
                run.append((x, y))
            elif run:
                if len(run) >= 2:
                    polylines.append(run)
                run = []
        if len(run) >= 2:
            polylines.append(run)
    return polylines


class ThreeDTab(GeneratorTab):
    NAME = "3d-wireframe"
    GROUP = "3D"
    DESCRIPTION = "OBJ/STL to hidden-line vector art."

    def __init__(self, host):
        super().__init__(host)
        model = self.add_group("Model")
        self.model_path = QLineEdit()
        model.addRow("File", self.model_path)
        model.addRow(
            "",
            file_picker(
                self.model_path,
                lambda _path: None,
                "Choose an OBJ or STL model",
                "Models (*.obj *.stl);;All files (*.*)",
            ),
        )
        self.style = QComboBox()
        self.style.addItem("Hidden-line wireframe", "hidden")
        self.style.addItem("Silhouette outlines", "silhouette")
        self.style.addItem("All edges (no hiding)", "all")
        model.addRow("Style", self.style)
        self.yaw = double_spin(35, -180, 180, 5, 0, " deg")
        model.addRow("Yaw", self.yaw)
        self.pitch = double_spin(-25, -90, 90, 5, 0, " deg")
        model.addRow("Pitch", self.pitch)
        self.roll = double_spin(0, -180, 180, 5, 0, " deg")
        model.addRow("Roll", self.roll)
        self.target_width = double_spin(140, 20, 900, 10, 0, " mm")
        model.addRow("Target width", self.target_width)
        self.sample = double_spin(0.7, 0.2, 3.0, 0.1, 2, " mm")
        model.addRow("Sample step", self.sample)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(8, 0, 60, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.stroke = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        page.addRow("Line width", self.stroke)
        self.scale_pct = double_spin(100, 10, 1000, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.finish_controls()

    def build_svg(self):
        path = self.model_path.text().strip()
        if not path:
            raise ValueError("Choose an OBJ or STL file first.")
        QGuiApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            polylines = three_d_polylines(
                path,
                style=self.style.currentData(),
                yaw=self.yaw.value(),
                pitch=self.pitch.value(),
                roll=self.roll.value(),
                width_mm=self.page_w.value(),
                height_mm=self.page_h.value(),
                margin_mm=self.margin.value(),
                sample_mm=self.sample.value(),
                target_width_mm=self.target_width.value(),
            )
        finally:
            QGuiApplication.restoreOverrideCursor()
        polylines = scale_polylines(
            polylines,
            self.scale_pct.value() / 100.0,
            self.page_w.value(),
            self.page_h.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.stroke.value(),
            f"{len(polylines)} visible segments for 3D Wireframe.",
        )


def create_tab(host):
    return ThreeDTab(host)
