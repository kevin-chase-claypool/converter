import bisect
import math
import os
import sys
import time
from array import array

from PySide6.QtCore import QPointF, QTimer, Qt, QRectF
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QSurfaceFormat
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QColorDialog,
    QScrollArea,
    QSlider,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import converter_core as converter
print(f"[geometry version: {getattr(converter, 'GEOMETRY_VERSION', 'OLD-no-new-patterns')}]")

# Playback wall-clock multiplier: 1.0 = real time, so the toolhead animates at
# the configured print speed (mm/s). Bump up to fast-forward long jobs.
PLAYBACK_RATE = 1.0
PREVIEW_TRAVEL_MM_S = 100.0


def fmt(value):
    return converter.format_float(value)


class CollapsibleSection(QWidget):
    def __init__(self, title, content, expanded=True):
        super().__init__()
        self.toggle = QPushButton(title)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(bool(expanded))
        self.toggle.setStyleSheet("QPushButton { text-align: left; padding: 4px 6px; font-weight: 600; }")
        self.content = content
        self.content.setVisible(bool(expanded))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(self.toggle)
        layout.addWidget(self.content)
        self.toggle.toggled.connect(self.set_expanded)
        self.set_expanded(bool(expanded))

    def set_expanded(self, expanded):
        self.content.setVisible(bool(expanded))
        marker = "v" if expanded else ">"
        title = self.toggle.text()
        if title.startswith(("v ", "> ")):
            title = title[2:]
        self.toggle.setText(f"{marker} {title}")


