import bisect
import dataclasses
import math
import os
import sys
import threading
import time
from array import array

from PySide6.QtCore import QObject, QPointF, QThread, QTimer, Qt, QRectF, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QImage,
    QPainter,
    QPainterPath,
    QSurfaceFormat,
)
from PySide6.QtOpenGL import QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QColorDialog,
    QScrollArea,
    QSlider,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import converter_core as converter
# Flushed so `qt_debug.log` names the build as soon as the app starts; it is the
# quickest way to tell a stale window from a stale install.
print(f"[geometry version: {getattr(converter, 'GEOMETRY_VERSION', 'OLD-no-new-patterns')}]", flush=True)
print(
    "[A guard: park above %.0f deg/segment, %.0f motor deg/min, %.0f motor deg/s^2, "
    "travel rotations fed]"
    % (
        float(converter.Settings().theta_max_step_deg),
        float(converter.Settings().theta_controller_limits.max_rate_deg_min),
        float(converter.Settings().theta_controller_limits.max_acceleration_deg_s2),
    ),
    flush=True,
)

# Playback wall-clock multiplier: 1.0 = real time, so the toolhead animates at
# the configured print speed (mm/s). Bump up to fast-forward long jobs.
PLAYBACK_RATE = 1.0


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

    # Emitted while the artwork is dragged, in machine millimetres relative to
    # the registered bed center, so the placement fields can follow the drag.
    placementChanged = Signal(float, float)

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
        # Boundary guide: the radius the gantry can actually reach from the
        # registered bed center. plan_program clips to it, so artwork outside it
        # is silently trimmed; drawing it makes that visible while the scale is
        # being chosen.
        self.reach_color = QColor("#15803d")
        self.show_pen_down_path = True
        self.show_machine_reach = True
        # Live placement. `placement` is where the artwork should sit relative to
        # the bed center; `planned_offset` is what the current plan already bakes
        # in. Their difference is applied as a shader shift, so dragging moves the
        # part immediately while the bed and reach circles stay pinned. Pressing
        # Preview re-plans with the new offset, after which the two agree.
        self.placement = (0.0, 0.0)
        self.planned_offset = (0.0, 0.0)
        self.is_placing = False
        self.last_place_pos = None
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
            uniform vec2 shift;
            void main() {
                float c = cos(theta);
                float s = sin(theta);
                vec2 d = (p + shift) - center;
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
            "shift": self.program.uniformLocation("shift"),
            "color": self.program.uniformLocation("color"),
        }
        for name in ("bed_circle", "bed_radius", "debug_box", "debug_cross", "reach_circle", "artwork", "drawn_path", "travel", "motion"):
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
        if kind == "travel":
            # Travel duration is planned from the configured G0 rate. Reuse it
            # here so pen-up motion remains visible and matches the command.
            return float(move.get("duration_ms", 0.0))
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

        reach_radius = float(getattr(self.settings, "machine_reach_radius_mm", 0.0))
        reach_circle = []
        if reach_radius > 0.0:
            prev = (self.preview_center[0] + reach_radius, self.preview_center[1])
            for i in range(1, 241):
                a = i / 240.0 * math.pi * 2.0
                curr = (
                    self.preview_center[0] + math.cos(a) * reach_radius,
                    self.preview_center[1] + math.sin(a) * reach_radius,
                )
                reach_circle.extend([prev[0], prev[1], curr[0], curr[1]])
                prev = curr

        artwork = []
        for contour in self.contours:
            for a, b in zip(contour, contour[1:]):
                artwork.extend([a[0], a[1], b[0], b[1]])
        # Keep-down connectors are drawn ink, but they are not part of the
        # clipped contour set, so the passes would look like separate strokes
        # even though the program joins them into one continuous serpentine.
        # Add them to the base layer so what is previewed matches what is drawn.
        for move in self.moves:
            if move.get("strategy") != "keep_down_bridge":
                continue
            bed_start = move.get("bed_start")
            bed_end = move.get("bed_end")
            if bed_start is not None and bed_end is not None:
                artwork.extend([bed_start[0], bed_start[1], bed_end[0], bed_end[1]])

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
            self.machine_points.extend([start, end])
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
            "reach_circle": array("f", reach_circle),
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
        if event.button() == Qt.LeftButton and not (event.modifiers() & Qt.ShiftModifier):
            # Drag the part on the bed, the way a slicer moves a model. Panning
            # moves to Shift+drag and to the middle and right buttons.
            self.is_placing = True
            self.last_place_pos = event.position()
            self.setCursor(Qt.SizeAllCursor)
            event.accept()
            return
        if event.button() in (Qt.LeftButton, Qt.MiddleButton, Qt.RightButton):
            self.is_panning = True
            self.last_pan_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_placing and self.last_place_pos is not None:
            current = event.position()
            dx = current.x() - self.last_place_pos.x()
            dy = current.y() - self.last_place_pos.y()
            min_x, min_y, max_x, max_y = self.adjusted_bounds()
            span_x = max(max_x - min_x, 1e-9)
            span_y = max(max_y - min_y, 1e-9)
            # Screen y runs down and world y runs up, so the vertical term flips.
            self.placement = (
                self.placement[0] + dx / max(self.width(), 1) * span_x,
                self.placement[1] - dy / max(self.height(), 1) * span_y,
            )
            self.last_place_pos = current
            self.placementChanged.emit(self.placement[0], self.placement[1])
            self.update()
            event.accept()
            return
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
        if self.is_placing and event.button() == Qt.LeftButton:
            self.is_placing = False
            self.last_place_pos = None
            self.unsetCursor()
            event.accept()
            return
        if self.is_panning and event.button() in (Qt.LeftButton, Qt.MiddleButton, Qt.RightButton):
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

    def set_show_pen_down_path(self, show):
        """Show only generated G1 X/Y segments, not pen-up travel clutter."""
        self.show_pen_down_path = bool(show)
        self.update()

    def set_show_machine_reach(self, show):
        """Show the gantry's reachable radius around the registered bed center."""
        self.show_machine_reach = bool(show)
        self.update()

    def set_reach_warning(self, warning):
        """Draw the reach guide in red when artwork is being clipped by it.

        The guide is the only place the bed circle and the reachable area are
        drawn at the same scale, so it is where an over-scale artwork is
        visible without reading the status line.
        """
        self.reach_warning = bool(warning)
        self.reach_color = QColor("#dc2626" if self.reach_warning else "#15803d")
        self.update()

    def set_planned_offset(self, offset):
        """Record the placement the current plan already accounts for."""
        self.planned_offset = (float(offset[0]), float(offset[1]))
        self.placement = self.planned_offset
        self.update()

    def set_placement(self, offset):
        """Move the artwork relative to the bed center, in machine millimetres."""
        self.placement = (float(offset[0]), float(offset[1]))
        self.update()

    def placement_delta(self):
        """How far the drag has moved the artwork past the planned placement."""
        return (
            self.placement[0] - self.planned_offset[0],
            self.placement[1] - self.planned_offset[1],
        )

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

    def active_segment_at_progress(self, progress):
        move, _index, _frac = self.active_move_at_progress(progress)
        if move is None or move.get("type") not in ("draw", "travel"):
            return None
        point = self.tool_point_at_progress(progress)
        return move.get("start", point), point

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

    def update_overlay_labels(self, point, bounds):
        if not self.moves:
            self.x_label.hide()
            self.y_label.hide()
            return
        sx, sy = self.screen_from_world(point, bounds)
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

    def set_shift(self, shift_x, shift_y):
        """Apply the live placement drag as a world shift for one draw call."""
        loc = self.uniform_loc.get("shift", -1)
        if loc < 0:
            return
        self.program.setUniformValue(loc, float(shift_x), float(shift_y))

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
        bounds = self.adjusted_bounds()
        self.update_overlay_labels(tool_point, bounds)

        self.program.bind()
        min_x, min_y, max_x, max_y = bounds
        self.program.setUniformValue(self.uniform_loc["center"], float(self.preview_center[0]), float(self.preview_center[1]))
        self.program.setUniformValue(self.uniform_loc["bounds"], float(min_x), float(min_y), float(max_x), float(max_y))

        # Draw the artwork upright in its own frame. The optional red overlay is
        # the generated machine-frame X/Y path for pen-down (G1) moves only.
        # Pen-up travel, crosshairs, and tool markers remain hidden so it stays
        # useful as a G-code sanity check instead of becoming a cluttered view.
        self.program.setUniformValue1f(self.uniform_loc["theta"], 0.0)
        shift_x, shift_y = self.placement_delta()
        # The bed and reach circles are pinned to the bed center; the artwork and
        # its tool path move with a placement drag.
        self.set_shift(0.0, 0.0)
        self.draw_static("bed_circle", QColor("#94a3b8"), 1.5)
        self.set_shift(shift_x, shift_y)
        # Full artwork in the undrawn color, then overdraw the portion drawn so
        # far in the drawn color — the boundary tracks where the pen is.
        self.draw_static("artwork", self.undrawn_color, 1.0)
        drawn_segments = self.draw_segments_done(progress)
        if drawn_segments > 0:
            self.draw_static("drawn_path", self.drawing_color, 1.6, count=drawn_segments * 2)
        if self.show_pen_down_path:
            self.draw_static("motion", self.motion_color, 1.2)
        self.set_shift(0.0, 0.0)
        if self.show_machine_reach:
            self.draw_static("reach_circle", self.reach_color, 2.0)
        self.program.release()


class PreviewWorker(QObject):
    progress = Signal(int, str)
    notice = Signal(str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, window, svg_path, settings):
        super().__init__()
        self.window = window
        self.svg_path = svg_path
        self.settings = settings
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def is_cancelled(self):
        return self.cancel_event.is_set()

    def run(self):
        try:
            settings = self.settings
            auto_fit = str(getattr(settings, "fit_mode", "manual")).strip().lower() in ("fill", "inside")
            if converter.is_raster_image(self.svg_path):
                # A photo has no outlines to measure, so size it from its pixels
                # before the fill is built: the fill spacing is millimetres and
                # cannot be resolved until the paper scale is known.
                settings = self.window.fitted_settings_for_artwork_bounds(settings, self.svg_path)
            elif auto_fit:
                # Measure the outlines first. An auto fit needs the artwork's
                # size before the fill can be generated, and filling here would
                # build the lattice at whatever scale the field still holds and
                # throw it away: on a 3000-unit artwork that is minutes of work
                # for geometry the fit immediately discards.
                self.progress.emit(6, "Measuring the artwork")
                outlines = self.window.load_contours(
                    self.svg_path, settings, self.is_cancelled, None, fill=False
                )
                if outlines:
                    fitted = self.window.fitted_settings(settings, outlines)
                else:
                    # Nothing measurable - an SVG that is only an embedded
                    # photo, or empty vector content - so use its viewBox.
                    fitted = self.window.fitted_settings_for_artwork_bounds(
                        settings, self.svg_path
                    )
                if fitted is not settings:
                    self.progress.emit(20, "Auto-fitting the artwork to the bed")
                    self.notice.emit(self.window.describe_fit(settings, fitted))
                    settings = fitted
            self.progress.emit(10, "Building fill geometry")
            raw_contours = self.window.load_contours(
                self.svg_path, settings, self.is_cancelled, self.notice.emit
            )
            self.progress.emit(48, f"Planning motion for {len(raw_contours)} contours")
            program_plan = converter.plan_program(raw_contours, settings, self.is_cancelled)
            moves = self.window.build_preview_moves(raw_contours, settings, self.is_cancelled, program_plan)
            self.progress.emit(78, f"Preparing {len(program_plan['contours'])} clipped contours")
            self.progress.emit(90, "Generating complete G-code listing")
            # `stats` reports the worst commanded bed-path deviation and where it
            # happened, which is the number to look at when a turn mid-stroke
            # leaves a mark on paper.
            stats = {}
            program_gcode = converter.contours_to_gcode(
                raw_contours, settings, program_plan, stats
            )
            self.finished.emit(
                (settings, program_plan["contours"], moves, program_plan["center"], program_gcode, stats)
            )
        except converter.OperationCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SVG to XY Theta G-code Converter - OpenGL")
        self.resize(1500, 950)
        self.moves = []
        self.contours = []
        self.preview_dirty = False
        self.preview_tab = None
        self.pending_source_tab = None
        self.pending_source_path = ""
        self.tab_preview_stale = False
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
        self.preview_thread = None
        self.preview_worker = None
        self.preview_started_at = None
        self.preview_elapsed_timer = QTimer(self)
        self.preview_elapsed_timer.timeout.connect(self.update_preview_elapsed)
        self.build_ui()

    def build_ui(self):
        window_root = QWidget()
        window_layout = QVBoxLayout(window_root)
        window_layout.setContentsMargins(6, 6, 6, 6)
        window_layout.setSpacing(4)
        self.setCentralWidget(window_root)

        self.convert_root = QWidget()
        self.stack = QStackedWidget()
        self.stack.setMinimumWidth(280)
        self.dashboard = QWidget()
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.convert_root)
        self.tool_index = {"All tools": 0, "Convert": 1}
        self.generator_tools = []
        self.tool_actions = {}
        self.current_tool = "Convert"

        # Artwork and G-code paths are data holders now: the File menu sets
        # them and the status bar shows them.
        self.svg_path = QLineEdit()
        self.gcode_path = QLineEdit()

        self.fields = {}
        self.field_rows = {}

        def make_form_group(title, items):
            box = QGroupBox(title)
            form = QFormLayout(box)
            form.setLabelAlignment(Qt.AlignRight)
            form.setHorizontalSpacing(6)
            form.setVerticalSpacing(2)
            form.setContentsMargins(8, 6, 8, 6)
            for label, key, value in items:
                if key == "fill_source":
                    edit = QComboBox()
                    for choice_label, choice_value in converter.FILL_SOURCE_CHOICES:
                        edit.addItem(choice_label, choice_value)
                    edit.setCurrentIndex(max(0, edit.findData(value)))
                elif key == "fit_mode":
                    edit = QComboBox()
                    for choice_label, choice_value in converter.FIT_MODE_CHOICES:
                        edit.addItem(choice_label, choice_value)
                    edit.setCurrentIndex(max(0, edit.findData(value)))
                elif key in converter.VALUE_CHOICE_FIELDS:
                    edit = QComboBox()
                    labels = converter.VALUE_CHOICE_LABELS.get(key, {})
                    for choice in converter.VALUE_CHOICE_FIELDS[key]:
                        edit.addItem(labels.get(choice, choice), choice)
                    edit.setCurrentIndex(max(0, edit.findData(value)))
                else:
                    edit = QLineEdit(value)
                    edit.setMaximumWidth(120)
                label_widget = QLabel(label)
                tooltip = converter.FIELD_TOOLTIPS.get(key)
                if tooltip:
                    edit.setToolTip(tooltip)
                    label_widget.setToolTip(tooltip)
                self.fields[key] = edit
                self.field_rows[key] = (label_widget, edit)
                form.addRow(label_widget, edit)
            return box, form

        checkbox_meta = {
            key: (group, label, checked)
            for group, key, label, checked in converter.CHECKBOX_FIELDS
        }

        def make_checkbox(key):
            _group, label, checked = checkbox_meta[key]
            widget = QCheckBox(label)
            widget.setChecked(bool(checked))
            tooltip = converter.FIELD_TOOLTIPS.get(key)
            if tooltip:
                widget.setToolTip(tooltip)
            return widget

        # Checkbox placement comes from CHECKBOX_FIELDS so a setting lives in
        # exactly one group and the sidebar cannot drift from the core model.
        checkboxes = {key: make_checkbox(key) for key in checkbox_meta}
        self.flip_y = checkboxes["flip_y"]
        self.use_z = checkboxes["include_z"]
        self.compensate_pen = checkboxes["compensate_pen_width"]
        self.expand_strokes = checkboxes["expand_strokes"]
        self.fill_wide_strokes = checkboxes["fill_wide_strokes"]
        self.keep_down_bridges = checkboxes["keep_down_bridges"]
        self.sine_rows_connected = checkboxes["sine_rows_connected"]
        self.monotonic_theta = checkboxes["monotonic_theta"]
        self.toolhead_status_handshake = checkboxes["toolhead_status_handshake"]
        self.toolhead_handshake_recover = checkboxes["toolhead_handshake_recover"]

        group_boxes = {}
        group_forms = {}
        for group_title, items in converter.TEXT_FIELD_GROUPS:
            box, form = make_form_group(group_title, items)
            group_boxes[group_title] = box
            group_forms[group_title] = form
        for key, (_group, _label, _checked) in checkbox_meta.items():
            group_forms[_group].addRow(checkboxes[key])

        self.undrawn_color_button = QPushButton("Undrawn")
        self.undrawn_color_button.clicked.connect(lambda: self.choose_preview_color("undrawn"))
        self.drawing_color_button = QPushButton("Drawn")
        self.drawing_color_button.clicked.connect(lambda: self.choose_preview_color("drawing"))
        self.motion_color_button = QPushButton("Motion")
        self.motion_color_button.clicked.connect(lambda: self.choose_preview_color("motion"))
        self.show_pen_down_path = QCheckBox("Show X/Y pen-down path")
        self.show_pen_down_path.setChecked(True)
        self.show_machine_reach = QCheckBox("Show machine reach guide")
        self.show_machine_reach.setChecked(True)
        color_widget = QWidget()
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(4)
        color_layout.addWidget(self.undrawn_color_button)
        color_layout.addWidget(self.drawing_color_button)
        color_layout.addWidget(self.motion_color_button)

        preview_box = group_boxes["Preview settings"]
        preview_form = group_forms["Preview settings"]
        preview_form.addRow(QLabel("Colors"), color_widget)
        preview_form.addRow(self.show_pen_down_path)
        preview_form.addRow(self.show_machine_reach)

        self.preview_build_bar = QProgressBar()
        self.preview_build_bar.setRange(0, 100)
        self.preview_build_bar.setTextVisible(True)
        self.preview_build_bar.hide()
        self.preview_stage = QLabel()
        self.preview_stage.setWordWrap(True)
        self.preview_stage.hide()

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(4)
        expanded_groups = {"Geometry", "Fill", "Motion"}
        for group_title, _items in converter.TEXT_FIELD_GROUPS:
            sidebar_layout.addWidget(
                CollapsibleSection(
                    group_title,
                    group_boxes[group_title],
                    group_title in expanded_groups,
                )
            )
        sidebar_layout.addStretch(1)
        sidebar_scroll = QScrollArea()
        self.sidebar_scroll = sidebar_scroll
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setWidget(sidebar)

        preview_widget = QWidget()
        self.preview_panel = preview_widget
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(2)
        self.gl_preview = GLPreview()
        self.show_pen_down_path.toggled.connect(self.gl_preview.set_show_pen_down_path)
        self.show_machine_reach.toggled.connect(self.gl_preview.set_show_machine_reach)
        self.gl_preview.placementChanged.connect(self.on_placement_changed)
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

        # Preview and Cancel belong with the preview they build and stop.
        preview_actions = QHBoxLayout()
        self.preview_button = QPushButton("Preview", clicked=self.preview)
        preview_actions.addWidget(self.preview_button, 1)
        self.cancel_preview_button = QPushButton("Cancel", clicked=self.cancel_preview)
        self.cancel_preview_button.setEnabled(False)
        preview_actions.addWidget(self.cancel_preview_button, 1)
        preview_layout.addLayout(preview_actions)

        self.status = QLabel("Choose an SVG to build a preview.")
        self.status.setWordWrap(True)
        preview_layout.addWidget(self.status)
        self.estimate = QLabel("Estimated time: preview an SVG to calculate.")
        self.estimate.setWordWrap(True)
        preview_layout.addWidget(self.estimate)
        preview_layout.addWidget(self.preview_build_bar)
        preview_layout.addWidget(self.preview_stage)

        # Over-scale artwork is the one mistake the preview cannot show: a
        # cropped plot still looks like a complete drawing. Say it in words and
        # offer the one-click fix next to the preview it applies to.
        self.fit_inside_button = QPushButton("Fit inside", clicked=self.fit_inside)
        self.fit_inside_button.setEnabled(False)
        self.fit_inside_button.setToolTip(
            "Scale so the whole drawing stays inside the drawable reach circle, and "
            "recenter it on the bed."
        )
        self.fill_bed_button = QPushButton("Fill bed", clicked=self.fill_bed)
        self.fill_bed_button.setEnabled(False)
        self.fill_bed_button.setToolTip(
            "Scale so the artwork's bounds touch the drawable reach circle, and recenter "
            "it on the bed. The four corners fall outside the circle and are clipped."
        )
        self.clip_warning = QLabel()
        self.clip_warning.setWordWrap(True)
        self.clip_warning.setStyleSheet("color: #b91c1c;")
        self.clip_warning.hide()
        clip_row = QHBoxLayout()
        clip_row.addWidget(self.fill_bed_button)
        clip_row.addWidget(self.fit_inside_button)
        clip_row.addWidget(self.clip_warning, 1)
        preview_layout.addLayout(clip_row)

        self.stale_warning = QLabel(
            "Settings changed since this preview - press Preview to rebuild it."
        )
        self.stale_warning.setWordWrap(True)
        self.stale_warning.setStyleSheet("color: #b45309;")
        self.stale_warning.hide()
        preview_layout.addWidget(self.stale_warning)

        convert_layout = QHBoxLayout(self.convert_root)
        convert_layout.setContentsMargins(0, 0, 0, 0)
        convert_layout.addWidget(sidebar_scroll, 1)

        dashboard_scroll = QScrollArea()
        dashboard_scroll.setWidgetResizable(True)
        dashboard_body = QWidget()
        self.dashboard_layout = QVBoxLayout(dashboard_body)
        self.dashboard_layout.setContentsMargins(12, 12, 12, 12)
        self.dashboard_layout.setSpacing(10)
        dashboard_scroll.setWidget(dashboard_body)
        dashboard_host = QVBoxLayout(self.dashboard)
        dashboard_host.setContentsMargins(0, 0, 0, 0)
        dashboard_host.addWidget(dashboard_scroll)

        # Import, export, and preview are window furniture, not tab content,
        # so switching tabs never hides them. The preview fills everything to
        # the right of the feature settings.
        main_split = QSplitter(Qt.Horizontal)
        self.main_split = main_split
        main_split.addWidget(self.stack)
        main_split.addWidget(preview_widget)
        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)
        main_split.setSizes([380, 1120])
        window_layout.addWidget(main_split, 1)

        self.log = QTextEdit()
        self.log.setMaximumHeight(60)
        self.log.setReadOnly(True)
        window_layout.addWidget(self.log)
        # On-screen build marker: a window opened before a converter change
        # keeps its old pattern list, and this is what tells the two apart.
        self.log.append(
            f"Converter core {getattr(converter, 'GEOMETRY_VERSION', 'OLD')}. "
            "Fill pattern 'gradient waves (sine_gradient)' is available. "
            "A-axis guard: the bed parks above %.0f deg per segment instead of "
            "sweeping, and the assumed A limits are %.0f motor deg/min and %.0f "
            "motor deg/s^2; pen-up rotations are fed, never rapids."
            % (
                float(converter.Settings().theta_max_step_deg),
                float(converter.Settings().theta_controller_limits.max_rate_deg_min),
                float(converter.Settings().theta_controller_limits.max_acceleration_deg_s2),
            )
        )

        self.update_color_buttons()
        # Preview generation is manual, so every field that changes the plan
        # must flag the visible build as out of date. Playback speed and the
        # estimate scale only affect the display and are deliberately excluded.
        for key, edit in self.fields.items():
            if key in ("print_speed", "motion_estimate_scale"):
                continue
            if isinstance(edit, QComboBox):
                edit.currentIndexChanged.connect(lambda _index: self.mark_preview_dirty())
            else:
                edit.textChanged.connect(lambda _text: self.mark_preview_dirty())
        for checkbox in (
            self.flip_y,
            self.compensate_pen,
            self.expand_strokes,
            self.fill_wide_strokes,
            self.keep_down_bridges,
            self.monotonic_theta,
            self.use_z,
            self.toolhead_status_handshake,
            self.toolhead_handshake_recover,
        ):
            checkbox.toggled.connect(lambda _checked: self.mark_preview_dirty())
        self.fields["print_speed"].textChanged.connect(lambda _text: self.on_print_speed_changed())
        self.fields["motion_estimate_scale"].textChanged.connect(lambda _text: self.on_motion_estimate_scale_changed())
        self.fields["hatch_pattern"].currentTextChanged.connect(lambda _text: self.update_pattern_settings())
        self.fields["fill_source"].currentIndexChanged.connect(lambda _index: self.update_pattern_settings())
        self.fields["fit_mode"].currentIndexChanged.connect(lambda _index: self.update_fit_fields())
        self.fill_wide_strokes.toggled.connect(lambda _checked: self.update_pattern_settings())
        self.update_pattern_settings()
        self.update_fit_fields()
        self.load_generator_tabs()
        self.build_dashboard()
        self.build_menus()
        self.show_tool("Convert")
        self.update_file_status()
        self.svg_path.textChanged.connect(lambda _text: self.update_file_status())
        self.gcode_path.textChanged.connect(lambda _text: self.update_file_status())

    def active_source_tab(self):
        """The tab that supplies artwork; None when Convert is active."""
        current = self.stack.currentWidget()
        return None if current is self.convert_root else current

    def resolve_active_source(self):
        """Return ``(svg_path, source_tab)`` for the active tab.

        Convert returns the Artwork row's file. A generator tab is built from
        its current controls. Raises ``ValueError`` with the user-facing reason.
        """
        current = self.stack.currentWidget()
        if current is self.dashboard:
            raise ValueError("Open a tool from All tools, or the Convert page, first.")
        tab = None if current is self.convert_root else current
        if tab is None:
            path = self.svg_path.text().strip()
            if not path:
                raise ValueError("Choose an artwork file first.")
            if not os.path.exists(path):
                raise ValueError(f"Artwork file not found: {path}")
            return path, self.convert_root
        builder = getattr(tab, "build_svg", None)
        if not callable(builder):
            name = self.current_tool
            raise ValueError(f"The {name} tab cannot supply artwork.")
        self.status.setText(f"Building {self.current_tool} artwork...")
        QApplication.processEvents()
        path = builder()
        if not path:
            raise ValueError("The generator produced no SVG.")
        return str(path), tab

    def settings_for_source(self, source_tab):
        """Build settings for the active tab.

        A generator page is already laid out in millimetres, so it is plotted
        1:1 with the fit mode manual. The Convert tab's auto fit would
        otherwise renormalize every generator result to the reach circle and
        hide the tab's Artwork scale control.
        """
        settings = self.settings()
        if source_tab is not self.convert_root:
            settings = dataclasses.replace(
                settings, fit_mode="manual", scale=1.0
            )
        return settings

    def on_tool_changed(self):
        """A preview belongs to one tool; switching tools only marks it stale."""
        current = self.stack.currentWidget()
        self.tab_preview_stale = (
            bool(self.moves)
            and self.preview_tab is not None
            and current is not self.preview_tab
            and current is not self.dashboard
        )
        self.update_stale_warning()

    def show_tool(self, title):
        """Switch to a tool page and keep the Tools menu checkmark in sync."""
        index = self.tool_index.get(title)
        if index is None:
            return
        self.stack.setCurrentIndex(index)
        self.current_tool = title
        action = getattr(self, "tool_actions", {}).get(title)
        if action is not None and not action.isChecked():
            action.setChecked(True)
        self.setWindowTitle(f"{title} - SVG to XY Theta G-code Converter")
        self.on_tool_changed()

    def build_dashboard(self):
        """Fill the All tools page with one card per tool, grouped."""
        heading = QLabel("All tools")
        heading.setStyleSheet("font-size: 16px; font-weight: 600;")
        self.dashboard_layout.addWidget(heading)
        hint = QLabel(
            "Choose a tool. Artwork, preview, and Save stay available on every "
            "page."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #475569;")
        self.dashboard_layout.addWidget(hint)
        entries = [("Convert", "Imported artwork to G-code.", "Core")]
        entries += [
            (title, description, group)
            for title, _widget, group, description in self.generator_tools
        ]
        groups = {}
        for title, description, group in entries:
            groups.setdefault(group, []).append((title, description))
        ordered_groups = [
            name for name in ("Core", "Photo-based", "Algorithm only")
            if name in groups
        ]
        ordered_groups += [name for name in groups if name not in ordered_groups]
        for group in ordered_groups:
            items = groups[group]
            box = QGroupBox(group)
            grid = QGridLayout(box)
            grid.setHorizontalSpacing(8)
            grid.setVerticalSpacing(8)
            for card, (title, description) in enumerate(items):
                button = QPushButton(f"{title}\n{description}")
                button.setMinimumHeight(64)
                button.setToolTip(description)
                button.clicked.connect(
                    lambda _checked=False, name=title: self.show_tool(name)
                )
                grid.addWidget(button, card // 2, card % 2)
            self.dashboard_layout.addWidget(box)
        self.dashboard_layout.addStretch(1)

    def _add_tool_action(self, menu, title, shortcut=""):
        action = QAction(title, self)
        action.setCheckable(True)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(
            lambda _checked=False, name=title: self.show_tool(name)
        )
        self.tool_action_group.addAction(action)
        menu.addAction(action)
        self.tool_actions[title] = action

    def build_menus(self):
        """File / Tools / View / Help menus; tool selection lives in Tools."""
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        open_action = QAction("&Open Artwork...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.pick_svg)
        file_menu.addAction(open_action)
        output_action = QAction("Set G-code &Destination...", self)
        output_action.setShortcut("Ctrl+Shift+S")
        output_action.triggered.connect(self.pick_gcode)
        file_menu.addAction(output_action)
        self.save_action = QAction("&Save G-code", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.convert)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator()
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menu.addMenu("&Tools")
        self.tools_menu = tools_menu
        self.all_tools_action = QAction("&All Tools", self)
        self.all_tools_action.setShortcut("Ctrl+T")
        self.all_tools_action.triggered.connect(
            lambda: self.show_tool("All tools")
        )
        tools_menu.addAction(self.all_tools_action)
        tools_menu.addSeparator()
        self.tool_action_group = QActionGroup(self)
        self.tool_action_group.setExclusive(True)
        self._add_tool_action(tools_menu, "Convert", "Ctrl+1")
        shortcuts = [
            "Ctrl+2", "Ctrl+3", "Ctrl+4", "Ctrl+5", "Ctrl+6",
            "Ctrl+7", "Ctrl+8", "Ctrl+9", "Ctrl+0",
        ]
        groups = {}
        for title, _widget, group, _description in self.generator_tools:
            groups.setdefault(group, []).append(title)
        ordered_groups = [
            name for name in ("Photo-based", "Algorithm only")
            if name in groups
        ]
        ordered_groups += [name for name in groups if name not in ordered_groups]
        shortcut_index = 0
        for group in ordered_groups:
            titles = groups[group]
            submenu = tools_menu.addMenu(group)
            for title in titles:
                shortcut = (
                    shortcuts[shortcut_index]
                    if shortcut_index < len(shortcuts)
                    else ""
                )
                self._add_tool_action(submenu, title, shortcut)
                shortcut_index += 1

        view_menu = menu.addMenu("&View")
        reach_action = QAction("Machine Reach Guide", self)
        reach_action.setCheckable(True)
        reach_action.setChecked(self.show_machine_reach.isChecked())
        reach_action.toggled.connect(self.show_machine_reach.setChecked)
        self.show_machine_reach.toggled.connect(reach_action.setChecked)
        view_menu.addAction(reach_action)
        pen_path_action = QAction("Pen-down Path", self)
        pen_path_action.setCheckable(True)
        pen_path_action.setChecked(self.show_pen_down_path.isChecked())
        pen_path_action.toggled.connect(self.show_pen_down_path.setChecked)
        self.show_pen_down_path.toggled.connect(pen_path_action.setChecked)
        view_menu.addAction(pen_path_action)
        view_menu.addSeparator()
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl+=")
        zoom_in_action.triggered.connect(self.gl_preview.zoom_in)
        view_menu.addAction(zoom_in_action)
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.gl_preview.zoom_out)
        view_menu.addAction(zoom_out_action)
        reset_view_action = QAction("&Reset Preview View", self)
        reset_view_action.setShortcut("Ctrl+Shift+R")
        reset_view_action.triggered.connect(self.gl_preview.reset_zoom)
        view_menu.addAction(reset_view_action)
        view_menu.addSeparator()
        log_action = QAction("Show &Log", self)
        log_action.setCheckable(True)
        log_action.setChecked(True)
        log_action.toggled.connect(self.log.setVisible)
        view_menu.addAction(log_action)

        help_menu = menu.addMenu("&Help")
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        recommended_action = QAction("&Recommended Settings", self)
        recommended_action.triggered.connect(self.show_recommended_settings)
        help_menu.addAction(recommended_action)
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        self.file_status = QLabel()
        self.statusBar().addPermanentWidget(self.file_status, 1)

    def update_file_status(self):
        artwork = self.svg_path.text().strip() or "(none)"
        gcode = self.gcode_path.text().strip() or "(none)"
        self.file_status.setText(
            f"Artwork: {artwork}    |    G-code: {gcode}"
        )

    def show_shortcuts(self):
        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            "Ctrl+O  Open artwork\n"
            "Ctrl+Shift+S  Set G-code destination\n"
            "Ctrl+S  Save G-code\n"
            "Ctrl+T  All tools dashboard\n"
            "Ctrl+1  Convert, Ctrl+2...0  other tools in menu order\n"
            "F5 (Preview button)  Build the active tool\n"
            "Ctrl+arrows / wheel  Zoom the preview (View menu)\n"
            "F1  This list",
        )

    def show_about(self):
        version = getattr(converter, "GEOMETRY_VERSION", "unknown")
        QMessageBox.about(
            self,
            "About",
            "<b>SVG to XY Theta G-code Converter</b><br>"
            f"Converter core {version}<br>"
            "PySide6/OpenGL preview with the All tools generator dashboard.<br>"
            "Third-party generator notices live in "
            "<code>software/generator_tabs/*_NOTICE.md</code>.",
        )

    def show_recommended_settings(self):
        QMessageBox.information(
            self,
            "Recommended Starting Settings",
            "All generators assume a 200 x 200 mm page, a 0.3 mm pen, and the "
            "1:1 preview unless noted.\n\n"
            "Convert: Fit bed (auto), Fill spacing 3 mm, linear or crosshatch, "
            "feed 700 / travel 3000 mm/min.\n"
            "Flow Field: noise source, scale 60 mm, octaves 3, spacing 3 mm, "
            "step 1 mm, 400 steps (use spacing 4 mm for a first plot).\n"
            "Line Draw: mode both, edge 35 %, hatch 2 mm, levels 144/64/16, "
            "jitter 0.25 mm, simplify 0.75 px, resolution 900 px.\n"
            "3D Wireframe: source Cube, size 2, detail 24, hidden-line "
            "wireframe, yaw 35 / pitch -25, perspective 4x radius, target "
            "width 140 mm, sample 0.7 mm.\n"
            "Harmonograph: physical model, d 900 / c 800 / p 900 / q 700 mm, "
            "A 10 / B 10 deg, R 0.001 / S 0.001, f 0.300 / g 0.302 Hz, "
            "disk 0.0008 Hz, 300 s, 12k samples.\n"
            "Snowflake: 6 arms, depth 3, length 45 %, branch angle 35 deg, "
            "branch scale 55 %, jitter 8 deg / 15 %.\n"
            "Truchet: quarter arcs, tile 12 mm, 10 arc segments, margin 6 mm.\n"
            "Text: size 12 mm, tracking 0.4 mm, line spacing 140 %, "
            "alignment left.\n"
            "Substitution: 3 colours, 4 iterations (32 x 32), colour "
            "boundaries, margin 6 mm.\n"
            "Postcard: 7x5 in landscape, margin 8 mm, line spacing 9 mm, "
            "stamp 25 x 30 mm, text 6 mm, tracking 0.2 mm.\n"
            "SquiggleCam: 50 rows, frequency 150, amplitude 1.0, spacing 4 px, "
            "resolution 700 px, brightness 0, contrast 0, min 0 / max 255.\n"
            "Pixel Art: mode big, pitch 0.6 mm (or line mode for denser "
            "runs), max grid 96, alpha 128, ignore white; paths auto-fit the "
            "page.\n"
            "Wobble: frequency 3 mm, amplitude 0.5 mm, jitter 20 %, seed 7, "
            "endpoint wobble on. Preview a tool first; Wobble uses its "
            "contours.\n"
            "Plotterfun: load an image inside the page, pick an algorithm, "
            "keep its defaults, then Export SVG to plot.\n"
            "Voronoi: 120 points, seed 7, relax 1, cell boundaries, margin "
            "6 mm.\n"
            "Path Prep: merge 5 deg / 0.05 mm, duplicate 0.05 mm, gap 0.2 mm, "
            "sort on; preview a tool first.\n"
            "Layers: pick a colour layer (or All colours) from an imported "
            "SVG.",
        )

    def update_stale_warning(self):
        if self.tab_preview_stale:
            self.stale_warning.setText(
                "Preview is from another tab - press Preview to rebuild."
            )
            self.stale_warning.show()
        elif self.preview_dirty and self.moves:
            self.stale_warning.setText(
                "Settings changed since this preview - press Preview to rebuild."
            )
            self.stale_warning.show()
        else:
            self.stale_warning.hide()

    def generator_status(self, message):
        """Status-line entry point for generator tabs."""
        self.status.setText(str(message))

    def artwork_path(self):
        """Path currently in the static Artwork row, for generator tabs."""
        return self.svg_path.text().strip()

    def current_contours(self):
        """Preview contours in millimetres, for post-process tools."""
        return self.contours

    def adopt_artwork(self, path):
        """Load external tool output (for example Plotterfun) as artwork."""
        path = str(path)
        if not os.path.exists(path):
            self.log.append(f"External SVG is missing: {path}")
            return
        self.svg_path.setText(path)
        self.update_suggested_gcode_path(path)
        self.auto_configure_shading(path)
        self.raw_cache_key = None
        self.raw_contours = None
        self.show_tool("Convert")
        self.status.setText("Artwork loaded - press Preview to build it.")
        self.log.append(f"External SVG loaded as artwork: {path}")

    def load_generator_tabs(self):
        """Add one page per `software/generator_tabs/*_tab.py` module."""
        try:
            from generator_tabs import load_tabs
        except Exception as exc:  # a missing package must not break Convert
            self.log.append(f"Generator tabs unavailable: {exc}")
            return
        for title, widget, error in load_tabs(self):
            if widget is None:
                self.log.append(f"Generator tab '{title}' failed: {error}")
                continue
            index = self.stack.addWidget(widget)
            self.tool_index[title] = index
            self.generator_tools.append(
                (
                    title,
                    widget,
                    getattr(widget, "GROUP", "Generators"),
                    getattr(widget, "DESCRIPTION", ""),
                )
            )
            self.log.append(f"Generator tab loaded: {title}")

    def pick_svg(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose artwork",
            "",
            "Artwork (*.svg *.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff *.gif);;"
            "SVG files (*.svg);;Images (*.jpg *.jpeg *.png *.bmp *.webp *.tif *.tiff *.gif);;"
            "All files (*.*)",
        )
        if path:
            self.svg_path.setText(path)
            self.update_suggested_gcode_path(path)
            self.auto_configure_shading(path)
            self.raw_cache_key = None
            self.raw_contours = None
            kind = "Image" if converter.is_raster_image(path) else "SVG"
            self.log.append(f"{kind} selected. Press Preview to regenerate.")

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
        """Report what this SVG can be hatched from, and set tone starter values.

        The fill *source* stays on Auto and resolves per file, so the user never
        has to decide between vector and image tone. This only supplies
        tone-friendly starter values when the artwork's tone comes from
        something the vector path cannot see.
        """
        try:
            sources = converter.svg_fill_sources(svg_path)
        except Exception as exc:  # noqa: BLE001
            self.log.append(f"Auto fill: could not inspect {os.path.basename(svg_path)}: {exc}")
            return
        tone_only = bool(sources["image"] or sources["gradient"])
        if tone_only:
            if float(self.fields["hatch_spacing_mm"].text() or 0.0) <= 0.0:
                self.fields["hatch_spacing_mm"].setText("4")
            if int(float(self.fields["shade_levels"].text() or 1)) < 4:
                self.fields["shade_levels"].setText("4")
            self.fields["shade_angle_step_deg"].setText("45")
            reason = "embedded image" if sources["image"] else "gradient paint"
            if converter.is_raster_image(svg_path):
                reason = "photo tone"
            self.log.append(
                f"Auto fill: this artwork carries {reason}, so Fill source Auto will "
                "hatch the rendered image."
            )
            if sources["gradient"]:
                self.log.append(
                    "Auto fill: gradient paint detected. Fill pattern 'sine_gradient' "
                    "plots a gradient as continuous adjacent sinusoids whose amplitude "
                    "follows the tone."
                )
            return
        stats = self.svg_tone_stats(svg_path)
        if stats and stats["p95"] - stats["p05"] >= 0.18 and stats["p95"] >= 0.25:
            if int(float(self.fields["shade_levels"].text() or 1)) < 4:
                self.fields["shade_levels"].setText("4")
            self.fields["shade_angle_step_deg"].setText("45")
        if sources["filled"]:
            detail = f"{sources['filled']} filled shapes"
        elif sources["outline"]:
            detail = f"{sources['outline']} stroke-only elements"
        else:
            detail = ""
        if detail:
            if sources["filled"]:
                self.log.append(
                    f"Auto fill: {detail} found, so Fill source Auto will hatch the "
                    "SVG's own regions and stay inside them."
                )
                if sources["filled"] >= 40:
                    self.log.append(
                        f"Auto fill: {sources['filled']} filled shapes with no image or "
                        "gradient looks like a traced bitmap. A trace has no gradients "
                        "left and hatching its layers separately is slow; open the "
                        "source photo instead (Browse accepts jpg/png), where one fill "
                        "reads the tone."
                    )
            else:
                self.log.append(
                    f"Auto fill: {detail} found; Fill source Auto will hatch the regions "
                    "their closed outlines enclose and stay inside them."
                )
        else:
            self.log.append(
                "Auto fill: no filled shapes or closed outlines found. "
                "Set Fill source to Image tone if this artwork should be hatched from pixels."
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
        text_values = {}
        for key, edit in self.fields.items():
            if isinstance(edit, QComboBox):
                # Combos show a human label and carry the stored value as data.
                value = edit.currentData()
                text_values[key] = edit.currentText() if value is None else value
            else:
                text_values[key] = edit.text()
        bool_values = {
            "flip_y": self.flip_y.isChecked(),
            "include_z": self.use_z.isChecked(),
            "compensate_pen_width": self.compensate_pen.isChecked(),
            "expand_strokes": self.expand_strokes.isChecked(),
            "fill_wide_strokes": self.fill_wide_strokes.isChecked(),
            "keep_down_bridges": self.keep_down_bridges.isChecked(),
            "sine_rows_connected": self.sine_rows_connected.isChecked(),
            "monotonic_theta": self.monotonic_theta.isChecked(),
            "toolhead_status_handshake": self.toolhead_status_handshake.isChecked(),
            "toolhead_handshake_recover": self.toolhead_handshake_recover.isChecked(),
        }
        settings = converter.settings_from_values(text_values, bool_values)
        self.print_speed_mm_s()
        return settings

    def update_pattern_settings(self):
        # Read the stored value, not the label: the combo shows readable labels
        # ("gradient waves (sine_gradient)") over canonical ids.
        combo = self.fields["hatch_pattern"]
        pattern = converter.normalized_hatch_pattern(combo.currentData() or combo.currentText())
        fill_source = self.fields["fill_source"].currentData() or "auto"

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
        set_visible("gradient_wave_amplitude_pct", pattern == "sine_gradient")
        set_visible("gradient_wave_density_pct", pattern == "sine_gradient")
        set_visible("shade_angle_step_deg", pattern in ("linear", "crosshatch", "diagonal", "diagonal_crosshatch", "cubic", "waves", "gyroid"))
        # Sampling resolution only matters when image tone can be used, which
        # "Auto" may still choose, so it stays visible for both.
        set_visible("raster_px_per_unit", fill_source != "shapes")
        set_visible("stroke_fill_ratio", self.fill_wide_strokes.isChecked())

    def fit_mode(self):
        return self.fields["fit_mode"].currentData() or "fill"

    def update_fit_fields(self):
        """An auto fit owns Scale, so the field shows the value but is not typed."""
        auto = self.fit_mode() != "manual"
        scale_edit = self.fields["scale"]
        scale_edit.setReadOnly(auto)
        scale_edit.setToolTip(
            converter.FIELD_TOOLTIPS["scale"]
            if not auto
            else "Set by the Fit mode. Choose Fit = Manual to type a scale."
        )

    def pattern_size_values(self, settings):
        return converter.pattern_size_values(settings)

    def pattern_spacing(self, settings, pattern, fallback=None):
        if fallback is None:
            fallback = float(getattr(settings, "hatch_spacing_mm", 0.0))
        return converter.pattern_size_override(pattern, fallback, self.pattern_size_values(settings))

    def build_preview_moves(self, contours, settings, cancel_check=None, program_plan=None):
        return converter.build_preview_moves(contours, settings, cancel_check, program_plan)

    def raw_geometry_key(self, svg_path, settings, fill=True):
        stat = os.stat(svg_path)
        return (
            os.path.abspath(svg_path),
            stat.st_mtime_ns,
            stat.st_size,
            bool(fill),
            float(settings.tolerance),
            bool(settings.flip_y),
            bool(getattr(settings, "expand_strokes", False)),
            float(getattr(settings, "hatch_spacing_mm", 0.0)),
            float(getattr(settings, "hatch_angle_deg", 0.0)),
            str(getattr(settings, "hatch_pattern", "crosshatch")).lower(),
            tuple(sorted(self.pattern_size_values(settings).items())),
            float(getattr(settings, "gradient_wave_amplitude_pct", 50.0)),
            float(getattr(settings, "gradient_wave_density_pct", 100.0)),
            bool(getattr(settings, "sine_rows_connected", True)),
            int(getattr(settings, "shade_levels", 1)),
            float(getattr(settings, "shade_angle_step_deg", 90.0)),
            str(getattr(settings, "fill_source", "auto")).lower(),
            float(getattr(settings, "raster_px_per_unit", 2.0)),
            bool(getattr(settings, "fill_wide_strokes", False)),
            float(getattr(settings, "stroke_fill_ratio", 2.0)),
            float(getattr(settings, "pen_diameter_mm", 0.0)),
            # `parse_svg_geometry` generates fill at the on-paper resolution for
            # this scale, so a scale change must invalidate the parsed geometry
            # even though the scaling itself happens later.
            float(getattr(settings, "scale", 1.0)),
            str(getattr(settings, "fit_mode", "manual")).lower(),
            # The bed-step limit changes which point the plan may rotate to, so
            # a geometry re-read is required when it moves.
            float(getattr(settings, "theta_max_step_deg", 10.0)),
        )

    def artwork_bounds_mm(self, artwork_path, settings):
        """Paper-space bounds for artwork whose outlines cannot be measured.

        A raster is its pixels; an SVG with no drawable outline (one that is
        only an embedded photo, for example) is its viewBox. Both are what an
        auto fit has to size when `parse_svg_geometry` comes back empty.
        """
        scale = float(getattr(settings, "scale", 1.0))
        if not math.isfinite(scale) or scale <= 0.0:
            scale = 1.0
        if converter.is_raster_image(artwork_path):
            image = QImage(artwork_path)
            if image.isNull():
                return []
            width, height = float(image.width()), float(image.height())
        else:
            renderer = QSvgRenderer(artwork_path)
            view = renderer.viewBoxF()
            if view.isNull() or view.width() <= 0 or view.height() <= 0:
                size = renderer.defaultSize()
                view = QRectF(0.0, 0.0, float(size.width()), float(size.height()))
            if view.width() <= 0 or view.height() <= 0:
                return []
            width, height = float(view.width()), float(view.height())
        width *= scale
        height *= scale
        return [
            (0.0, 0.0),
            (width, 0.0),
            (width, height),
            (0.0, height),
            (0.0, 0.0),
        ]

    def fitted_settings_for_artwork_bounds(self, settings, artwork_path):
        """Apply the auto fit to artwork that has no outlines to measure.

        An SVG carries outlines that say how big the artwork is; a photo does
        not, so the image bounds stand in for them. Without this the first pass
        would fill at whatever scale the field still holds - often 1.0 on a
        fresh session, which for a 4000-pixel photo is four metres of paper.
        """
        bounds = self.artwork_bounds_mm(artwork_path, settings)
        if not bounds:
            return settings
        return self.fitted_settings(settings, [bounds])

    def raster_shade_contours(self, svg_path, settings, cancel_check=None):
        converter.check_cancelled(cancel_check)
        spacing = float(getattr(settings, "hatch_spacing_mm", 0.0))
        if spacing <= 0:
            return []
        # Fill spacing and the pattern sizes are on-paper millimetres, but this
        # path generates in SVG user units and `apply_geometry_settings` scales
        # the result by `settings.scale` afterwards. Convert once, at the top: on
        # an artwork that is 1000 units wide, an unconverted "2 mm" fill is two
        # user units, so the lattice is built ~5x too dense and then shrunk -
        # seconds of work and hundreds of thousands of points for a 4 mm fill.
        artwork_scale = float(getattr(settings, "scale", 1.0))
        if not math.isfinite(artwork_scale) or artwork_scale <= 0.0:
            artwork_scale = 1.0
        levels = max(1, int(getattr(settings, "shade_levels", 1)))
        max_dim = 2400

        if converter.is_raster_image(svg_path):
            # A photo is already pixels: one view unit is one source pixel, which
            # samples the tone exactly and needs no renderer. `Raster px/unit`
            # cannot mean anything here, so the only scaling is the max_dim cap.
            image = QImage(svg_path)
            if image.isNull():
                return []
            image = image.convertToFormat(QImage.Format_ARGB32)
            view = QRectF(0.0, 0.0, float(image.width()), float(image.height()))
            px_per_unit = 1.0
        else:
            px_per_unit = max(float(getattr(settings, "raster_px_per_unit", 2.0)), 0.1)
            renderer = QSvgRenderer(svg_path)
            view = renderer.viewBoxF()
            if view.isNull() or view.width() <= 0 or view.height() <= 0:
                size = renderer.defaultSize()
                view = QRectF(0.0, 0.0, float(size.width()), float(size.height()))

        width = max(1, int(math.ceil(view.width() * px_per_unit)))
        height = max(1, int(math.ceil(view.height() * px_per_unit)))
        scale_down = max(width / max_dim, height / max_dim, 1.0)
        if scale_down > 1.0:
            px_per_unit /= scale_down
            width = max(1, int(math.ceil(view.width() * px_per_unit)))
            height = max(1, int(math.ceil(view.height() * px_per_unit)))

        if not converter.is_raster_image(svg_path):
            downscaled = QImage(width, height, QImage.Format_ARGB32)
            downscaled.fill(QColor(255, 255, 255, 0))
            painter = QPainter(downscaled)
            renderer.render(painter, QRectF(0.0, 0.0, float(width), float(height)))
            painter.end()
            image = downscaled
        elif (width, height) != (image.width(), image.height()):
            image = image.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        def darkness_at(x, y):
            converter.check_cancelled(cancel_check)
            px = int((x - view.left()) * px_per_unit)
            py = int((y - view.top()) * px_per_unit)
            if px < 0 or py < 0 or px >= image.width() or py >= image.height():
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
        # `terrain` reads Terrain size mm as the hill width, not the contour
        # pitch, so its pitch always comes from Fill spacing.
        if pattern == "terrain":
            active_spacing = spacing / artwork_scale
        else:
            active_spacing = self.pattern_spacing(settings, pattern, spacing) / artwork_scale
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
                converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
                x = math.floor(min_rx / cell) * cell
                while x < max_rx:
                    converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
                x = view.left()
                while x < view.right():
                    converter.check_cancelled(cancel_check)
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
            for contour in converter.concentric_region_contours(loops, raster_spacing, cancel_check):
                if len(contour) >= 3:
                    contours.append([maybe_flip(point) for point in contour])

        # Tone-driven sine fill. Unlike every other pattern here the tone is
        # carried by wave amplitude rather than by line density, so it is drawn
        # as one pass at the full spacing instead of one layer per shade level.
        if pattern == "sine_gradient":
            polys = converter.sine_gradient_region_contours(
                (view.left(), view.top(), view.right(), view.bottom()),
                darkness_at,
                active_spacing,
                base_angle,
                amplitude_pct=float(getattr(settings, "gradient_wave_amplitude_pct", 50.0)),
                density_pct=float(getattr(settings, "gradient_wave_density_pct", 100.0)),
                connect_rows=bool(getattr(settings, "sine_rows_connected", True)),
                cancel_check=cancel_check,
            )
            return [[maybe_flip(point) for point in poly] for poly in polys]

        ink_floor = float(converter.INK_FLOOR)

        def raster_inside(x, y):
            if not (view.left() <= x <= view.right() and view.top() <= y <= view.bottom()):
                return False
            return darkness_at(x, y) >= ink_floor

        # Tone-driven stipple: blue-noise dots whose density follows tone.
        if pattern == "stipple":
            points = converter.stipple_points(
                (view.left(), view.top(), view.right(), view.bottom()),
                raster_inside,
                darkness_at,
                active_spacing,
                cancel_check=cancel_check,
            )
            # Each dot is a small closed circle sized on paper (about one pen
            # tip), so it reads as a dot instead of a dash and survives the
            # sub-pen-width filter that runs after the artwork scale is applied.
            radius = converter.stipple_mark_radius(
                float(getattr(settings, "pen_diameter_mm", 0.0))
            ) / artwork_scale
            return [
                [maybe_flip(point) for point in circle]
                for circle in converter.dot_mark_contours(points, radius)
            ]

        # Classic halftone: fixed-pitch dots whose radius follows tone.
        if pattern == "halftone":
            circles = converter.halftone_contours(
                (view.left(), view.top(), view.right(), view.bottom()),
                raster_inside,
                darkness_at,
                active_spacing,
                base_angle,
                cancel_check=cancel_check,
            )
            return [[maybe_flip(point) for point in circle] for circle in circles]

        # Single-line portrait: stipple points walked into one continuous path.
        if pattern == "tsp":
            points = converter.stipple_points(
                (view.left(), view.top(), view.right(), view.bottom()),
                raster_inside,
                darkness_at,
                active_spacing,
                cancel_check=cancel_check,
            )
            line = converter.greedy_single_line(
                points, cell=active_spacing, cancel_check=cancel_check
            )
            if len(line) >= 2:
                return [[maybe_flip(point) for point in line]]
            return []

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
                converter.check_cancelled(cancel_check)
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                mark_radius = max(layer_spacing * 0.055, sample_step)
                row_step = layer_spacing * math.sqrt(3.0) / 2.0
                y = min_ry + row_step * 0.5
                row = 0
                while y <= max_ry:
                    converter.check_cancelled(cancel_check)
                    x = min_rx + layer_spacing * (0.5 if row % 2 == 0 else 1.0)
                    while x <= max_rx:
                        converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                radius = max(layer_spacing * 0.5, sample_step)
                row_step = radius * math.sqrt(3.0)
                y = min_ry + radius
                row = 0
                while y <= max_ry - radius:
                    converter.check_cancelled(cancel_check)
                    x = min_rx + radius + (radius if row % 2 else 0.0)
                    while x <= max_rx - radius:
                        converter.check_cancelled(cancel_check)
                        circle = [world(x + math.cos(2.0 * math.pi * i / steps) * radius, y + math.sin(2.0 * math.pi * i / steps) * radius) for i in range(steps + 1)]
                        add_shape_if_dark(circle, threshold)
                        x += radius * 2.0
                    y += row_step
                    row += 1
            return contours

        if pattern == "hexagonal":
            for layer in range(levels):
                converter.check_cancelled(cancel_check)
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                radius = max(layer_spacing * 0.5, sample_step)
                x_step = radius * 1.5
                y_step = radius * math.sqrt(3.0)
                col = 0
                x = min_rx - radius
                while x <= max_rx + radius:
                    converter.check_cancelled(cancel_check)
                    y = min_ry - radius + (y_step * 0.5 if col % 2 else 0.0)
                    while y <= max_ry + radius:
                        converter.check_cancelled(cancel_check)
                        hexagon = [world(x + math.cos(math.radians(60.0 * i)) * radius, y + math.sin(math.radians(60.0 * i)) * radius) for i in range(7)]
                        for a, b in zip(hexagon, hexagon[1:]):
                            add_segment_if_dark(a, b, threshold)
                        y += y_step
                    x += x_step
                    col += 1
            return contours

        if pattern == "diamonds":
            for layer in range(levels):
                converter.check_cancelled(cancel_check)
                threshold = (layer + 1) / (levels + 1)
                layer_spacing = active_spacing / math.sqrt(layer + 1)
                half = max(layer_spacing * 0.5, sample_step)
                x_min = int(math.floor((min_rx - half) / half)) - 1
                x_max = int(math.ceil((max_rx + half) / half)) + 1
                y_min = int(math.floor((min_ry - half) / half)) - 1
                y_max = int(math.ceil((max_ry + half) / half)) + 1
                for j in range(y_min, y_max + 1):
                    converter.check_cancelled(cancel_check)
                    y = j * half
                    for i in range(x_min, x_max + 1):
                        x = i * half
                        add_segment_if_dark(world(x, y), world(x + half, y + half), threshold)
                        add_segment_if_dark(world(x, y), world(x + half, y - half), threshold)
            return contours

        if pattern == "triangular":
            for layer in range(levels):
                converter.check_cancelled(cancel_check)
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
                    converter.check_cancelled(cancel_check)
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

        # Tone-traced terrain: the image's own shading is the elevation, so the
        # contour lines follow the faces and features instead of a synthetic
        # field. The level interval is calibrated to the photo's mean tone
        # gradient, so Fill spacing is the average gap between lines whatever
        # the picture contains; Terrain size mm is the smoothing radius.
        if pattern == "terrain":
            hill_size = float(getattr(settings, "terrain_size_mm", 0.0)) / artwork_scale
            blur = hill_size if hill_size > 0.0 else active_spacing * 0.5
            # Sample on the pixel centres: the outermost grid line must sit
            # inside the image, or the tone cliff at the edge draws a rectangle
            # of contours around the artwork.
            edge = 0.5 / px_per_unit
            return [
                [maybe_flip(point) for point in line]
                for line in converter.tone_terrain_contours(
                    (
                        view.left() + edge,
                        view.top() + edge,
                        view.right() - edge,
                        view.bottom() - edge,
                    ),
                    active_spacing,
                    darkness_at,
                    # Two source pixels: the contour pitch only needs half the
                    # spacing, but thin features (a scan's linework) have to be
                    # sampled or they vanish between grid lines.
                    step=min(active_spacing * 0.5, 2.0 / px_per_unit),
                    blur=blur,
                    min_step=sample_step,
                    cancel_check=cancel_check,
                )
            ]

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
            converter.check_cancelled(cancel_check)
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
                    converter.check_cancelled(cancel_check)
                    active_start = None
                    last_point = None
                    t = t_min
                    while t <= t_max:
                        converter.check_cancelled(cancel_check)
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

    def concentric_from_closed_contours(self, contours, settings, cancel_check=None):
        converter.check_cancelled(cancel_check)
        spacing = self.pattern_spacing(settings, "concentric")
        if spacing <= 0:
            return []
        close_tol = max(float(getattr(settings, "tolerance", 0.25)) * 2.0, 0.5)
        polygons = []
        for contour in contours:
            converter.check_cancelled(cancel_check)
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
            converter.check_cancelled(cancel_check)
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
            converter.check_cancelled(cancel_check)
            row = y * width
            src = y * bpl
            for x in range(width):
                if data[src + x] == 0:
                    dist[row + x] = 0.0

        diag = math.sqrt(2.0)
        for y in range(height):
            converter.check_cancelled(cancel_check)
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
            converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
                d = converter.distance(endpoint, point)
                if d < best_d and connector_inside(endpoint, point):
                    best = (d, index)
                    best_d = d
            return best

        def join_concentric_levels(levels):
            chains = []
            max_gap_px = spacing * px_per_unit * 2.35
            for level_index, loops in enumerate(levels):
                converter.check_cancelled(cancel_check)
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
            converter.check_cancelled(cancel_check)
            threshold = level * px_per_unit
            segments = []
            for y in range(height - 1):
                converter.check_cancelled(cancel_check)
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

    def lattice_from_closed_contours(self, contours, settings, cancel_check=None):
        converter.check_cancelled(cancel_check)
        pattern = converter.normalized_hatch_pattern(getattr(settings, "hatch_pattern", "crosshatch"))
        spacing = self.pattern_spacing(settings, pattern)
        if spacing <= 0:
            return []
        close_tol = max(float(getattr(settings, "tolerance", 0.25)) * 2.0, 0.5)
        polygons = []
        for contour in contours:
            converter.check_cancelled(cancel_check)
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
            converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
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
            j_min = int(math.floor((rmin_y - row_step) / row_step)) - 1
            j_max = int(math.ceil((rmax_y + row_step) / row_step)) + 1
            i_min = int(math.floor((rmin_x - side) / side - j_max * 0.5)) - 1
            i_max = int(math.ceil((rmax_x + side) / side - j_min * 0.5)) + 1

            def tri_point(i, j):
                return ((i + j * 0.5) * side, j * row_step)

            for j in range(j_min, j_max + 1):
                converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
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
                converter.check_cancelled(cancel_check)
                y = math.floor((rmin_y - radius) / y_step) * y_step + (y_step * 0.5 if col % 2 else 0.0)
                while y <= rmax_y + radius:
                    converter.check_cancelled(cancel_check)
                    vertices = [world(x + math.cos(math.radians(60.0 * i)) * radius, y + math.sin(math.radians(60.0 * i)) * radius) for i in range(7)]
                    for a, b in zip(vertices, vertices[1:]):
                        add_segment(a, b)
                    y += y_step
                x += x_step
                col += 1
        if pattern in ("triangular", "diamonds", "hexagonal"):
            return converter.chain_segments_to_paths(out)
        return out

    def load_contours(self, svg_path, settings, cancel_check=None, notice=None, fill=True):
        """Parse the artwork, with or without its fill.

        ``fill=False`` returns outlines only. An auto fit needs the artwork's
        size before the fill can be generated - the fill spacing is
        millimetres - so the preview measures the outlines first and builds the
        fill once, at the fitted scale, instead of filling twice.
        """
        converter.check_cancelled(cancel_check)
        key = self.raw_geometry_key(svg_path, settings, fill)
        if self.raw_cache_key != key or self.raw_contours is None:
            source = converter.resolve_fill_source(settings, svg_path)
            parse_hatch_spacing = (
                0.0 if source == "tone" or not fill else float(getattr(settings, "hatch_spacing_mm", 0.0))
            )
            fill_stats = {"fill_contours": 0}
            if converter.is_raster_image(svg_path):
                # A photo has no vector geometry at all: its tone fill is the
                # whole drawing, so skip the SVG parse and go straight to the
                # rendered-image path.
                raw_contours = self.raster_shade_contours(svg_path, settings, cancel_check)
                fill_stats["fill_contours"] = len(raw_contours)
                self.raw_contours = raw_contours
                self.raw_cache_key = key
                if notice:
                    notice(self.describe_fill(svg_path, settings, "tone", len(raw_contours)))
                converter.check_cancelled(cancel_check)
                return converter.apply_geometry_settings(self.raw_contours, settings)
            raw_contours = converter.parse_svg_geometry(
                svg_path,
                settings.tolerance,
                settings.flip_y,
                parse_hatch_spacing,
                float(getattr(settings, "hatch_angle_deg", 0.0)),
                str(getattr(settings, "hatch_pattern", "crosshatch")).lower(),
                int(getattr(settings, "shade_levels", 1)),
                float(getattr(settings, "shade_angle_step_deg", 90.0)),
                bool(getattr(settings, "expand_strokes", False)),
                float(getattr(settings, "triangle_size_mm", 0.0)),
                self.pattern_size_values(settings),
                cancel_check,
                scale=float(getattr(settings, "scale", 1.0)),
                fill_wide_strokes=bool(getattr(settings, "fill_wide_strokes", False)),
                stroke_fill_ratio=float(getattr(settings, "stroke_fill_ratio", 2.0)),
                pen_diameter=float(getattr(settings, "pen_diameter_mm", 0.0)),
                stats=fill_stats,
                gradient_amplitude_pct=float(getattr(settings, "gradient_wave_amplitude_pct", 50.0)),
                gradient_density_pct=float(getattr(settings, "gradient_wave_density_pct", 100.0)),
            )
            if source == "tone" and fill:
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
                        cancel_check,
                        scale=float(getattr(settings, "scale", 1.0)),
                    )
                    if pattern == "concentric":
                        tone_contours = self.concentric_from_closed_contours(centerline_contours, settings, cancel_check)
                    else:
                        tone_contours = self.lattice_from_closed_contours(centerline_contours, settings, cancel_check)
                    raw_contours.extend(tone_contours)
                    fill_stats["fill_contours"] += len(tone_contours)
                else:
                    tone_contours = self.raster_shade_contours(svg_path, settings, cancel_check)
                    raw_contours.extend(tone_contours)
                    fill_stats["fill_contours"] += len(tone_contours)
            converter.check_cancelled(cancel_check)
            self.raw_contours = raw_contours
            self.raw_cache_key = key
            if notice:
                notice(self.describe_fill(svg_path, settings, source, fill_stats["fill_contours"]))
        converter.check_cancelled(cancel_check)
        return converter.apply_geometry_settings(self.raw_contours, settings)

    def describe_fill(self, svg_path, settings, source, fill_contours):
        """One log line explaining what the fill settings will actually hatch."""
        spacing = float(getattr(settings, "hatch_spacing_mm", 0.0))
        if spacing <= 0.0:
            return (
                "Fill: off (Fill spacing mm = 0), so only outlines are plotted. "
                "Set a spacing such as 4 to hatch the artwork."
            )
        pattern = converter.normalized_hatch_pattern(getattr(settings, "hatch_pattern", "crosshatch"))
        try:
            sources = converter.svg_fill_sources(svg_path)
        except Exception:  # noqa: BLE001
            sources = {"filled": 0, "outline": 0, "image": 0, "gradient": 0}
        if fill_contours <= 0:
            if sources["image"] and source != "tone":
                return (
                    "Fill: nothing to hatch from the SVG's shapes. This artwork carries an "
                    "embedded image, which only Fill source = Image tone can hatch."
                )
            if sources["image"] or sources["gradient"]:
                return (
                    "Fill: nothing to hatch - the image tone is too light or too small at "
                    "the current Raster px/unit. Raise Raster px/unit or reduce Fill spacing mm."
                )
            return (
                "Fill: nothing to hatch - this SVG has no filled shapes and no closed "
                "outlines, so there is no interior to fill. Its strokes still plot."
            )
        where = "image tone" if source == "tone" else "the SVG's own regions"
        active_spacing = self.pattern_spacing(settings, pattern, spacing)
        if pattern == "sine_gradient":
            if source != "tone":
                return (
                    f"Fill: {active_spacing:g} mm sine waves inside {where}, "
                    f"{fill_contours} wave passes. Amplitude follows visible tone, so "
                    "this pattern needs Fill source = Image tone (or Auto with "
                    "gradient artwork) to read a gradient; otherwise it is a uniform "
                    "sine hatch."
                )
            rows = (
                "joined into continuous strokes"
                if bool(getattr(settings, "sine_rows_connected", True))
                else "as separate rows"
            )
            return (
                f"Fill: {active_spacing:g} mm sine gradient waves, {fill_contours} "
                f"wave passes inside {where}, {rows}. Amplitude follows tone, so "
                "Shade levels do not change this pattern."
            )
        if pattern == "stipple":
            return (
                f"Fill: {active_spacing:g} mm stipple dots inside {where}, "
                f"{fill_contours} marks. Dot density follows tone, so "
                "Shade levels do not change this pattern."
            )
        if pattern == "halftone":
            return (
                f"Fill: {active_spacing:g} mm halftone dots inside {where}, "
                f"{fill_contours} dots. Dot size follows tone, so "
                "Shade levels do not change this pattern."
            )
        if pattern == "tsp":
            return (
                f"Fill: {active_spacing:g} mm single-line path inside {where}, "
                f"{fill_contours} stroke(s). Point density follows tone, so "
                "Shade levels do not change this pattern."
            )
        if pattern == "terrain":
            if source == "tone":
                return (
                    "Fill: terrain contours of the image's own shading, "
                    f"{fill_contours} contour line(s). Darker areas are higher ground, "
                    f"so the lines trace the photo's features; lines closer than half "
                    f"of {spacing:g} mm are skipped so hard outlines are traced once, "
                    "and Shade levels does not change this pattern."
                )
            return (
                f"Fill: {spacing:g} mm terrain contours inside {where}, "
                f"{fill_contours} contour line(s). A flat SVG shape has no tone "
                "gradient to trace, so its hills come from a synthetic height field "
                "and Shade levels darken the fill."
            )
        return f"Fill: {spacing:g} mm {pattern}, {fill_contours} hatch passes inside {where}."

    def print_speed_mm_s(self):
        speed = float(self.fields["print_speed"].text())
        if speed <= 0.0:
            raise ValueError("preview playback speed must be greater than zero.")
        return speed

    def on_print_speed_changed(self):
        self.update_estimate()
        try:
            speed = self.print_speed_mm_s()
        except ValueError:
            return
        self.gl_preview.set_play_speed(speed)

    def motion_estimate_scale(self):
        return float(self.fields["motion_estimate_scale"].text())

    def on_motion_estimate_scale_changed(self):
        try:
            converter.calibrated_motion_seconds(0.0, self.motion_estimate_scale())
        except ValueError:
            return
        self.update_estimate()

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

    def estimate_runtime(self, moves):
        draw_mm = 0.0
        draw_seconds = 0.0
        travel_seconds = 0.0
        pen_seconds = 0.0
        strategy_counts = {}
        for move in moves:
            kind = move.get("type")
            if kind == "draw":
                draw_mm += self.move_strategy_length(move)
                draw_seconds += float(move.get("duration_ms", 0.0)) / 1000.0
                strategy = move.get("strategy", "tangent")
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            elif kind == "travel":
                travel_seconds += float(move.get("duration_ms", 0.0)) / 1000.0
            elif kind in ("pen_up", "pen_down"):
                pen_seconds += float(move.get("duration_ms", 0.0)) / 1000.0

        model_motion_seconds = draw_seconds + travel_seconds
        motion_estimate_scale = self.motion_estimate_scale()
        calibrated_motion_seconds = converter.calibrated_motion_seconds(
            model_motion_seconds,
            motion_estimate_scale,
        )
        model_total_seconds = model_motion_seconds + pen_seconds
        total_seconds = calibrated_motion_seconds + pen_seconds
        return {
            "total_seconds": total_seconds,
            "model_total_seconds": model_total_seconds,
            "draw_seconds": draw_seconds,
            "travel_seconds": travel_seconds,
            "pen_seconds": pen_seconds,
            "motion_estimate_scale": motion_estimate_scale,
            "calibrated_motion_seconds": calibrated_motion_seconds,
            "draw_mm": draw_mm,
            "strategy_counts": strategy_counts,
        }

    def update_estimate(self):
        if not self.moves:
            self.estimate.setText("Estimated time: preview an SVG to calculate.")
            return None
        try:
            estimate = self.estimate_runtime(self.moves)
        except ValueError as exc:
            self.estimate.setText(f"Controller-time estimate unavailable: {exc}")
            return None
        counts = estimate["strategy_counts"]
        axis_summary = f"x_theta {counts.get('x_theta', 0)}, y_theta {counts.get('y_theta', 0)}"
        fallback_count = counts.get("fallback", 0)
        if fallback_count:
            axis_summary += f", fallback {fallback_count}"
        self.estimate.setText(
            "Calibrated controller-time estimate: "
            f"{self.format_duration(estimate['total_seconds'])} "
            f"(model {self.format_duration(estimate['model_total_seconds'])}; "
            f"motion ×{fmt(estimate['motion_estimate_scale'])}; "
            f"draw {self.format_duration(estimate['draw_seconds'])}, "
            f"travel {self.format_duration(estimate['travel_seconds'])}, "
            f"pen {self.format_duration(estimate['pen_seconds'])}; "
            f"draw coordinated motion {fmt(estimate['draw_mm'])}; "
            f"{axis_summary}). Pen dwells are not scaled; refine after more timing runs."
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

    def reach_summary(self):
        """Artwork radius against the configured gantry reach.

        Measured before clipping, so artwork the reach cap would trim is
        reported rather than quietly disappearing.
        """
        info = self.clip_info()
        if not info:
            return ""
        radius, reach = info
        if radius <= reach:
            return f"Machine reach: artwork radius {fmt(radius)} mm is inside {fmt(reach)} mm."
        return (
            f"Machine reach: artwork radius {fmt(radius)} mm exceeds {fmt(reach)} mm by "
            f"{fmt(radius - reach)} mm; the excess is clipped."
        )

    def clip_info(self):
        """Pre-clip artwork radius and the reach cap, or None when unknown."""
        reach = float(getattr(self.gl_preview.settings, "machine_reach_radius_mm", 0.0))
        source = self.raw_contours if self.raw_contours else self.contours
        if reach <= 0.0 or not source:
            return None
        return converter.artwork_radius(source), reach

    def update_clip_warning(self):
        """Show, next to the preview, that the artwork is being cut by the reach.

        A cropped plot still looks like a finished drawing, so an over-scale
        artwork is the one planning mistake the preview cannot show by itself.
        """
        source = self.raw_contours if self.raw_contours else self.contours
        reach = float(getattr(self.gl_preview.settings, "machine_reach_radius_mm", 0.0))
        offset_x = float(self.fields["artwork_offset_x_mm"].text() or 0.0)
        offset_y = float(self.fields["artwork_offset_y_mm"].text() or 0.0)
        off_center = abs(offset_x) > 1e-9 or abs(offset_y) > 1e-9
        if source and reach > 0.0:
            # Enable each fit only when it would actually change something, so
            # the buttons read as "available actions", not permanent furniture.
            self.fit_inside_button.setEnabled(
                off_center
                or abs(converter.fit_scale_to_radius(source, reach) - 1.0) > 1e-3
            )
            self.fill_bed_button.setEnabled(
                off_center
                or abs(converter.fit_scale_to_span(source, 2.0 * reach) - 1.0) > 1e-3
            )
        else:
            self.fit_inside_button.setEnabled(False)
            self.fill_bed_button.setEnabled(False)
        info = self.clip_info()
        if not info:
            self.clip_warning.hide()
            self.gl_preview.set_reach_warning(False)
            return
        radius, reach = info
        clipped = radius > reach
        self.gl_preview.set_reach_warning(clipped)
        if not clipped:
            self.clip_warning.hide()
            return
        outside = (
            "most of the drawing is outside"
            if radius > 1.5 * reach
            else "the corners fall outside"
        )
        self.clip_warning.setText(
            f"Artwork radius {fmt(radius)} mm vs the {fmt(reach)} mm reach: {outside} the "
            "drawable circle. Fill bed sizes the bounds to the bed (corners clipped); "
            "Fit inside keeps the whole drawing."
        )
        self.clip_warning.show()

    def fit_inside(self):
        """Scale so the whole drawing stays inside the reach circle, and keep it."""
        self.select_fit_mode("inside")
        self.fit_to_bed(fill=False)

    def fill_bed(self):
        """Scale so the artwork's bounds touch the reach circle, and keep it."""
        self.select_fit_mode("fill")
        self.fit_to_bed(fill=True)

    def select_fit_mode(self, mode):
        """Make a fit button's behaviour the standing auto-fit for this artwork."""
        combo = self.fields["fit_mode"]
        index = combo.findData(mode)
        if index >= 0 and combo.currentIndex() != index:
            combo.setCurrentIndex(index)
            self.log.append(f"Fit mode set to {combo.itemText(index)}.")

    def fit_to_bed(self, fill=False):
        """Scale, and recenter, the artwork against the drawable reach circle.

        ``fill=False`` keeps every point inside the circle; ``fill=True`` sizes
        the bounding box to the circle's diameter so the bounds touch it and the
        four corners are clipped. Both fits recenter the artwork on the bed,
        because the point of the action is to place the drawing on the bed.
        """
        reach = float(self.fields["machine_reach_radius_mm"].text() or 0.0)
        source = self.raw_contours if self.raw_contours else self.contours
        if reach <= 0.0 or not source:
            self.log.append("Fit: build a preview first so the artwork size is known.")
            return
        current = float(self.fields["scale"].text() or 1.0)
        if fill:
            factor = converter.fit_scale_to_span(source, 2.0 * reach)
            action = "Fill bed"
            goal = f"make the bounds touch the {fmt(reach)} mm reach circle"
        else:
            factor = converter.fit_scale_to_radius(source, reach)
            action = "Fit inside"
            goal = f"keep the whole drawing inside the {fmt(reach)} mm reach circle"
        fitted = current * factor
        if abs(fitted - current) > 1e-6:
            self.fields["scale"].setText(f"{fitted:.4f}")
        # A fit is a placement, so it also returns the artwork to the bed center
        # instead of preserving a manual or dragged offset.
        recentred = (
            abs(float(self.fields["artwork_offset_x_mm"].text() or 0.0)) > 1e-9
            or abs(float(self.fields["artwork_offset_y_mm"].text() or 0.0)) > 1e-9
        )
        self.fields["artwork_offset_x_mm"].setText("0")
        self.fields["artwork_offset_y_mm"].setText("0")
        self.log.append(
            f"{action}: scale {fmt(current)} -> {fmt(fitted)} to {goal}"
            + (", artwork recentred on the bed center." if recentred else ".")
            + " Press Preview to rebuild."
        )

    def mark_preview_dirty(self):
        """Flag that the visible preview no longer matches the settings."""
        if not self.moves or self.preview_dirty:
            return
        self.preview_dirty = True
        self.update_stale_warning()

    def fitted_settings(self, settings, contours):
        """Apply the configured auto-fit to *settings* for this artwork.

        Returns *settings* unchanged when the fit is manual or the artwork is
        already at the wanted size. The caller re-reads the geometry when this
        returns a different object, because the fill is generated at the
        on-paper resolution of the final scale.
        """
        mode = str(getattr(settings, "fit_mode", "manual")).strip().lower()
        if mode not in ("fill", "inside") or not contours:
            return settings
        reach = float(getattr(settings, "machine_reach_radius_mm", 0.0))
        scale = float(getattr(settings, "scale", 0.0))
        if reach <= 0.0 or scale <= 0.0:
            return settings
        if mode == "fill":
            factor = converter.fit_scale_to_span(contours, 2.0 * reach)
        else:
            factor = converter.fit_scale_to_radius(contours, reach)
        fitted = scale * factor
        if fitted <= 0.0 or abs(fitted - scale) <= 1e-6:
            return settings
        return dataclasses.replace(settings, scale=fitted)

    def describe_fit(self, settings, fitted):
        """One log line naming the auto fit and the scale it chose."""
        mode = str(getattr(settings, "fit_mode", "fill")).strip().lower()
        named = "Fill bed" if mode == "fill" else "Fit inside"
        return (
            f"Auto-fit ({named}): Scale {fmt(settings.scale)} -> {fmt(fitted.scale)} "
            f"for the {fmt(fitted.machine_reach_radius_mm)} mm reach circle."
        )

    def on_placement_changed(self, x, y):
        """Follow a preview drag so the next build places the artwork there."""
        self.fields["artwork_offset_x_mm"].setText(f"{x:.2f}")
        self.fields["artwork_offset_y_mm"].setText(f"{y:.2f}")

    def install_preview(self, settings, contours, moves, bed_center, program_gcode):
        # The plan already places the artwork at this offset, so the preview's
        # own placement delta starts at zero and a later drag measures from here.
        self.gl_preview.set_planned_offset(
            (
                float(getattr(settings, "artwork_offset_x_mm", 0.0)),
                float(getattr(settings, "artwork_offset_y_mm", 0.0)),
            )
        )
        self.moves = moves
        self.contours = contours
        self.program_lines = program_gcode.splitlines()
        self.slider.setMaximum(max(0, len(self.moves)))
        self.set_index(len(self.moves))
        self.gl_preview.set_preview(self.contours, self.moves, settings, center=bed_center, play_speed_mm_s=self.print_speed_mm_s())
        # Show the scale the build actually used, so an auto fit is visible in
        # the field and the next build starts from it instead of re-deriving it.
        used_scale = f"{float(getattr(settings, 'scale', 1.0)):.4f}"
        scale_edit = self.fields["scale"]
        if scale_edit.text() != used_scale:
            blocked = scale_edit.blockSignals(True)
            scale_edit.setText(used_scale)
            scale_edit.blockSignals(blocked)
        self.preview_dirty = False
        self.tab_preview_stale = False
        self.preview_tab = self.pending_source_tab
        self.update_stale_warning()
        return settings

    def preview(self):
        if self.preview_thread is not None:
            return
        try:
            svg_path, source_tab = self.resolve_active_source()
        except Exception as exc:
            QMessageBox.warning(self, "Preview needs artwork", str(exc))
            return
        self.pending_source_tab = source_tab
        self.pending_source_path = svg_path
        settings = self.settings_for_source(source_tab)
        if source_tab is not self.convert_root:
            self.log.append(
                "Generator page plotted 1:1; Artwork scale sets its size."
            )
        try:
            self.raw_geometry_key(svg_path, settings)
        except Exception as exc:
            QMessageBox.critical(self, "Preview failed", str(exc))
            return

        self.pause()
        self.preview_button.setEnabled(False)
        self.preview_button.setText("Building...")
        self.cancel_preview_button.setEnabled(True)
        self.save_action.setEnabled(False)
        self.preview_build_bar.setValue(2)
        self.preview_build_bar.show()
        self.preview_stage.setProperty("stage", "Reading settings")
        self.preview_stage.setText("Reading settings | 0.0 s")
        self.preview_stage.show()
        self.status.setText("Building preview...")
        self.preview_started_at = time.monotonic()
        self.preview_elapsed_timer.start(100)

        self.preview_thread = QThread(self)
        self.preview_worker = PreviewWorker(self, svg_path, settings)
        self.preview_worker.moveToThread(self.preview_thread)
        self.preview_thread.started.connect(self.preview_worker.run)
        self.preview_worker.progress.connect(self.set_preview_build_progress)
        self.preview_worker.notice.connect(self.log.append)
        self.preview_worker.finished.connect(self.preview_ready)
        self.preview_worker.failed.connect(self.preview_failed)
        self.preview_worker.cancelled.connect(self.preview_cancelled)
        self.preview_worker.finished.connect(self.preview_thread.quit)
        self.preview_worker.failed.connect(self.preview_thread.quit)
        self.preview_worker.cancelled.connect(self.preview_thread.quit)
        self.preview_thread.finished.connect(self.preview_worker.deleteLater)
        self.preview_thread.finished.connect(self.preview_thread.deleteLater)
        self.preview_thread.finished.connect(self.preview_thread_finished)
        self.preview_thread.start()

    def cancel_preview(self):
        if self.preview_worker is None:
            return
        self.preview_worker.cancel()
        self.cancel_preview_button.setEnabled(False)
        self.preview_stage.setProperty("stage", "Cancelling preview")
        self.update_preview_elapsed()
        self.status.setText("Cancelling preview...")

    def set_preview_build_progress(self, percent, stage):
        self.preview_build_bar.setValue(percent)
        self.preview_build_bar.setFormat(f"{percent}%")
        self.preview_stage.setProperty("stage", stage)
        self.update_preview_elapsed()

    def update_preview_elapsed(self):
        if self.preview_started_at is None:
            return
        stage = self.preview_stage.property("stage") or "Building preview"
        elapsed = time.monotonic() - self.preview_started_at
        self.preview_stage.setText(f"{stage} | {elapsed:.1f} s")

    def preview_ready(self, result):
        settings, contours, moves, bed_center, program_gcode, stats = result
        self.set_preview_build_progress(94, "Preparing OpenGL preview")
        QApplication.processEvents()
        self.install_preview(settings, contours, moves, bed_center, program_gcode)
        deviation = float(stats.get("worst_bed_deviation_mm", 0.0)) if stats else 0.0
        if deviation > 0.0:
            self.log.append(
                "Tolerance %.2f mm: worst commanded bed-path deviation about "
                "%.2f mm at %.1f mm radius (%s). Lower Tolerance or Max bed step "
                "deg if that shows on paper."
                % (
                    float(getattr(settings, "tolerance", 0.0)),
                    deviation,
                    float(stats.get("worst_bed_deviation_radius_mm", 0.0)),
                    stats.get("worst_bed_deviation_strategy", "draw"),
                )
            )
        self.set_preview_build_progress(100, "Preview ready")
        estimate = self.update_estimate()
        if estimate:
            self.log.append(
                f"Loaded {len(self.moves)} preview moves from {len(self.program_lines)} exact G-code lines. "
                f"Calibrated controller-time estimate {self.format_duration(estimate['total_seconds'])} "
                f"from model {self.format_duration(estimate['model_total_seconds'])} "
                f"at motion scale {fmt(estimate['motion_estimate_scale'])}."
            )
        else:
            self.log.append(f"Loaded {len(self.moves)} preview moves from {len(self.program_lines)} exact G-code lines.")
        size_summary = self.size_summary()
        if size_summary:
            self.log.append(f"Pen compensation: {size_summary}.")
        reach_summary = self.reach_summary()
        if reach_summary:
            self.log.append(reach_summary)
        self.update_clip_warning()
        self.status.setText(f"Preview ready: {len(self.moves)} commands. {reach_summary}")

    def preview_failed(self, message):
        self.preview_build_bar.setValue(0)
        self.preview_stage.setProperty("stage", "Preview failed")
        self.update_preview_elapsed()
        self.status.setText("Preview failed.")
        QMessageBox.critical(self, "Preview failed", message)

    def preview_cancelled(self):
        self.preview_build_bar.setValue(0)
        self.preview_build_bar.setFormat("Cancelled")
        self.preview_stage.setProperty("stage", "Preview cancelled")
        self.update_preview_elapsed()
        self.status.setText("Preview cancelled. The previous preview was kept.")
        self.log.append("Preview generation cancelled.")

    def preview_thread_finished(self):
        self.preview_elapsed_timer.stop()
        self.update_preview_elapsed()
        self.preview_button.setEnabled(True)
        self.preview_button.setText("Preview")
        self.cancel_preview_button.setEnabled(False)
        self.save_action.setEnabled(True)
        self.preview_thread = None
        self.preview_worker = None

    def closeEvent(self, event):
        if self.preview_thread is not None:
            self.cancel_preview()
            self.status.setText("Cancelling preview. Close again after cancellation finishes.")
            event.ignore()
            return
        super().closeEvent(event)

    def convert(self):
        try:
            svg_path, source_tab = self.resolve_active_source()
        except Exception as exc:
            QMessageBox.warning(self, "Conversion needs artwork", str(exc))
            return
        if not self.gcode_path.text().strip():
            self.update_suggested_gcode_path(svg_path)
        gcode_path = self.gcode_path.text().strip()
        if not gcode_path:
            QMessageBox.warning(self, "Conversion needs an output path", "Choose where to save the G-code file.")
            return
        try:
            settings = self.settings_for_source(source_tab)
            contours_data = self.load_contours(svg_path, settings, notice=self.log.append)
            gcode = converter.contours_to_gcode(contours_data, settings)
            with open(gcode_path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(gcode)
            contours, lines = len(contours_data), len(gcode.splitlines())
        except Exception as exc:
            QMessageBox.critical(self, "Conversion failed", str(exc))
            return
        self.log.append(f"Saved {lines} G-code lines from {contours} contours: {gcode_path}")

    def set_index(self, index):
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
        self.update_status()

    def update_status(self):
        if not self.moves:
            return
        if self.preview_progress >= len(self.moves):
            move = self.moves[-1]
        else:
            move = self.moves[min(max(int(math.floor(self.preview_progress)), 0), len(self.moves) - 1)]
        theta, motor = self.gl_preview.active_theta()
        point = self.gl_preview.tool_point_at_progress(self.preview_progress) or move.get("end", (0, 0))
        strategy = move.get("strategy", "")
        strategy_text = f" | {strategy}" if strategy else ""
        self.status.setText(f"move {fmt(self.preview_progress)}/{len(self.moves)} {move.get('type')}{strategy_text} | X {fmt(point[0])} Y {fmt(point[1])} | bed theta {fmt(theta)} deg | A motor {fmt(motor)} deg")

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
            self.set_index(self.preview_progress)

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
        self.set_index(progress)
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