class GLPreview(QOpenGLWidget):
    GL_LINES = 0x0001
    GL_FLOAT = 0x1406

    def __init__(self):
        super().__init__()
        self.contours = []
        self.moves = []
        self.progress = 0.0
        self.settings = converter.Settings()
        self.drawing_color = QColor("#2563eb")
        self.undrawn_color = QColor("#bcd0f5")
        self.motion_color = QColor("#be123c")
        self.gantry_color = QColor("#7f1d1d")
        self.fast_render = False
        self.preview_center = (0.0, 0.0)
        self.preview_radius = 1.0
        self.override_center = None
        self.machine_points = []
        self.theta_cache = [(0.0, 0.0)]
        self.cumulative_ms = [0.0]
        self.play_speed_mm_s = 100.0
        self.draw_count_at_move = []
        self.bounds_base = (-1.0, -1.0, 1.0, 1.0)
        self.zoom_factor = 1.0
        self.pan_offset = (0.0, 0.0)
        self.is_panning = False
        self.last_pan_pos = None
        self.program = None
        self.program_ok = False
        self.vertex_counts = {}
        self.vertex_arrays = {}
        self.vbos = {}
        self.dynamic_vbo = None
        self.dynamic_capacity = 0
        self.uniform_loc = {}
        self._vbos_dirty = False
        self._cached_bounds = None
        self._cached_bounds_key = None
        self.x_label = QLabel("X gantry", self)
        self.y_label = QLabel("Y gantry", self)
        for label in (self.x_label, self.y_label):
            label.setStyleSheet("color: #7f1d1d; background: transparent; font-size: 11px;")
            label.setAttribute(Qt.WA_TransparentForMouseEvents)
            label.hide()

    def initializeGL(self):
        funcs = self.context().functions()
        funcs.initializeOpenGLFunctions()
        funcs.glClearColor(1.0, 1.0, 1.0, 1.0)
        funcs.glDisable(0x0B71)  # GL_DEPTH_TEST
        funcs.glEnable(0x0BE2)   # GL_BLEND
        funcs.glBlendFunc(0x0302, 0x0303)

        self.program = QOpenGLShaderProgram(self)
        vertex_source = """attribute vec2 p;
            uniform vec2 center;
            uniform float theta;
            uniform vec4 bounds;
            void main() {
                float c = cos(theta);
                float s = sin(theta);
                vec2 d = p - center;
                vec2 r = center + vec2(d.x*c - d.y*s, d.x*s + d.y*c);
                vec2 n = (r - bounds.xy) / (bounds.zw - bounds.xy) * 2.0 - 1.0;
                gl_Position = vec4(n.x, n.y, 0.0, 1.0);
            }
        """
        fragment_source = """uniform vec4 color;
            void main() {
                gl_FragColor = color;
            }
        """
        if not self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, vertex_source):
            print("OpenGL vertex shader failed:", self.program.log())
        if not self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, fragment_source):
            print("OpenGL fragment shader failed:", self.program.log())
        self.program.bindAttributeLocation("p", 0)
        self.program_ok = self.program.link()
        if not self.program_ok:
            print("OpenGL shader link failed:", self.program.log())
            return
        self.uniform_loc = {
            "center": self.program.uniformLocation("center"),
            "theta": self.program.uniformLocation("theta"),
            "bounds": self.program.uniformLocation("bounds"),
            "color": self.program.uniformLocation("color"),
        }
        for name in ("bed_circle", "bed_radius", "debug_box", "debug_cross", "artwork", "drawn_path", "travel", "motion"):
            buf = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
            buf.setUsagePattern(QOpenGLBuffer.StaticDraw)
            buf.create()
            self.vbos[name] = buf
        self.dynamic_vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.dynamic_vbo.setUsagePattern(QOpenGLBuffer.StreamDraw)
        self.dynamic_vbo.create()
        self._vbos_dirty = bool(self.vertex_arrays)

    def set_preview(self, contours, moves, settings, center=None, play_speed_mm_s=None):
        self.contours = contours
        self.moves = moves
        self.settings = settings
        self.override_center = center
        if play_speed_mm_s is not None:
            self.play_speed_mm_s = max(float(play_speed_mm_s), 1e-9)
        self.progress = float(len(moves))
        self.rebuild_cache()
        self.update()

    def _playback_move_ms(self, move):
        # Use full coordinated motion length so theta-heavy smoothing changes
        # are visible in the simulated runtime.
        kind = move.get("type")
        if kind == "draw":
            dist = float(move.get("motion_length", move.get("xy_length", 0.0)))
            return dist / max(self.play_speed_mm_s, 1e-9) * 1000.0
        if kind == "travel" and ("motion_length" in move or "xy_length" in move):
            dist = float(move.get("xy_length", move.get("motion_length", 0.0)))
            return dist / PREVIEW_TRAVEL_MM_S * 1000.0
        return float(move.get("duration_ms", 0.0))

    def rebuild_timeline(self):
        cumulative = [0.0]
        for move in self.moves:
            cumulative.append(cumulative[-1] + max(1.0, self._playback_move_ms(move)))
        self.cumulative_ms = cumulative

    def set_play_speed(self, mm_s):
        self.play_speed_mm_s = max(float(mm_s), 1e-9)
        self.rebuild_timeline()

    def rebuild_cache(self):
        flat_points = [point for contour in self.contours for point in contour]
        if self.override_center is not None:
            self.preview_center = self.override_center
            bed_radius = max(float(getattr(self.settings, "bed_diameter_mm", 457.2)), 1.0) / 2.0
            if flat_points:
                art_radius = max(math.hypot(x - self.preview_center[0], y - self.preview_center[1]) for x, y in flat_points)
            else:
                art_radius = 0.0
            self.preview_radius = max(bed_radius, art_radius)
        elif flat_points:
            min_x, min_y, max_x, max_y = converter.contour_bounds(self.contours)
            self.preview_center = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
            bed_radius = max(float(getattr(self.settings, "bed_diameter_mm", 457.2)), 1.0) / 2.0
            art_radius = max(math.hypot(x - self.preview_center[0], y - self.preview_center[1]) for x, y in flat_points)
            self.preview_radius = max(bed_radius, art_radius)
        else:
            self.preview_center = (0.0, 0.0)
            self.preview_radius = 1.0

        bed_radius = max(float(getattr(self.settings, "bed_diameter_mm", 457.2)), 1.0) / 2.0
        bed_circle = []
        prev = (self.preview_center[0] + bed_radius, self.preview_center[1])
        for i in range(1, 241):
            a = i / 240.0 * math.pi * 2.0
            curr = (self.preview_center[0] + math.cos(a) * bed_radius, self.preview_center[1] + math.sin(a) * bed_radius)
            bed_circle.extend([prev[0], prev[1], curr[0], curr[1]])
            prev = curr
        bed_radius_line = [self.preview_center[0], self.preview_center[1], self.preview_center[0] + bed_radius, self.preview_center[1]]
        min_dbg = self.preview_center[0] - bed_radius
        max_dbg = self.preview_center[0] + bed_radius
        min_dy = self.preview_center[1] - bed_radius
        max_dy = self.preview_center[1] + bed_radius
        debug_box = [
            min_dbg, min_dy, max_dbg, min_dy,
            max_dbg, min_dy, max_dbg, max_dy,
            max_dbg, max_dy, min_dbg, max_dy,
            min_dbg, max_dy, min_dbg, min_dy,
        ]
        debug_cross = [
            self.preview_center[0] - bed_radius * 0.25, self.preview_center[1],
            self.preview_center[0] + bed_radius * 0.25, self.preview_center[1],
            self.preview_center[0], self.preview_center[1] - bed_radius * 0.25,
            self.preview_center[0], self.preview_center[1] + bed_radius * 0.25,
        ]

        artwork = []
        for contour in self.contours:
            for a, b in zip(contour, contour[1:]):
                artwork.extend([a[0], a[1], b[0], b[1]])

        travel = []
        motion = []
        drawn_path = []
        draw_count_at_move = []
        draw_segments = 0
        self.machine_points = []
        self.theta_cache = []
        self.cumulative_ms = [0.0]
        theta = (0.0, 0.0)
        for move in self.moves:
            self.cumulative_ms.append(self.cumulative_ms[-1] + max(1.0, self._playback_move_ms(move)))
            self.theta_cache.append(theta)
            start = move.get("start", self.preview_center)
            end = move.get("end", start)
            command_start = move.get("command_start", start)
            command_end = move.get("command_end", end)
            self.machine_points.extend([start, end, command_start, command_end])
            if move.get("type") == "travel":
                travel.extend([start[0], start[1], end[0], end[1]])
            elif move.get("type") == "draw":
                motion.extend([start[0], start[1], end[0], end[1]])
                bed_start = move.get("bed_start")
                bed_end = move.get("bed_end")
                if bed_start is not None and bed_end is not None:
                    # bed-frame artwork in draw order; the first K segments are
                    # the portion drawn so far (shown dark over the light base).
                    drawn_path.extend([bed_start[0], bed_start[1], bed_end[0], bed_end[1]])
                    draw_segments += 1
            draw_count_at_move.append(draw_segments)
            if "bed_theta" in move:
                theta = (move.get("bed_theta", 0.0), move.get("motor_theta", 0.0))
        self.theta_cache.append(theta)
        self.draw_count_at_move = draw_count_at_move

        base_points = [
            (self.preview_center[0] - self.preview_radius, self.preview_center[1] - self.preview_radius),
            (self.preview_center[0] + self.preview_radius, self.preview_center[1] + self.preview_radius),
        ] + self.machine_points
        min_x = min(x for x, _ in base_points)
        max_x = max(x for x, _ in base_points)
        min_y = min(y for _, y in base_points)
        max_y = max(y for _, y in base_points)
        pad = max(self.preview_radius * 0.08, 10.0)
        self.bounds_base = (min_x - pad, min_y - pad, max_x + pad, max_y + pad)

        self.vertex_arrays = {
            "bed_circle": array("f", bed_circle),
            "bed_radius": array("f", bed_radius_line),
            "debug_box": array("f", debug_box),
            "debug_cross": array("f", debug_cross),
            "artwork": array("f", artwork),
            "drawn_path": array("f", drawn_path),
            "travel": array("f", travel),
            "motion": array("f", motion),
        }
        self.vertex_counts = {name: len(values) // 2 for name, values in self.vertex_arrays.items()}
        self._vbos_dirty = True
        self._cached_bounds = None
        self._cached_bounds_key = None

    def resizeGL(self, width, height):
        funcs = self.context().functions()
        funcs.glViewport(0, 0, max(1, width), max(1, height))
        self._cached_bounds = None
        self._cached_bounds_key = None

    def invalidate_bounds(self):
        self._cached_bounds = None
        self._cached_bounds_key = None

    def set_zoom(self, factor):
        self.zoom_factor = max(0.1, min(float(factor), 20.0))
        self.invalidate_bounds()
        self.update()

    def zoom_in(self):
        self.set_zoom(self.zoom_factor * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom_factor / 1.25)

    def reset_zoom(self):
        self.pan_offset = (0.0, 0.0)
        self.set_zoom(1.0)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        self.set_zoom(self.zoom_factor * (1.15 if delta > 0 else 1.0 / 1.15))
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_pan_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_panning and self.last_pan_pos is not None:
            current = event.position()
            dx = current.x() - self.last_pan_pos.x()
            dy = current.y() - self.last_pan_pos.y()
            min_x, min_y, max_x, max_y = self.adjusted_bounds()
            span_x = max(max_x - min_x, 1e-9)
            span_y = max(max_y - min_y, 1e-9)
            self.pan_offset = (
                self.pan_offset[0] - dx / max(self.width(), 1) * span_x,
                self.pan_offset[1] + dy / max(self.height(), 1) * span_y,
            )
            self.last_pan_pos = current
            self.invalidate_bounds()
            self.update()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_panning:
            self.is_panning = False
            self.last_pan_pos = None
            self.unsetCursor()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.reset_zoom()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def set_fast_render(self, enabled):
        self.fast_render = bool(enabled)
        self.update()

    def set_index(self, index):
        self.progress = max(0.0, min(float(index), float(len(self.moves))))
        self.update()

    def set_colors(self, drawing_color=None, motion_color=None, undrawn_color=None):
        if drawing_color is not None:
            self.drawing_color = QColor(drawing_color)
        if undrawn_color is not None:
            self.undrawn_color = QColor(undrawn_color)
        if motion_color is not None:
            self.motion_color = QColor(motion_color)
            self.gantry_color = QColor(motion_color).darker(140)
        self.update()

    def active_theta(self):
        return self.theta_at_progress(self.progress)

    def theta_before(self, index):
        if not self.theta_cache:
            return 0.0, 0.0
        index = max(0, min(index, len(self.theta_cache) - 1))
        return self.theta_cache[index]

    def theta_at_progress(self, progress):
        if not self.moves or progress <= 0:
            return 0.0, 0.0
        if progress >= len(self.moves):
            return self.theta_before(len(self.moves))
        index = int(math.floor(progress))
        frac = progress - index
        move = self.moves[index]
        start_theta, start_motor = self.theta_before(index)
        end_theta = move.get("bed_theta", start_theta)
        end_motor = move.get("motor_theta", start_motor)
        return (
            start_theta + (end_theta - start_theta) * frac,
            start_motor + (end_motor - start_motor) * frac,
        )

    def draw_segments_done(self, progress):
        if not self.draw_count_at_move:
            return 0
        idx = int(math.floor(max(0.0, min(progress, float(len(self.moves))))))
        idx = max(0, min(idx, len(self.draw_count_at_move) - 1))
        return self.draw_count_at_move[idx]

    def active_move_at_progress(self, progress):
        if not self.moves:
            return None, 0, 0.0
        if progress >= len(self.moves):
            return self.moves[-1], len(self.moves) - 1, 1.0
        index = max(0, min(int(math.floor(progress)), len(self.moves) - 1))
        return self.moves[index], index, max(0.0, min(progress - index, 1.0))

    def interpolate_point(self, progress, start_key, end_key, fallback_start="start", fallback_end="end"):
        if not self.moves:
            return None
        move, _index, frac = self.active_move_at_progress(progress)
        if progress >= len(self.moves):
            frac = 1.0
        start = move.get(start_key, move.get(fallback_start, move.get(fallback_end)))
        end = move.get(end_key, move.get(fallback_end, start))
        return (
            start[0] + (end[0] - start[0]) * frac,
            start[1] + (end[1] - start[1]) * frac,
        )

    def tool_point_at_progress(self, progress):
        return self.interpolate_point(progress, "start", "end")

    def command_point_at_progress(self, progress):
        return self.interpolate_point(progress, "command_start", "command_end")

    def adjusted_bounds(self):
        key = (self.width(), self.height(), self.bounds_base, self.zoom_factor, self.pan_offset)
        if self._cached_bounds is not None and self._cached_bounds_key == key:
            return self._cached_bounds
        min_x, min_y, max_x, max_y = self.bounds_base
        span_x = max(max_x - min_x, 1e-9)
        span_y = max(max_y - min_y, 1e-9)
        view_aspect = max(self.width(), 1) / max(self.height(), 1)
        bounds_aspect = span_x / span_y
        if bounds_aspect < view_aspect:
            extra = span_y * view_aspect - span_x
            min_x -= extra / 2.0
            max_x += extra / 2.0
        else:
            extra = span_x / view_aspect - span_y
            min_y -= extra / 2.0
            max_y += extra / 2.0
        if self.zoom_factor != 1.0:
            cx = (min_x + max_x) / 2.0
            cy = (min_y + max_y) / 2.0
            half_x = (max_x - min_x) / (2.0 * self.zoom_factor)
            half_y = (max_y - min_y) / (2.0 * self.zoom_factor)
            min_x, max_x = cx - half_x, cx + half_x
            min_y, max_y = cy - half_y, cy + half_y
        pan_x, pan_y = self.pan_offset
        min_x += pan_x
        max_x += pan_x
        min_y += pan_y
        max_y += pan_y
        bounds = (min_x, min_y, max_x, max_y)
        self._cached_bounds = bounds
        self._cached_bounds_key = key
        return bounds

    def screen_from_world(self, point, bounds):
        min_x, min_y, max_x, max_y = bounds
        x = (point[0] - min_x) / max(max_x - min_x, 1e-9) * self.width()
        y = self.height() - (point[1] - min_y) / max(max_y - min_y, 1e-9) * self.height()
        return x, y

    def update_overlay_labels(self, command_point, bounds):
        if not self.moves:
            self.x_label.hide()
            self.y_label.hide()
            return
        sx, sy = self.screen_from_world(command_point, bounds)
        self.x_label.move(8, max(0, min(int(sy) - 18, self.height() - 18)))
        self.y_label.move(max(0, min(int(sx) + 8, self.width() - 70)), 4)
        self.x_label.show()
        self.y_label.show()

    def color_tuple(self, color):
        q = color if isinstance(color, QColor) else QColor(color)
        return (q.redF(), q.greenF(), q.blueF(), q.alphaF())

    def set_color(self, color):
        loc = self.uniform_loc.get("color", -1)
        if loc < 0:
            return
        r, g, b, a = self.color_tuple(color)
        self.program.setUniformValue(loc, float(r), float(g), float(b), float(a))

    def upload_static_vbos(self):
        for name, arr in self.vertex_arrays.items():
            buf = self.vbos.get(name)
            if buf is None or not arr:
                continue
            data = bytes(arr)
            buf.bind()
            buf.allocate(data, len(data))
            buf.release()
        self._vbos_dirty = False

    def draw_static(self, name, color, width=1.0, count=None):
        total = self.vertex_counts.get(name, 0)
        if count is None:
            count = total
        else:
            count = max(0, min(count, total))
        if count <= 0:
            return
        buf = self.vbos.get(name)
        if buf is None:
            return
        funcs = self.context().functions()
        self.set_color(color)
        funcs.glLineWidth(float(width))
        buf.bind()
        self.program.enableAttributeArray(0)
        self.program.setAttributeBuffer(0, self.GL_FLOAT, 0, 2, 0)
        funcs.glDrawArrays(self.GL_LINES, 0, count)
        self.program.disableAttributeArray(0)
        buf.release()

    def draw_dynamic_lines(self, values, color, width=1.0):
        if not values:
            return
        funcs = self.context().functions()
        data = bytes(array("f", values))
        size = len(data)
        self.dynamic_vbo.bind()
        if size > self.dynamic_capacity:
            self.dynamic_vbo.allocate(data, size)
            self.dynamic_capacity = size
        else:
            self.dynamic_vbo.write(0, data, size)
        self.set_color(color)
        funcs.glLineWidth(float(width))
        self.program.enableAttributeArray(0)
        self.program.setAttributeBuffer(0, self.GL_FLOAT, 0, 2, 0)
        funcs.glDrawArrays(self.GL_LINES, 0, len(values) // 2)
        self.program.disableAttributeArray(0)
        self.dynamic_vbo.release()

    def marker_square(self, point, size):
        x, y = point
        return [
            x - size, y - size, x + size, y - size,
            x + size, y - size, x + size, y + size,
            x + size, y + size, x - size, y + size,
            x - size, y + size, x - size, y - size,
        ]

    def paintGL(self):
        funcs = self.context().functions()
        funcs.glClearColor(1.0, 1.0, 1.0, 1.0)
        funcs.glClear(0x00004000)  # GL_COLOR_BUFFER_BIT
        if self.program is None or not self.program_ok or not self.contours:
            return
        if self._vbos_dirty:
            self.upload_static_vbos()

        progress = max(0.0, min(self.progress, float(len(self.moves))))
        active, _active_index, _active_frac = self.active_move_at_progress(progress)
        bed_theta, _motor_theta = self.active_theta()
        tool_point = self.tool_point_at_progress(progress) or self.preview_center
        command_point = self.command_point_at_progress(progress) or tool_point
        bounds = self.adjusted_bounds()
        self.update_overlay_labels(command_point, bounds)

        self.program.bind()
        bed_theta_rad = math.radians(bed_theta)
        min_x, min_y, max_x, max_y = bounds
        self.program.setUniformValue(self.uniform_loc["center"], float(self.preview_center[0]), float(self.preview_center[1]))
        self.program.setUniformValue(self.uniform_loc["bounds"], float(min_x), float(min_y), float(max_x), float(max_y))

        # Bed-attached geometry rotates with the bed.
        self.program.setUniformValue1f(self.uniform_loc["theta"], float(bed_theta_rad))
        self.draw_static("bed_circle", QColor("#94a3b8"), 1.5)
        self.draw_static("debug_box", QColor("#e5e7eb"), 1.0)
        self.draw_static("debug_cross", QColor("#111827"), 2.0)
        # Full artwork in the undrawn color, then overdraw the portion drawn so
        # far in the drawn color — the boundary tracks where the pen is.
        self.draw_static("artwork", self.undrawn_color, 1.0)
        drawn_segments = self.draw_segments_done(progress)
        if drawn_segments > 0:
            self.draw_static("drawn_path", self.drawing_color, 1.6, count=drawn_segments * 2)
        self.draw_static("bed_radius", QColor("#0f766e"), 2.0)

        # Machine-frame geometry — no bed rotation.
        self.program.setUniformValue1f(self.uniform_loc["theta"], 0.0)
        self.draw_static("travel", QColor("#cbd5e1"), 1.0)
        self.draw_static("motion", self.motion_color.lighter(155), 1.0)

        if active is not None and active.get("type") in ("draw", "travel"):
            self.draw_dynamic_lines(
                [active["start"][0], active["start"][1], active["end"][0], active["end"][1]],
                self.motion_color if active.get("type") == "draw" else QColor("#6b7280"),
                3.0,
            )

        crosshair = [
            min_x, command_point[1], max_x, command_point[1],
            command_point[0], min_y, command_point[0], max_y,
        ]
        pen_connector = [command_point[0], command_point[1], tool_point[0], tool_point[1]]
        tool_marker = self.marker_square(tool_point, (max_x - min_x) * 0.0045)
        pen_tip_bed = [
            command_point[0] - 8, command_point[1] - 8,
            command_point[0] + 8, command_point[1] - 8,
            command_point[0] + 8, command_point[1] - 8,
            command_point[0] + 8, command_point[1] + 8,
            command_point[0] + 8, command_point[1] + 8,
            command_point[0] - 8, command_point[1] + 8,
            command_point[0] - 8, command_point[1] + 8,
            command_point[0] - 8, command_point[1] - 8,
        ]
        self.draw_dynamic_lines(crosshair, self.gantry_color, 1.0)
        self.draw_dynamic_lines(pen_connector, QColor("#111827"), 1.0)
        self.draw_dynamic_lines(pen_tip_bed, QColor("#f59e0b"), 2.0)
        self.draw_dynamic_lines(tool_marker, self.motion_color if active and active.get("type") == "draw" else QColor("#6b7280"), 2.0)
        self.program.release()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SVG to XY Theta G-code Converter - OpenGL")
        self.resize(1500, 950)
        self.moves = []
        self.contours = []
        self.raw_contours = None
        self.raw_cache_key = None
        self.preview_index = 0
        self.preview_progress = 0.0
        self.drawing_color = QColor("#2563eb")
        self.undrawn_color = QColor("#bcd0f5")
        self.motion_color = QColor("#be123c")
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self.play_step)
        self.play_last_time = None
        self.play_start_time = None
        self.play_start_progress = 0.0
        self.last_command_follow_time = 0.0
        self.auto_gcode_path = ""
        self.build_ui()

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        file_row = QHBoxLayout()
        self.svg_path = QLineEdit()
        self.gcode_path = QLineEdit()
        file_row.addWidget(QLabel("SVG"))
        file_row.addWidget(self.svg_path, 3)
        file_row.addWidget(QPushButton("Browse", clicked=self.pick_svg))
        file_row.addWidget(QLabel("G-code"))
        file_row.addWidget(self.gcode_path, 3)
        file_row.addWidget(QPushButton("Browse", clicked=self.pick_gcode))
        main_layout.addLayout(file_row)

        self.fields = {}
        self.field_rows = {}
        field_groups = dict(converter.TEXT_FIELD_GROUPS)

        def make_form_group(title, items):
            box = QGroupBox(title)
            form = QFormLayout(box)
            form.setLabelAlignment(Qt.AlignRight)
            form.setHorizontalSpacing(6)
            form.setVerticalSpacing(2)
            form.setContentsMargins(8, 6, 8, 6)
            for label, key, value in items:
                if key == "hatch_pattern":
                    edit = QComboBox()
                    edit.addItems([
                        "linear",
                        "crosshatch",
                        "diagonal",
                        "diagonal_crosshatch",
                        "triangular",
                        "cubic",
                        "diamonds",
                        "hexagonal",
                        "circles",
                        "dots",
                        "waves",
                        "gyroid",
                        "concentric",
                    ])
                    edit.setCurrentText(value)
                else:
                    edit = QLineEdit(value)
                    edit.setMaximumWidth(120)
                label_widget = QLabel(label)
                self.fields[key] = edit
                self.field_rows[key] = (label_widget, edit)
                form.addRow(label_widget, edit)
            return box, form

        checkbox_meta = {key: (label, checked) for _group, key, label, checked in converter.CHECKBOX_FIELDS}

        def make_checkbox(key):
            label, checked = checkbox_meta[key]
            widget = QCheckBox(label)
            widget.setChecked(bool(checked))
            return widget

        self.flip_y = make_checkbox("flip_y")
        self.use_z = make_checkbox("include_z")
        self.preview_xy = make_checkbox("preview_xy_only")
        self.compensate_pen = make_checkbox("compensate_pen_width")
        self.monotonic_theta = make_checkbox("monotonic_theta")
        self.raster_shading = make_checkbox("raster_shading")

        geometry_box, geometry_form = make_form_group("Geometry", field_groups["Geometry"])
        geometry_form.addRow(self.flip_y)
        geometry_form.addRow(self.compensate_pen)

        shading_box, shading_form = make_form_group("Shading", field_groups["Shading"])
        shading_form.addRow(self.raster_shading)

        motion_box, _motion_form = make_form_group("Motion", field_groups["Motion"])

        theta_box, theta_form = make_form_group("Theta kinematics", field_groups["Theta kinematics"])
        theta_form.addRow(self.monotonic_theta)

        pen_box, pen_form = make_form_group("Pen", field_groups["Pen"])
        pen_form.addRow(self.use_z)

        self.undrawn_color_button = QPushButton("Undrawn")
        self.undrawn_color_button.clicked.connect(lambda: self.choose_preview_color("undrawn"))
        self.drawing_color_button = QPushButton("Drawn")
        self.drawing_color_button.clicked.connect(lambda: self.choose_preview_color("drawing"))
        self.motion_color_button = QPushButton("Motion")
        self.motion_color_button.clicked.connect(lambda: self.choose_preview_color("motion"))
        color_widget = QWidget()
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(4)
        color_layout.addWidget(self.undrawn_color_button)
        color_layout.addWidget(self.drawing_color_button)
        color_layout.addWidget(self.motion_color_button)

        preview_box, preview_form = make_form_group("Preview settings", field_groups["Preview settings"])
        preview_form.addRow(QLabel("Colors"), color_widget)

        other_box = QGroupBox("Other settings")
        other_layout = QVBoxLayout(other_box)
        other_layout.setContentsMargins(8, 6, 8, 6)
        other_layout.setSpacing(2)
        other_layout.addWidget(self.preview_xy)
        other_layout.addStretch(1)

        actions = QHBoxLayout()
        actions.addWidget(QPushButton("Preview", clicked=self.preview))
        actions.addWidget(QPushButton("Save G-code", clicked=self.convert))

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(4)
        sidebar_layout.addWidget(CollapsibleSection("Geometry", geometry_box, True))
        sidebar_layout.addWidget(CollapsibleSection("Shading", shading_box, True))
        sidebar_layout.addWidget(CollapsibleSection("Motion", motion_box, True))
        sidebar_layout.addWidget(CollapsibleSection("Theta kinematics", theta_box, False))
        sidebar_layout.addWidget(CollapsibleSection("Pen", pen_box, False))
        sidebar_layout.addWidget(CollapsibleSection("Preview settings", preview_box, False))
        sidebar_layout.addWidget(CollapsibleSection("Other settings", other_box, False))
        sidebar_layout.addLayout(actions)
        sidebar_layout.addStretch(1)
        sidebar.setMaximumWidth(320)
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setWidget(sidebar)
        sidebar_scroll.setMaximumWidth(340)

        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(2)
        self.gl_preview = GLPreview()
        preview_layout.addWidget(self.gl_preview, 1)

        controls = QHBoxLayout()
        controls.addWidget(QPushButton("|<", clicked=lambda: self.set_index(0)))
        controls.addWidget(QPushButton("<", clicked=lambda: self.set_index(self.preview_index - 1)))
        controls.addWidget(QPushButton("Play", clicked=self.play))
        controls.addWidget(QPushButton("Pause", clicked=self.pause))
        controls.addWidget(QPushButton(">", clicked=lambda: self.set_index(self.preview_index + 1)))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.set_index)
        controls.addWidget(self.slider, 1)
        controls.addWidget(QPushButton(">|", clicked=lambda: self.set_index(len(self.moves))))
        preview_layout.addLayout(controls)

        self.status = QLabel("Choose an SVG to build a preview.")
        self.status.setWordWrap(True)
        preview_layout.addWidget(self.status)
        self.estimate = QLabel("Estimated time: preview an SVG to calculate.")
        self.estimate.setWordWrap(True)
        preview_layout.addWidget(self.estimate)

        self.command_list = QListWidget()
        mono = QFont("Consolas", 9)
        self.command_list.setFont(mono)
        self.command_list.currentRowChanged.connect(self.command_selected)

        main_split = QSplitter(Qt.Horizontal)
        main_split.addWidget(sidebar_scroll)
        main_split.addWidget(preview_widget)
        main_split.addWidget(self.command_list)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)
        main_split.setStretchFactor(2, 0)
        main_split.setSizes([300, 1100, 320])
        main_layout.addWidget(main_split, 1)

        self.log = QTextEdit()
        self.log.setMaximumHeight(60)
        self.log.setReadOnly(True)
        main_layout.addWidget(self.log)

        self.update_color_buttons()
        self.fields["print_speed"].textChanged.connect(lambda _text: self.on_print_speed_changed())
        self.fields["hatch_pattern"].currentTextChanged.connect(lambda _text: self.update_pattern_settings())
        self.raster_shading.toggled.connect(lambda _checked: self.update_pattern_settings())
        self.update_pattern_settings()

    def pick_svg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose SVG", "", "SVG files (*.svg);;All files (*.*)")
        if path:
            self.svg_path.setText(path)
            self.update_suggested_gcode_path(path)
            self.auto_configure_shading(path)
            self.raw_cache_key = None
            self.raw_contours = None
            self.log.append("SVG selected. Press Preview to regenerate.")

    def update_suggested_gcode_path(self, svg_path):
        if not svg_path:
            return
        suggested_gcode = os.path.splitext(svg_path)[0] + ".gcode"
        current_gcode = self.gcode_path.text().strip()
        if not current_gcode or current_gcode == self.auto_gcode_path:
            self.gcode_path.setText(suggested_gcode)
            self.auto_gcode_path = suggested_gcode

    def svg_tone_stats(self, svg_path):
        renderer = QSvgRenderer(svg_path)
        view = renderer.viewBoxF()
        if view.isNull() or view.width() <= 0 or view.height() <= 0:
            size = renderer.defaultSize()
            view = QRectF(0.0, 0.0, float(size.width()), float(size.height()))
        if view.isNull() or view.width() <= 0 or view.height() <= 0:
            return None
        max_dim = 160
        scale = max(view.width() / max_dim, view.height() / max_dim, 1.0)
        width = max(1, int(math.ceil(view.width() / scale)))
        height = max(1, int(math.ceil(view.height() / scale)))
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(QColor(255, 255, 255, 0))
        painter = QPainter(image)
        renderer.render(painter, QRectF(0.0, 0.0, float(width), float(height)))
        painter.end()

        values = []
        step = max(1, int(math.sqrt(max(width * height, 1) / 4000.0)))
        for y in range(0, height, step):
            for x in range(0, width, step):
                color = image.pixelColor(x, y)
                alpha = color.alphaF()
                if alpha <= 0.02:
                    continue
                lum = 0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF()
                values.append(max(0.0, min((1.0 - lum) * alpha, 1.0)))
        if not values:
            return None
        values.sort()
        lo = values[int(len(values) * 0.05)]
        hi = values[int(len(values) * 0.95)]
        mean = sum(values) / len(values)
        return {"min": values[0], "max": values[-1], "p05": lo, "p95": hi, "mean": mean, "count": len(values)}

    def auto_configure_shading(self, svg_path):
        stats = self.svg_tone_stats(svg_path)
        if not stats:
            return
        tone_range = stats["p95"] - stats["p05"]
        shadeable = tone_range >= 0.18 and stats["p95"] >= 0.25
        if not shadeable:
            self.log.append("Auto shading: no meaningful tone variation detected; leaving raster shading off.")
            return
        self.raster_shading.setChecked(True)
        if float(self.fields["hatch_spacing_mm"].text() or 0.0) <= 0.0:
            self.fields["hatch_spacing_mm"].setText("4")
        if int(float(self.fields["shade_levels"].text() or 1)) < 4:
            self.fields["shade_levels"].setText("4")
        self.fields["shade_angle_step_deg"].setText("45")
        if float(self.fields["raster_px_per_unit"].text() or 0.0) < 2.0:
            self.fields["raster_px_per_unit"].setText("2")
        self.log.append(
            "Auto shading: tone variation detected "
            f"(p05 {fmt(stats['p05'])}, p95 {fmt(stats['p95'])}); raster shading enabled."
        )

    def pick_gcode(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save G-code", "", "G-code files (*.gcode *.nc *.tap);;All files (*.*)")
        if path:
            self.gcode_path.setText(path)
            self.auto_gcode_path = ""

    def update_color_buttons(self):
        for button, color in (
            (self.undrawn_color_button, self.undrawn_color),
            (self.drawing_color_button, self.drawing_color),
            (self.motion_color_button, self.motion_color),
        ):
            text_color = "#ffffff" if color.lightness() < 128 else "#111827"
            button.setStyleSheet(
                f"QPushButton {{ background-color: {color.name()}; color: {text_color}; border: 1px solid #6b7280; padding: 4px 12px; }}"
            )

    def choose_preview_color(self, target):
        current = {
            "undrawn": self.undrawn_color,
            "drawing": self.drawing_color,
            "motion": self.motion_color,
        }.get(target, self.drawing_color)
        color = QColorDialog.getColor(current, self, f"Choose {target} preview color")
        if not color.isValid():
            return
        if target == "undrawn":
            self.undrawn_color = color
        elif target == "drawing":
            self.drawing_color = color
        else:
            self.motion_color = color
        self.gl_preview.set_colors(self.drawing_color, self.motion_color, self.undrawn_color)
        self.update_color_buttons()

    def settings(self):
        text_values = {
            key: edit.currentText() if isinstance(edit, QComboBox) else edit.text()
            for key, edit in self.fields.items()
        }
        bool_values = {
            "flip_y": self.flip_y.isChecked(),
            "include_z": self.use_z.isChecked(),
            "preview_xy_only": self.preview_xy.isChecked(),
            "compensate_pen_width": self.compensate_pen.isChecked(),
            "monotonic_theta": self.monotonic_theta.isChecked(),
            "raster_shading": self.raster_shading.isChecked(),
        }
        return converter.settings_from_values(text_values, bool_values)

    def update_pattern_settings(self):
        pattern = converter.normalized_hatch_pattern(self.fields["hatch_pattern"].currentText())

        def set_visible(key, visible):
            row = self.field_rows.get(key)
            if not row:
                return
            label, widget = row
            label.setVisible(bool(visible))
            widget.setVisible(bool(visible))

        # Pattern-specific options. Hidden fields keep their value but do not
        # affect unrelated patterns.
        for pattern_name, field_name in converter.PATTERN_SIZE_FIELDS.items():
            set_visible(field_name, pattern == pattern_name)
        set_visible("shade_angle_step_deg", pattern in ("linear", "crosshatch", "diagonal", "diagonal_crosshatch", "cubic", "waves", "gyroid"))
        set_visible("raster_px_per_unit", self.raster_shading.isChecked())

    def pattern_size_values(self, settings):
        return converter.pattern_size_values(settings)

    def pattern_spacing(self, settings, pattern, fallback=None):
        if fallback is None:
            fallback = float(getattr(settings, "hatch_spacing_mm", 0.0))
        return converter.pattern_size_override(pattern, fallback, self.pattern_size_values(settings))

    def build_preview_moves(self, contours, settings):
        return converter.build_preview_moves(contours, settings)

    def raw_geometry_key(self, svg_path, settings):
        stat = os.stat(svg_path)
        return (
            os.path.abspath(svg_path),
            stat.st_mtime_ns,
            stat.st_size,
            float(settings.tolerance),
            bool(settings.flip_y),
            float(getattr(settings, "hatch_spacing_mm", 0.0)),
            float(getattr(settings, "hatch_angle_deg", 0.0)),
            str(getattr(settings, "hatch_pattern", "crosshatch")).lower(),
            tuple(sorted(self.pattern_size_values(settings).items())),
            int(getattr(settings, "shade_levels", 1)),
            float(getattr(settings, "shade_angle_step_deg", 90.0)),
            bool(getattr(settings, "raster_shading", False)),
            float(getattr(settings, "raster_px_per_unit", 2.0)),
        )

    def raster_shade_contours(self, svg_path, settings):
        spacing = float(getattr(settings, "hatch_spacing_mm", 0.0))
        if spacing <= 0:
            return []
        levels = max(1, int(getattr(settings, "shade_levels", 1)))
        px_per_unit = max(float(getattr(settings, "raster_px_per_unit", 2.0)), 0.1)
        renderer = QSvgRenderer(svg_path)
        view = renderer.viewBoxF()
        if view.isNull() or view.width() <= 0 or view.height() <= 0:
            size = renderer.defaultSize()
            view = QRectF(0.0, 0.0, float(size.width()), float(size.height()))
        max_dim = 2400
        width = max(1, int(math.ceil(view.width() * px_per_unit)))
        height = max(1, int(math.ceil(view.height() * px_per_unit)))
        scale_down = max(width / max_dim, height / max_dim, 1.0)
        if scale_down > 1.0:
            px_per_unit /= scale_down
            width = max(1, int(math.ceil(view.width() * px_per_unit)))
            height = max(1, int(math.ceil(view.height() * px_per_unit)))

        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(QColor(255, 255, 255, 0))
        painter = QPainter(image)
        renderer.render(painter, QRectF(0.0, 0.0, float(width), float(height)))
        painter.end()

        def darkness_at(x, y):
            px = int((x - view.left()) * px_per_unit)
            py = int((y - view.top()) * px_per_unit)
            if px < 0 or py < 0 or px >= width or py >= height:
                return 0.0
            color = image.pixelColor(px, py)
            alpha = color.alphaF()
            if alpha <= 0.0:
                return 0.0
            lum = 0.2126 * color.redF() + 0.7152 * color.greenF() + 0.0722 * color.blueF()
            return max(0.0, min((1.0 - lum) * alpha, 1.0))

        def maybe_flip(point):
            if not settings.flip_y:
                return point
            return (point[0], view.top() + view.bottom() - point[1])

        corners = [
            (view.left(), view.top()),
            (view.right(), view.top()),
            (view.right(), view.bottom()),
            (view.left(), view.bottom()),
        ]
        contours = []
        base_angle = float(getattr(settings, "hatch_angle_deg", 0.0))
        angle_step = float(getattr(settings, "shade_angle_step_deg", 90.0))
        pattern = converter.normalized_hatch_pattern(getattr(settings, "hatch_pattern", "crosshatch"))
        active_spacing = self.pattern_spacing(settings, pattern, spacing)
        sample_step = max(0.5 / px_per_unit, min(active_spacing / 3.0, 1.0))
        min_segment = max(active_spacing * 0.5, sample_step * 2.0)

        def add_mark(center, radius, mark):
            if mark == "circles":
                steps = 18
                contours.append([
                    maybe_flip((
                        center[0] + math.cos(2.0 * math.pi * i / steps) * radius,
                        center[1] + math.sin(2.0 * math.pi * i / steps) * radius,
                    ))
                    for i in range(steps + 1)
                ])
            else:
                contours.append([
                    maybe_flip((center[0] - radius, center[1])),
                    maybe_flip((center[0] + radius, center[1])),
                ])

        def add_shape_if_dark(points, threshold):
            checks = list(points[:-1])
            checks.extend(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0) for a, b in zip(points, points[1:]))
            if all(view.left() <= x <= view.right() and view.top() <= y <= view.bottom() and darkness_at(x, y) >= threshold for x, y in checks):
                contours.append([maybe_flip(point) for point in points])

        seen_raster_segments = set()

        def add_segment_if_dark(a, b, threshold):
            length = converter.distance(a, b)
            if length <= 1e-9:
                return
            steps = max(1, int(math.ceil(length / max(sample_step, 1e-6))))
            active_start = None
            last_active = None

            def point_at(index):
                t = index / steps
                return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

            def flush():
                nonlocal active_start, last_active
                if active_start is None or last_active is None:
                    return
                if converter.distance(active_start, last_active) < max(sample_step * 0.75, 1e-6):
                    active_start = None
                    last_active = None
                    return
                key_a = (round(active_start[0], 5), round(active_start[1], 5))
                key_b = (round(last_active[0], 5), round(last_active[1], 5))
                key = tuple(sorted((key_a, key_b)))
                if key not in seen_raster_segments:
                    seen_raster_segments.add(key)
                    contours.append([maybe_flip(active_start), maybe_flip(last_active)])
                active_start = None
                last_active = None

            for index in range(steps + 1):
                point = point_at(index)
                x, y = point
                active = view.left() <= x <= view.right() and view.top() <= y <= view.bottom() and darkness_at(x, y) >= threshold
                if active:
                    if active_start is None:
                        active_start = point
                    last_active = point
                else:
                    flush()
            flush()

        def append_active_polyline(points, threshold):
            active = []

            def flush():
                if len(active) < 2:
                    return
                length = sum(converter.distance(a, b) for a, b in zip(active, active[1:]))
                if length >= min_segment:
                    contours.append([maybe_flip(point) for point in active])

            for point in points:
                x, y = point
                is_active = view.left() <= x <= view.right() and view.top() <= y <= view.bottom() and darkness_at(x, y) >= threshold
                if is_active:
                    active.append(point)
                else:
                    flush()
                    active = []
            flush()

        def rotated_bounds(angle_deg):
            angle = math.radians(angle_deg)
            ca, sa = math.cos(angle), math.sin(angle)
            cs, sn = math.cos(-angle), math.sin(-angle)
            rot_corners = [(x * cs - y * sn, x * sn + y * cs) for x, y in corners]
            return (
                ca,
                sa,
                min(x for x, _ in rot_corners),
                max(x for x, _ in rot_corners),
                min(y for _, y in rot_corners),
                max(y for _, y in rot_corners),
            )

        def raster_wave(angle_deg, threshold, raster_spacing):
            ca, sa, min_rx, max_rx, min_ry, max_ry = rotated_bounds(angle_deg)
            amplitude = raster_spacing * 0.42
            wavelength = raster_spacing * 2.0
            width = max_rx - min_rx + 4.0 * raster_spacing
            n_steps = max(8, int(width / max(wavelength, 1e-6) * 24))

            def world(x, y):
                return (x * ca - y * sa, x * sa + y * ca)

            y = math.floor((min_ry - raster_spacing) / raster_spacing) * raster_spacing
            row = 0
            while y <= max_ry + raster_spacing:
                phase = math.pi if row % 2 else 0.0
                points = [
                    world(
                        min_rx - 2.0 * raster_spacing + i * width / n_steps,
                        y + amplitude * math.sin(2.0 * math.pi * (i / n_steps) * (width / wavelength) + phase),
                    )
                    for i in range(n_steps + 1)
                ]
                append_active_polyline(points, threshold)
                y += raster_spacing
                row += 1

        def raster_gyroid(angle_deg, threshold, raster_spacing):
            ca, sa, min_rx, max_rx, min_ry, max_ry = rotated_bounds(angle_deg)
            margin = raster_spacing * 1.5
            min_rx -= margin
            max_rx += margin
            min_ry -= margin
            max_ry += margin
            cell = max(raster_spacing / 6.0, sample_step)
            k = 2.0 * math.pi / max(raster_spacing * 2.0, 1e-6)

            def field(x, y):
                return math.sin(x * k) * math.cos(y * k) + math.sin(y * k) * math.cos(x * k)

            def world(x, y):
                return (x * ca - y * sa, x * sa + y * ca)

            def interp(p0, v0, p1, v1):
                denom = v0 - v1
                t = 0.5 if abs(denom) < 1e-12 else max(0.0, min(1.0, v0 / denom))
                return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)

            y = math.floor(min_ry / cell) * cell
            while y < max_ry:
                x = math.floor(min_rx / cell) * cell
                while x < max_rx:
                    pts = [(x, y), (x + cell, y), (x + cell, y + cell), (x, y + cell)]
                    vals = [field(px, py) for px, py in pts]
                    crossings = []
                    for i, j in ((0, 1), (1, 2), (2, 3), (3, 0)):
                        vi, vj = vals[i], vals[j]
                        if (vi <= 0.0 < vj) or (vj <= 0.0 < vi):
                            crossings.append(interp(pts[i], vi, pts[j], vj))
                    if len(crossings) == 2:
                        add_segment_if_dark(world(*crossings[0]), world(*crossings[1]), threshold)
                    elif len(crossings) == 4:
                        add_segment_if_dark(world(*crossings[0]), world(*crossings[1]), threshold)
                        add_segment_if_dark(world(*crossings[2]), world(*crossings[3]), threshold)
                    x += cell
                y += cell

        def stitch_segments_to_polylines(segments, close_tol):
            endpoint_map = {}

            def key(point):
                return (round(point[0], 5), round(point[1], 5))

            for index, (a, b) in enumerate(segments):
                endpoint_map.setdefault(key(a), []).append((index, 0))
                endpoint_map.setdefault(key(b), []).append((index, 1))

            used = [False] * len(segments)

            def take_unused(endpoint_key):
                bucket = endpoint_map.get(endpoint_key)
                while bucket:
                    index, end = bucket.pop()
                    if not used[index]:
                        return index, end
                return None

            polylines = []
            for index, (a, b) in enumerate(segments):
                if used[index]:
                    continue
                used[index] = True
                line = [a, b]

                while True:
                    next_ref = take_unused(key(line[-1]))
                    if next_ref is None:
                        break
                    next_index, end = next_ref
                    used[next_index] = True
                    seg_a, seg_b = segments[next_index]
                    line.append(seg_b if end == 0 else seg_a)

                while True:
                    next_ref = take_unused(key(line[0]))
                    if next_ref is None:
                        break
                    next_index, end = next_ref
                    used[next_index] = True
                    seg_a, seg_b = segments[next_index]
                    line.insert(0, seg_b if end == 0 else seg_a)

                if len(line) >= 3 and converter.distance(line[0], line[-1]) <= close_tol:
                    line[-1] = line[0]
                polylines.append(line)
            return polylines

        def polygon_area2(points):
            pts = points[:-1] if len(points) > 1 and points[0] == points[-1] else points
            return sum(
                pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                for i in range(len(pts))
            ) if len(pts) >= 3 else 0.0

        def raster_threshold_loops(threshold, raster_spacing):
            step = max(sample_step, raster_spacing / 4.0)
            segments = []

            def interp(p0, v0, p1, v1):
                denom = v0 - v1
                t = 0.5 if abs(denom) < 1e-12 else max(0.0, min(1.0, v0 / denom))
                return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)

            y = view.top()
            while y < view.bottom():
                x = view.left()
                while x < view.right():
                    x1 = min(x + step, view.right())
                    y1 = min(y + step, view.bottom())
                    pts = [(x, y), (x1, y), (x1, y1), (x, y1)]
                    vals = [darkness_at(px, py) - threshold for px, py in pts]
                    crossings = []
                    for i, j in ((0, 1), (1, 2), (2, 3), (3, 0)):
                        vi, vj = vals[i], vals[j]
                        if (vi <= 0.0 < vj) or (vj <= 0.0 < vi):
                            crossings.append(interp(pts[i], vi, pts[j], vj))
                    if len(crossings) == 2:
                        segments.append((crossings[0], crossings[1]))
                    elif len(crossings) == 4:
                        segments.append((crossings[0], crossings[1]))
                        segments.append((crossings[2], crossings[3]))
                    x += step
                y += step
            min_area = max(raster_spacing * raster_spacing * 0.25, step * step)
            loops = []
            for line in stitch_segments_to_polylines(segments, step * 1.5):
                if len(line) >= 4 and line[0] == line[-1] and abs(polygon_area2(line)) >= min_area:
                    loops.append(line)
            return loops

        def raster_concentric(threshold, raster_spacing):
            loops = raster_threshold_loops(threshold, raster_spacing)
            for contour in converter.concentric_region_contours(loops, raster_spacing):
                if len(contour) >= 3:
                    contours.append([maybe_flip(point) for point in contour])

        if pattern in ("circles", "dots", "diamonds", "hexagonal", "triangular"):
            angle = math.radians(base_angle)
            ca, sa = math.cos(angle), math.sin(angle)
            cs, sn = math.cos(-angle), math.sin(-angle)
            rot_corners = [(x * cs - y * sn, x * sn + y * cs) for x, y in corners]
            min_rx = min(x for x, _ in rot_corners)
            max_rx = max(x for x, _ in rot_corners)
            min_ry = min(y for _, y in rot_corners)
            max_ry = max(y for _, y in rot_corners)

            def world(x, y):
                return (x * ca - y * sa, x * sa + y * ca)

        if pattern == "dots":
            for layer in range(levels):
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                mark_radius = max(layer_spacing * 0.055, sample_step)
                row_step = layer_spacing * math.sqrt(3.0) / 2.0
                y = min_ry + row_step * 0.5
                row = 0
                while y <= max_ry:
                    x = min_rx + layer_spacing * (0.5 if row % 2 == 0 else 1.0)
                    while x <= max_rx:
                        center = world(x, y)
                        dot = [(center[0] - mark_radius, center[1]), (center[0] + mark_radius, center[1])]
                        if all(view.left() <= px <= view.right() and view.top() <= py <= view.bottom() and darkness_at(px, py) >= threshold for px, py in dot):
                            add_mark(center, mark_radius, pattern)
                        x += layer_spacing
                    y += row_step
                    row += 1
            return contours

        if pattern == "circles":
            steps = 18
            for layer in range(levels):
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                radius = max(layer_spacing * 0.5, sample_step)
                row_step = radius * math.sqrt(3.0)
                y = min_ry + radius
                row = 0
                while y <= max_ry - radius:
                    x = min_rx + radius + (radius if row % 2 else 0.0)
                    while x <= max_rx - radius:
                        circle = [world(x + math.cos(2.0 * math.pi * i / steps) * radius, y + math.sin(2.0 * math.pi * i / steps) * radius) for i in range(steps + 1)]
                        add_shape_if_dark(circle, threshold)
                        x += radius * 2.0
                    y += row_step
                    row += 1
            return contours

        if pattern == "hexagonal":
            for layer in range(levels):
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                radius = max(layer_spacing * 0.5, sample_step)
                x_step = radius * 1.5
                y_step = radius * math.sqrt(3.0)
                col = 0
                x = min_rx - radius
                while x <= max_rx + radius:
                    y = min_ry - radius + (y_step * 0.5 if col % 2 else 0.0)
                    while y <= max_ry + radius:
                        hexagon = [world(x + math.cos(math.radians(60.0 * i)) * radius, y + math.sin(math.radians(60.0 * i)) * radius) for i in range(7)]
                        for a, b in zip(hexagon, hexagon[1:]):
                            add_segment_if_dark(a, b, threshold)
                        y += y_step
                    x += x_step
                    col += 1
            return contours

        if pattern == "diamonds":
            for layer in range(levels):
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                half = max(layer_spacing * 0.5, sample_step)
                x_min = int(math.floor((min_rx - half) / half)) - 1
                x_max = int(math.ceil((max_rx + half) / half)) + 1
                y_min = int(math.floor((min_ry - half) / half)) - 1
                y_max = int(math.ceil((max_ry + half) / half)) + 1
                for j in range(y_min, y_max + 1):
                    y = j * half
                    for i in range(x_min, x_max + 1):
                        x = i * half
                        add_segment_if_dark(world(x, y), world(x + half, y + half), threshold)
                        add_segment_if_dark(world(x, y), world(x + half, y - half), threshold)
            return contours

        if pattern == "triangular":
            for layer in range(levels):
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                side = max(layer_spacing, sample_step * 2.0)
                row_step = side * math.sqrt(3.0) / 2.0
                i_min = int(math.floor((min_rx - side) / side)) - 1
                i_max = int(math.ceil((max_rx + side) / side)) + 1
                j_min = int(math.floor((min_ry - row_step) / row_step)) - 1
                j_max = int(math.ceil((max_ry + row_step) / row_step)) + 1

                def tri_point(i, j):
                    return (i * side + (0.5 * side if j % 2 else 0.0), j * row_step)

                for j in range(j_min, j_max + 1):
                    for i in range(i_min, i_max + 1):
                        p = tri_point(i, j)
                        add_segment_if_dark(world(*p), world(*tri_point(i + 1, j)), threshold)
                        add_segment_if_dark(world(*p), world(*tri_point(i, j + 1)), threshold)
                        add_segment_if_dark(world(*p), world(*tri_point(i - 1, j + 1)), threshold)
            return contours

        if pattern == "waves":
            for layer in range(levels):
                raster_wave(base_angle, (layer + 1) / (levels + 1), active_spacing / math.sqrt(layer + 1))
            return contours

        if pattern == "gyroid":
            for layer in range(levels):
                raster_gyroid(base_angle, (layer + 1) / (levels + 1), active_spacing / math.sqrt(layer + 1))
            return contours

        if pattern == "concentric":
            for layer in range(levels):
                raster_concentric((layer + 1) / (levels + 1), active_spacing / math.sqrt(layer + 1))
            return contours

        if pattern == "linear":
            offsets = (0.0,)
        elif pattern == "crosshatch":
            offsets = (0.0, 90.0)
        elif pattern == "diagonal":
            offsets = (45.0,)
        elif pattern == "diagonal_crosshatch":
            offsets = (45.0, 135.0)
        elif pattern == "cubic":
            offsets = (30.0, 90.0, 150.0)
        else:
            offsets = (0.0, 90.0)

        for layer in range(levels):
            threshold = (layer + 1) / (levels + 1)
            raster_spacing = active_spacing / math.sqrt(layer + 1)
            for offset_angle in offsets:
                angle = math.radians(base_angle + offset_angle)
                ux, uy = math.cos(angle), math.sin(angle)
                nx, ny = -uy, ux
                s_values = [x * nx + y * ny for x, y in corners]
                t_values = [x * ux + y * uy for x, y in corners]
                s = min(s_values) - raster_spacing
                s_max = max(s_values) + raster_spacing
                t_min = min(t_values) - raster_spacing
                t_max = max(t_values) + raster_spacing
                while s <= s_max:
                    active_start = None
                    last_point = None
                    t = t_min
                    while t <= t_max:
                        x = ux * t + nx * s
                        y = uy * t + ny * s
                        inside = view.left() <= x <= view.right() and view.top() <= y <= view.bottom()
                        active = inside and darkness_at(x, y) >= threshold
                        if active:
                            point = (x, y)
                            if active_start is None:
                                active_start = point
                            last_point = point
                        elif active_start is not None and last_point is not None:
                            if converter.distance(active_start, last_point) >= min_segment:
                                contours.append([maybe_flip(active_start), maybe_flip(last_point)])
                            active_start = None
                            last_point = None
                        t += sample_step
                    if active_start is not None and last_point is not None and converter.distance(active_start, last_point) >= min_segment:
                        contours.append([maybe_flip(active_start), maybe_flip(last_point)])
                    s += raster_spacing
        return contours

    def concentric_from_closed_contours(self, contours, settings):
        spacing = self.pattern_spacing(settings, "concentric")
        if spacing <= 0:
            return []
        close_tol = max(float(getattr(settings, "tolerance", 0.25)) * 2.0, 0.5)
        polygons = []
        for contour in contours:
            if len(contour) < 4:
                continue
            polygon = list(contour)
            if converter.distance(polygon[0], polygon[-1]) > close_tol:
                continue
            polygon[-1] = polygon[0]
            polygons.append(polygon)
        if not polygons:
            return []

        bounds = converter.contour_bounds(polygons)
        min_x, min_y, max_x, max_y = bounds
        if max_x <= min_x or max_y <= min_y:
            return []

        px_per_unit = max(float(getattr(settings, "raster_px_per_unit", 2.0)), 0.25)
        margin = spacing * 2.0
        width = max(1, int(math.ceil((max_x - min_x + margin * 2.0) * px_per_unit)))
        height = max(1, int(math.ceil((max_y - min_y + margin * 2.0) * px_per_unit)))
        max_dim = 1800
        scale_down = max(width / max_dim, height / max_dim, 1.0)
        if scale_down > 1.0:
            px_per_unit /= scale_down
            width = max(1, int(math.ceil((max_x - min_x + margin * 2.0) * px_per_unit)))
            height = max(1, int(math.ceil((max_y - min_y + margin * 2.0) * px_per_unit)))

        def to_px(point):
            return (
                (point[0] - min_x + margin) * px_per_unit,
                (point[1] - min_y + margin) * px_per_unit,
            )

        def to_world(point):
            return (
                point[0] / px_per_unit + min_x - margin,
                point[1] / px_per_unit + min_y - margin,
            )

        path = QPainterPath()
        path.setFillRule(Qt.OddEvenFill)
        for polygon in polygons:
            px0, py0 = to_px(polygon[0])
            path.moveTo(px0, py0)
            for point in polygon[1:]:
                px, py = to_px(point)
                path.lineTo(px, py)
            path.closeSubpath()

        image = QImage(width, height, QImage.Format_Grayscale8)
        image.fill(0)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillPath(path, QColor(255, 255, 255))
        painter.end()

        bpl = image.bytesPerLine()
        data = bytes(image.constBits())
        total = width * height
        big = 1.0e9
        dist = [big] * total
        for y in range(height):
            row = y * width
            src = y * bpl
            for x in range(width):
                if data[src + x] == 0:
                    dist[row + x] = 0.0

        diag = math.sqrt(2.0)
        for y in range(height):
            row = y * width
            for x in range(width):
                i = row + x
                d = dist[i]
                if x:
                    d = min(d, dist[i - 1] + 1.0)
                if y:
                    d = min(d, dist[i - width] + 1.0)
                    if x:
                        d = min(d, dist[i - width - 1] + diag)
                    if x + 1 < width:
                        d = min(d, dist[i - width + 1] + diag)
                dist[i] = d
        for y in range(height - 1, -1, -1):
            row = y * width
            for x in range(width - 1, -1, -1):
                i = row + x
                d = dist[i]
                if x + 1 < width:
                    d = min(d, dist[i + 1] + 1.0)
                if y + 1 < height:
                    d = min(d, dist[i + width] + 1.0)
                    if x:
                        d = min(d, dist[i + width - 1] + diag)
                    if x + 1 < width:
                        d = min(d, dist[i + width + 1] + diag)
                dist[i] = d

        def interp(p0, v0, p1, v1):
            denom = v0 - v1
            t = 0.5 if abs(denom) < 1e-12 else max(0.0, min(1.0, v0 / denom))
            return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)

        def stitch_segments(segments):
            endpoint_map = {}

            def key(point):
                return (round(point[0], 4), round(point[1], 4))

            for index, (a, b) in enumerate(segments):
                endpoint_map.setdefault(key(a), []).append((index, 0))
                endpoint_map.setdefault(key(b), []).append((index, 1))
            used = [False] * len(segments)
            loops = []

            def take(endpoint_key):
                bucket = endpoint_map.get(endpoint_key)
                while bucket:
                    index, end = bucket.pop()
                    if not used[index]:
                        return index, end
                return None

            for index, (a, b) in enumerate(segments):
                if used[index]:
                    continue
                used[index] = True
                line = [a, b]
                while True:
                    ref = take(key(line[-1]))
                    if ref is None:
                        break
                    next_index, end = ref
                    used[next_index] = True
                    seg_a, seg_b = segments[next_index]
                    line.append(seg_b if end == 0 else seg_a)
                while True:
                    ref = take(key(line[0]))
                    if ref is None:
                        break
                    next_index, end = ref
                    used[next_index] = True
                    seg_a, seg_b = segments[next_index]
                    line.insert(0, seg_b if end == 0 else seg_a)
                if len(line) >= 3 and converter.distance(line[0], line[-1]) <= 1.5:
                    line[-1] = line[0]
                loops.append(line)
            return loops

        def closed_loop(loop):
            if len(loop) >= 3 and loop[0] != loop[-1]:
                return loop + [loop[0]]
            return loop

        def rotate_loop(loop, index):
            pts = loop[:-1] if len(loop) > 1 and loop[0] == loop[-1] else loop
            if not pts:
                return []
            index %= len(pts)
            return pts[index:] + pts[:index] + [pts[index]]

        def mask_inside(point):
            x = int(round(point[0]))
            y = int(round(point[1]))
            if x < 0 or y < 0 or x >= width or y >= height:
                return False
            return data[y * bpl + x] > 0

        def connector_inside(a, b):
            steps = max(2, int(math.ceil(converter.distance(a, b))))
            for i in range(steps + 1):
                t = i / steps
                p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                if not mask_inside(p):
                    return False
            return True

        def closest_loop_pair(a_loop, b_loop, max_gap_px):
            a_pts = a_loop[:-1] if len(a_loop) > 1 and a_loop[0] == a_loop[-1] else a_loop
            b_pts = b_loop[:-1] if len(b_loop) > 1 and b_loop[0] == b_loop[-1] else b_loop
            best = None
            best_d = max_gap_px
            if not a_pts or not b_pts:
                return None
            step_a = max(1, len(a_pts) // 160)
            step_b = max(1, len(b_pts) // 160)
            for ia in range(0, len(a_pts), step_a):
                a = a_pts[ia]
                for ib in range(0, len(b_pts), step_b):
                    b = b_pts[ib]
                    d = converter.distance(a, b)
                    if d < best_d and connector_inside(a, b):
                        best = (d, ia, ib)
                        best_d = d
            return best

        def closest_endpoint_pair(endpoint, loop, max_gap_px):
            pts = loop[:-1] if len(loop) > 1 and loop[0] == loop[-1] else loop
            best = None
            best_d = max_gap_px
            for index, point in enumerate(pts):
                d = converter.distance(endpoint, point)
                if d < best_d and connector_inside(endpoint, point):
                    best = (d, index)
                    best_d = d
            return best

        def join_concentric_levels(levels):
            chains = []
            max_gap_px = spacing * px_per_unit * 2.35
            for level_index, loops in enumerate(levels):
                loops = [closed_loop(loop) for loop in loops if len(loop) >= 4 and loop[0] == loop[-1]]
                if not loops:
                    continue
                if level_index == 0 or not chains:
                    chains.extend({"path": loop, "last_loop": loop, "joined": 1} for loop in loops)
                    continue

                unused = set(range(len(loops)))
                for chain in chains:
                    if not unused:
                        break
                    best = None
                    best_loop_index = None
                    best_attach = None
                    if chain["joined"] == 1:
                        for loop_index in list(unused):
                            pair = closest_loop_pair(chain["last_loop"], loops[loop_index], max_gap_px)
                            if pair is None:
                                continue
                            d, outer_i, inner_i = pair
                            if best is None or d < best:
                                best = d
                                best_loop_index = loop_index
                                best_attach = (outer_i, inner_i)
                        if best_loop_index is None:
                            continue
                        outer_i, inner_i = best_attach
                        outer = rotate_loop(chain["path"], outer_i)
                        inner = rotate_loop(loops[best_loop_index], inner_i)
                        chain["path"] = outer + [inner[0]] + inner
                        chain["last_loop"] = inner
                    else:
                        endpoint = chain["path"][-1]
                        for loop_index in list(unused):
                            pair = closest_endpoint_pair(endpoint, loops[loop_index], max_gap_px)
                            if pair is None:
                                continue
                            d, inner_i = pair
                            if best is None or d < best:
                                best = d
                                best_loop_index = loop_index
                                best_attach = inner_i
                        if best_loop_index is None:
                            continue
                        inner = rotate_loop(loops[best_loop_index], best_attach)
                        chain["path"].extend([inner[0]] + inner)
                        chain["last_loop"] = inner
                    chain["joined"] += 1
                    unused.remove(best_loop_index)

                for loop_index in unused:
                    loop = loops[loop_index]
                    chains.append({"path": loop, "last_loop": loop, "joined": 1})
            return [chain["path"] for chain in chains]

        levels = []
        max_dist = max(d for d in dist if d < big) / px_per_unit
        level = spacing
        while level < max_dist:
            threshold = level * px_per_unit
            segments = []
            for y in range(height - 1):
                row = y * width
                next_row = row + width
                for x in range(width - 1):
                    pts = [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]
                    vals = [
                        dist[row + x] - threshold,
                        dist[row + x + 1] - threshold,
                        dist[next_row + x + 1] - threshold,
                        dist[next_row + x] - threshold,
                    ]
                    crossings = []
                    for i, j in ((0, 1), (1, 2), (2, 3), (3, 0)):
                        vi, vj = vals[i], vals[j]
                        if (vi <= 0.0 < vj) or (vj <= 0.0 < vi):
                            crossings.append(interp(pts[i], vi, pts[j], vj))
                    if len(crossings) == 2:
                        segments.append((crossings[0], crossings[1]))
                    elif len(crossings) == 4:
                        segments.append((crossings[0], crossings[1]))
                        segments.append((crossings[2], crossings[3]))
            loops = []
            for loop in stitch_segments(segments):
                if len(loop) >= 4 and loop[0] == loop[-1]:
                    loops.append(loop)
            levels.append(loops)
            level += spacing
        return [[to_world(point) for point in chain] for chain in join_concentric_levels(levels) if len(chain) >= 2]

    def lattice_from_closed_contours(self, contours, settings):
        pattern = converter.normalized_hatch_pattern(getattr(settings, "hatch_pattern", "crosshatch"))
        spacing = self.pattern_spacing(settings, pattern)
        if spacing <= 0:
            return []
        close_tol = max(float(getattr(settings, "tolerance", 0.25)) * 2.0, 0.5)
        polygons = []
        for contour in contours:
            if len(contour) < 4:
                continue
            polygon = list(contour)
            if converter.distance(polygon[0], polygon[-1]) > close_tol:
                continue
            polygon[-1] = polygon[0]
            polygons.append(polygon)
        if not polygons:
            return []
        bounds = converter.contour_bounds(polygons)
        min_x, min_y, max_x, max_y = bounds
        if max_x <= min_x or max_y <= min_y:
            return []

        px_per_unit = max(float(getattr(settings, "raster_px_per_unit", 2.0)), 0.25)
        margin = spacing * 2.0
        width = max(1, int(math.ceil((max_x - min_x + margin * 2.0) * px_per_unit)))
        height = max(1, int(math.ceil((max_y - min_y + margin * 2.0) * px_per_unit)))
        max_dim = 1800
        scale_down = max(width / max_dim, height / max_dim, 1.0)
        if scale_down > 1.0:
            px_per_unit /= scale_down
            width = max(1, int(math.ceil((max_x - min_x + margin * 2.0) * px_per_unit)))
            height = max(1, int(math.ceil((max_y - min_y + margin * 2.0) * px_per_unit)))

        def to_px(point):
            return (
                (point[0] - min_x + margin) * px_per_unit,
                (point[1] - min_y + margin) * px_per_unit,
            )

        path = QPainterPath()
        path.setFillRule(Qt.OddEvenFill)
        for polygon in polygons:
            px0, py0 = to_px(polygon[0])
            path.moveTo(px0, py0)
            for point in polygon[1:]:
                px, py = to_px(point)
                path.lineTo(px, py)
            path.closeSubpath()

        def inside(point):
            px, py = to_px(point)
            if px < 0.0 or py < 0.0 or px >= width or py >= height:
                return False
            return path.contains(QPointF(px, py))

        def rotated_bounds_world(angle_deg):
            ang = math.radians(angle_deg)
            cs, sn = math.cos(-ang), math.sin(-ang)
            points = [(x * cs - y * sn, x * sn + y * cs) for polygon in polygons for x, y in polygon]
            return min(x for x, _ in points), min(y for _, y in points), max(x for x, _ in points), max(y for _, y in points)

        angle = math.radians(float(getattr(settings, "hatch_angle_deg", 0.0)))
        ca, sa = math.cos(angle), math.sin(angle)
        rmin_x, rmin_y, rmax_x, rmax_y = rotated_bounds_world(float(getattr(settings, "hatch_angle_deg", 0.0)))
        rmin_x -= margin
        rmax_x += margin
        rmin_y -= margin
        rmax_y += margin

        def world(x, y):
            return (x * ca - y * sa, x * sa + y * ca)

        out = []
        seen = set()
        sample = max(0.5 / px_per_unit, min(spacing / 5.0, 1.0))

        def add_full_segment(a, b):
            key = tuple(sorted(((round(a[0], 5), round(a[1], 5)), (round(b[0], 5), round(b[1], 5)))))
            if key not in seen:
                seen.add(key)
                out.append([a, b])

        def add_segment(a, b):
            length = converter.distance(a, b)
            if length <= 1e-9:
                return
            steps = max(1, int(math.ceil(length / sample)))
            start = None
            last = None
            last_point = None
            last_active = False

            def refine(pa, active_a, pb, active_b):
                lo = pa
                hi = pb
                lo_active = active_a
                for _ in range(16):
                    mid = ((lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5)
                    mid_active = inside(mid)
                    if mid_active == lo_active:
                        lo = mid
                        lo_active = mid_active
                    else:
                        hi = mid
                return lo if lo_active else hi

            def flush():
                nonlocal start, last
                if start is not None and last is not None and converter.distance(start, last) >= sample * 0.75:
                    key = tuple(sorted(((round(start[0], 5), round(start[1], 5)), (round(last[0], 5), round(last[1], 5)))))
                    if key not in seen:
                        seen.add(key)
                        out.append([start, last])
                start = None
                last = None

            for idx in range(steps + 1):
                t = idx / steps
                point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                active = inside(point)
                if active:
                    if start is None:
                        start = refine(last_point, last_active, point, active) if last_point is not None and not last_active else point
                    last = point
                else:
                    if start is not None and last is not None and last_point is not None and last_active:
                        last = refine(last_point, last_active, point, active)
                    flush()
                last_point = point
                last_active = active
            flush()

        fill_spacing = max(spacing, 1e-6)
        if pattern == "triangular":
            side = max(fill_spacing, 0.05)
            row_step = side * math.sqrt(3.0) / 2.0
            i_min = int(math.floor((rmin_x - rmax_y - side) / side)) - 2
            i_max = int(math.ceil((rmax_x - rmin_y + side) / side)) + 2
            j_min = int(math.floor((rmin_y - row_step) / row_step)) - 1
            j_max = int(math.ceil((rmax_y + row_step) / row_step)) + 1

            def tri_point(i, j):
                return ((i + j * 0.5) * side, j * row_step)

            for j in range(j_min, j_max + 1):
                for i in range(i_min, i_max + 1):
                    p = tri_point(i, j)
                    add_segment(world(*p), world(*tri_point(i + 1, j)))
                    add_segment(world(*p), world(*tri_point(i, j + 1)))
                    add_segment(world(*p), world(*tri_point(i - 1, j + 1)))
        elif pattern == "diamonds":
            half = max(fill_spacing * 0.5, 0.05)
            x_min = int(math.floor((rmin_x - half) / half)) - 1
            x_max = int(math.ceil((rmax_x + half) / half)) + 1
            y_min = int(math.floor((rmin_y - half) / half)) - 1
            y_max = int(math.ceil((rmax_y + half) / half)) + 1
            for j in range(y_min, y_max + 1):
                y = j * half
                for i in range(x_min, x_max + 1):
                    x = i * half
                    add_segment(world(x, y), world(x + half, y + half))
                    add_segment(world(x, y), world(x + half, y - half))
        elif pattern == "hexagonal":
            radius = max(fill_spacing * 0.5, 0.05)
            x_step = radius * 1.5
            y_step = radius * math.sqrt(3.0)
            x = math.floor((rmin_x - radius) / x_step) * x_step
            col = 0
            while x <= rmax_x + radius:
                y = math.floor((rmin_y - radius) / y_step) * y_step + (y_step * 0.5 if col % 2 else 0.0)
                while y <= rmax_y + radius:
                    vertices = [world(x + math.cos(math.radians(60.0 * i)) * radius, y + math.sin(math.radians(60.0 * i)) * radius) for i in range(7)]
                    for a, b in zip(vertices, vertices[1:]):
                        add_segment(a, b)
                    y += y_step
                x += x_step
                col += 1
        if pattern in ("triangular", "diamonds", "hexagonal"):
            return converter.chain_segments_to_paths(out)
        return out

    def load_contours(self, svg_path, settings):
        key = self.raw_geometry_key(svg_path, settings)
        if self.raw_cache_key != key or self.raw_contours is None:
            parse_hatch_spacing = 0.0 if getattr(settings, "raster_shading", False) else float(getattr(settings, "hatch_spacing_mm", 0.0))
            self.raw_contours = converter.parse_svg_geometry(
                svg_path,
                settings.tolerance,
                settings.flip_y,
                parse_hatch_spacing,
                float(getattr(settings, "hatch_angle_deg", 0.0)),
                str(getattr(settings, "hatch_pattern", "crosshatch")).lower(),
                int(getattr(settings, "shade_levels", 1)),
                float(getattr(settings, "shade_angle_step_deg", 90.0)),
                True,
                float(getattr(settings, "triangle_size_mm", 0.0)),
                self.pattern_size_values(settings),
            )
            if getattr(settings, "raster_shading", False):
                pattern = converter.normalized_hatch_pattern(getattr(settings, "hatch_pattern", "crosshatch"))
                if pattern in ("concentric", "triangular", "diamonds", "hexagonal"):
                    centerline_contours = converter.parse_svg_geometry(
                        svg_path,
                        settings.tolerance,
                        settings.flip_y,
                        0.0,
                        float(getattr(settings, "hatch_angle_deg", 0.0)),
                        str(getattr(settings, "hatch_pattern", "crosshatch")).lower(),
                        int(getattr(settings, "shade_levels", 1)),
                        float(getattr(settings, "shade_angle_step_deg", 90.0)),
                        False,
                        float(getattr(settings, "triangle_size_mm", 0.0)),
                        self.pattern_size_values(settings),
                    )
                    if pattern == "concentric":
                        self.raw_contours.extend(self.concentric_from_closed_contours(centerline_contours, settings))
                    else:
                        self.raw_contours.extend(self.lattice_from_closed_contours(centerline_contours, settings))
                else:
                    self.raw_contours.extend(self.raster_shade_contours(svg_path, settings))
            self.raw_cache_key = key
            self.log.append(f"Parsed SVG geometry once: {len(self.raw_contours)} raw contours.")
        return converter.apply_geometry_settings(self.raw_contours, settings)

    def print_speed_mm_s(self):
        return max(float(self.fields["print_speed"].text()), 1e-9)

    def on_print_speed_changed(self):
        self.update_estimate()
        try:
            speed = self.print_speed_mm_s()
        except ValueError:
            return
        self.gl_preview.set_play_speed(speed)

    def move_strategy_length(self, move):
        # Full coordinated motion length; includes theta motor degrees so
        # rotation-heavy smoothing changes affect the displayed estimate.
        if "motion_length" in move:
            return float(move["motion_length"])
        if "xy_length" in move:
            return float(move["xy_length"])
        start = move.get("start", (0.0, 0.0))
        end = move.get("end", start)
        dx = abs(end[0] - start[0])
        dy = abs(end[1] - start[1])
        strategy = move.get("strategy")
        if strategy == "x_theta":
            return dx
        if strategy == "y_theta":
            return dy
        return math.hypot(dx, dy)

    def format_duration(self, seconds):
        seconds = max(0, int(round(seconds)))
        hours, rem = divmod(seconds, 3600)
        minutes, secs = divmod(rem, 60)
        if hours:
            return f"{hours}h {minutes}m {secs}s"
        if minutes:
            return f"{minutes}m {secs}s"
        return f"{secs}s"

    def estimate_runtime(self, moves, print_speed_mm_s):
        draw_mm = 0.0
        travel_seconds = 0.0
        pen_seconds = 0.0
        strategy_counts = {}
        for move in moves:
            kind = move.get("type")
            if kind == "draw":
                draw_mm += self.move_strategy_length(move)
                strategy = move.get("strategy", "tangent")
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            elif kind == "travel":
                if "motion_length" in move or "xy_length" in move:
                    travel_seconds += float(move.get("xy_length", move.get("motion_length", 0.0))) / PREVIEW_TRAVEL_MM_S
                else:
                    travel_seconds += float(move.get("duration_ms", 0.0)) / 1000.0
            elif kind in ("pen_up", "pen_down"):
                pen_seconds += float(move.get("duration_ms", 0.0)) / 1000.0

        draw_seconds = draw_mm / max(print_speed_mm_s, 1e-9)
        total_seconds = draw_seconds + travel_seconds + pen_seconds
        return {
            "total_seconds": total_seconds,
            "draw_seconds": draw_seconds,
            "travel_seconds": travel_seconds,
            "pen_seconds": pen_seconds,
            "draw_mm": draw_mm,
            "strategy_counts": strategy_counts,
        }

    def update_estimate(self):
        if not self.moves:
            self.estimate.setText("Estimated time: preview an SVG to calculate.")
            return None
        try:
            print_speed = self.print_speed_mm_s()
        except ValueError:
            self.estimate.setText("Estimated time: enter a valid print speed.")
            return None
        estimate = self.estimate_runtime(self.moves, print_speed)
        counts = estimate["strategy_counts"]
        axis_summary = f"x_theta {counts.get('x_theta', 0)}, y_theta {counts.get('y_theta', 0)}"
        fallback_count = counts.get("fallback", 0)
        if fallback_count:
            axis_summary += f", fallback {fallback_count}"
        self.estimate.setText(
            "Estimated time: "
            f"{self.format_duration(estimate['total_seconds'])} "
            f"(draw {self.format_duration(estimate['draw_seconds'])}, "
            f"travel {self.format_duration(estimate['travel_seconds'])}, "
            f"pen {self.format_duration(estimate['pen_seconds'])}; "
            f"draw coordinated motion {fmt(estimate['draw_mm'])} @ {fmt(print_speed)} mm/s; "
            f"{axis_summary})"
        )
        return estimate

    def size_summary(self):
        if not self.contours:
            return ""
        min_x, min_y, max_x, max_y = converter.contour_bounds(self.contours)
        path_w = max_x - min_x
        path_h = max_y - min_y
        pen = max(float(self.fields["pen_diameter_mm"].text()), 0.0)
        ink_w = path_w + pen
        ink_h = path_h + pen
        return f"path {fmt(path_w)} x {fmt(path_h)} mm, estimated ink {fmt(ink_w)} x {fmt(ink_h)} mm"

    def load_preview(self, show_errors=True):
        try:
            settings = self.settings()
            raw_contours = self.load_contours(self.svg_path.text(), settings)
            bed_center = converter.contour_center(raw_contours)
            clip_radius = max(float(getattr(settings, "bed_diameter_mm", 457.2)) / 2.0 - float(getattr(settings, "bed_margin_mm", 0.0)), 0.0)
            self.moves = self.build_preview_moves(raw_contours, settings)
            self.contours = converter.clip_contours_to_bed(raw_contours, bed_center, clip_radius)
        except Exception as exc:
            if show_errors:
                QMessageBox.critical(self, "Preview failed", str(exc))
            return None
        self.command_list.clear()
        headers = ["(Generated preview)", "G21", "G90", f"G0 F{fmt(settings.travel_rate)}"]
        lines = headers
        lines.extend(f"{i:05d}: {move.get('gcode', '')}" for i, move in enumerate(self.moves, start=1))
        self.command_list.addItems(lines)
        self.slider.setMaximum(max(0, len(self.moves)))
        self.set_index(len(self.moves))
        self.gl_preview.set_preview(self.contours, self.moves, settings, center=bed_center, play_speed_mm_s=self.print_speed_mm_s())
        return settings

    def preview(self):
        if self.load_preview(show_errors=True) is None:
            return
        estimate = self.update_estimate()
        if estimate:
            self.log.append(
                f"Loaded {len(self.moves)} preview commands. Estimated print time {self.format_duration(estimate['total_seconds'])} "
                f"at {fmt(self.print_speed_mm_s())} mm/s."
            )
        else:
            self.log.append(f"Loaded {len(self.moves)} preview commands.")
        size_summary = self.size_summary()
        if size_summary:
            self.log.append(f"Pen compensation: {size_summary}.")

    def convert(self):
        svg_path = self.svg_path.text().strip()
        if not svg_path:
            QMessageBox.warning(self, "Conversion needs an SVG", "Choose an SVG file first.")
            return
        if not self.gcode_path.text().strip():
            self.update_suggested_gcode_path(svg_path)
        gcode_path = self.gcode_path.text().strip()
        if not gcode_path:
            QMessageBox.warning(self, "Conversion needs an output path", "Choose where to save the G-code file.")
            return
        try:
            settings = self.settings()
            contours_data = self.load_contours(svg_path, settings)
            gcode = converter.contours_to_gcode(contours_data, settings)
            with open(gcode_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(gcode)
            contours, lines = len(contours_data), len(gcode.splitlines())
        except Exception as exc:
            QMessageBox.critical(self, "Conversion failed", str(exc))
            return
        self.log.append(f"Saved {lines} G-code lines from {contours} contours: {gcode_path}")

    def set_index(self, index, sync_command_list=True):
        if not self.moves:
            return
        self.preview_progress = max(0.0, min(float(index), float(len(self.moves))))
        self.preview_index = int(math.floor(self.preview_progress))
        if self.preview_progress >= len(self.moves):
            self.preview_index = len(self.moves)
        if self.slider.value() != self.preview_index:
            self.slider.blockSignals(True)
            self.slider.setValue(self.preview_index)
            self.slider.blockSignals(False)
        self.gl_preview.set_index(self.preview_progress)
        if sync_command_list:
            row = self.preview_index + 4 if self.preview_index < len(self.moves) else len(self.moves) + 3
            if self.preview_progress <= 0:
                row = 0
            if 0 <= row < self.command_list.count() and self.command_list.currentRow() != row:
                self.command_list.blockSignals(True)
                self.command_list.setCurrentRow(row)
                self.command_list.scrollToItem(self.command_list.item(row))
                self.command_list.blockSignals(False)
        self.update_status()

    def command_selected(self, row):
        if row >= 4:
            self.set_index(row - 4)

    def update_status(self):
        if not self.moves:
            return
        if self.preview_progress >= len(self.moves):
            move = self.moves[-1]
        else:
            move = self.moves[min(max(int(math.floor(self.preview_progress)), 0), len(self.moves) - 1)]
        theta, motor = self.gl_preview.active_theta()
        point = self.gl_preview.tool_point_at_progress(self.preview_progress) or move.get("end", (0, 0))
        command_point = self.gl_preview.command_point_at_progress(self.preview_progress) or move.get("command_end", point)
        strategy = move.get("strategy", "")
        strategy_text = f" | {strategy}" if strategy else ""
        self.status.setText(f"move {fmt(self.preview_progress)}/{len(self.moves)} {move.get('type')}{strategy_text} | pen X {fmt(point[0])} Y {fmt(point[1])} | cmd X {fmt(command_point[0])} Y {fmt(command_point[1])} | bed theta {fmt(theta)} deg | A motor {fmt(motor)} deg")

    def play(self):
        if not self.moves:
            return
        if self.preview_progress >= len(self.moves):
            self.set_index(0)
        self.gl_preview.set_fast_render(True)
        self.play_start_time = time.monotonic()
        self.play_start_progress = self.preview_progress
        self.last_command_follow_time = 0.0
        self.play_timer.start(16)

    def pause(self):
        self.play_timer.stop()
        self.play_last_time = None
        self.play_start_time = None
        self.gl_preview.set_fast_render(False)
        if self.moves:
            self.set_index(self.preview_progress, sync_command_list=True)

    def progress_after_time(self, start_progress, elapsed_ms):
        if not self.moves or not self.gl_preview.cumulative_ms:
            return 0.0
        start_index = max(0, min(int(math.floor(start_progress)), len(self.moves) - 1))
        start_frac = max(0.0, min(float(start_progress) - start_index, 1.0))
        # Per-move durations must come from the same playback timeline that built
        # cumulative_ms (print-speed paced), not the engine feed-rate duration_ms,
        # or the fraction within a move would be scaled wrong.
        start_move_ms = max(1.0, self.gl_preview._playback_move_ms(self.moves[start_index]))
        start_time = self.gl_preview.cumulative_ms[start_index] + start_frac * start_move_ms
        target_time = start_time + elapsed_ms * PLAYBACK_RATE
        if target_time >= self.gl_preview.cumulative_ms[-1]:
            return float(len(self.moves))
        index = max(0, bisect.bisect_right(self.gl_preview.cumulative_ms, target_time) - 1)
        move_ms = max(1.0, self.gl_preview._playback_move_ms(self.moves[index]))
        frac = (target_time - self.gl_preview.cumulative_ms[index]) / move_ms
        return index + max(0.0, min(frac, 1.0))

    def play_step(self):
        if self.preview_progress >= len(self.moves):
            self.pause()
            return
        if self.play_start_time is None:
            self.play_start_time = time.monotonic()
            self.play_start_progress = self.preview_progress
        elapsed_ms = (time.monotonic() - self.play_start_time) * 1000.0
        progress = self.progress_after_time(self.play_start_progress, elapsed_ms)
        now = time.monotonic()
        follow = now - self.last_command_follow_time >= 0.25
        self.set_index(progress, sync_command_list=follow)
        self.gl_preview.update()
        if follow:
            self.last_command_follow_time = now


if __name__ == "__main__":
    gl_format = QSurfaceFormat()
    gl_format.setRenderableType(QSurfaceFormat.OpenGL)
    gl_format.setVersion(2, 1)
    gl_format.setProfile(QSurfaceFormat.CompatibilityProfile)
    gl_format.setDepthBufferSize(0)
    gl_format.setStencilBufferSize(0)
    gl_format.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
    QSurfaceFormat.setDefaultFormat(gl_format)
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
