"""Harmonograph generator tab.

Algorithm re-implemented in Python from the MIT-licensed
ttencate/harmonograph (https://github.com/ttencate/harmonograph): two
orthogonal oscillations decay over time, producing the damped Lissajous
figures known as harmonograph curves. The tab draws one or more curves as SVG.
"""

from __future__ import annotations

import math
import random

from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Harmonograph"
ORDER = 40


def harmonograph_pendulum_polylines(
    width_mm=200.0,
    height_mm=200.0,
    pivot_x_mm=900.0,
    pivot_y_mm=800.0,
    arm_x_mm=900.0,
    arm_y_mm=700.0,
    amplitude_x_deg=10.0,
    amplitude_y_deg=10.0,
    phase_x=0.0,
    phase_y=0.0,
    damping_x=0.001,
    damping_y=0.001,
    freq_x_hz=0.3,
    freq_y_hz=0.302,
    rotation_hz=0.0008,
    duration_s=300.0,
    samples=12_000,
    smooth_steps=0,
    size_pct=45.0,
    margin_mm=10.0,
    scale_pct=100.0,
):
    """Physical two-pendulum harmonograph, ported from ttencate/harmonograph.

    Upstream equations (harmonograph.js, updateXY):
    alpha = A sin(2*pi*(f t + u)) exp(-R t)
    beta  = B sin(2*pi*(g t + v)) exp(-S t)
    gamma = 2*pi*h*t
    xa = p cos(alpha) + q sin(alpha) - d
    ya = q cos(alpha) - p sin(alpha)
    xb = xa cos(beta) - ya sin(beta)
    yb = ya cos(beta) + xa sin(beta) - c
    x  = xb cos(gamma) - yb sin(gamma)
    y  = yb cos(gamma) + xb sin(gamma)
    """
    width_mm = max(20.0, float(width_mm))
    height_mm = max(20.0, float(height_mm))
    duration = max(1.0, float(duration_s))
    count = max(200, min(200_000, int(samples)))
    amp_x = math.radians(max(0.0, float(amplitude_x_deg)))
    amp_y = math.radians(max(0.0, float(amplitude_y_deg)))
    points = []
    for index in range(count):
        t = duration * index / (count - 1)
        alpha = (
            amp_x
            * math.sin(2.0 * math.pi * (freq_x_hz * t + phase_x))
            * math.exp(-damping_x * t)
        )
        beta = (
            amp_y
            * math.sin(2.0 * math.pi * (freq_y_hz * t + phase_y))
            * math.exp(-damping_y * t)
        )
        gamma = 2.0 * math.pi * rotation_hz * t
        xa = arm_x_mm * math.cos(alpha) + arm_y_mm * math.sin(alpha) - pivot_x_mm
        ya = arm_y_mm * math.cos(alpha) - arm_x_mm * math.sin(alpha)
        xb = xa * math.cos(beta) - ya * math.sin(beta)
        yb = ya * math.cos(beta) + xa * math.sin(beta) - pivot_y_mm
        x = xb * math.cos(gamma) - yb * math.sin(gamma)
        y = yb * math.cos(gamma) + xb * math.sin(gamma)
        points.append((x, y))
    if smooth_steps > 0 and len(points) > 3:
        for _ in range(max(0, min(4, int(smooth_steps)))):
            smoothed = [points[0]]
            for first, second in zip(points, points[1:]):
                smoothed.append(
                    (
                        0.75 * first[0] + 0.25 * second[0],
                        0.75 * first[1] + 0.25 * second[1],
                    )
                )
                smoothed.append(
                    (
                        0.25 * first[0] + 0.75 * second[0],
                        0.25 * first[1] + 0.75 * second[1],
                    )
                )
            smoothed.append(points[-1])
            points = smoothed
    xs = [x for x, _y in points]
    ys = [y for _x, y in points]
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
    scale *= max(0.05, min(1.0, float(size_pct) / 100.0))
    centre_x = (max(xs) + min(xs)) / 2.0
    centre_y = (max(ys) + min(ys)) / 2.0
    page_x = width_mm / 2.0
    page_y = height_mm / 2.0
    polylines = [
        [
            (page_x + (x - centre_x) * scale, page_y + (y - centre_y) * scale)
            for x, y in points
        ]
    ]
    return scale_polylines(
        polylines, float(scale_pct) / 100.0, width_mm, height_mm
    )


def harmonograph_polylines(
    width_mm=200.0,
    height_mm=200.0,
    seed=7,
    freq_x=3.0,
    freq_y=2.0,
    phase_deg=30.0,
    damping=0.008,
    turns=60.0,
    samples=6000,
    curves=2,
    size_pct=45.0,
    margin_mm=10.0,
    scale_pct=100.0,
):
    """Return harmonograph curves in page millimetres."""
    width_mm = max(20.0, float(width_mm))
    height_mm = max(20.0, float(height_mm))
    amplitude = (min(width_mm, height_mm) / 2.0 - margin_mm) * max(
        0.05, min(1.0, float(size_pct) / 100.0)
    )
    amplitude = max(1.0, amplitude)
    centre_x = width_mm / 2.0
    centre_y = height_mm / 2.0
    turns = max(1.0, float(turns))
    count = max(200, min(40_000, int(samples)))
    rng = random.Random(int(seed))
    polylines = []
    for curve in range(max(1, min(4, int(curves)))):
        phase = math.radians(
            phase_deg + curve * 23.0 + rng.uniform(-3.0, 3.0)
        )
        omega_x = 2.0 * math.pi * (freq_x + curve * 0.017)
        omega_y = 2.0 * math.pi * (freq_y + curve * 0.013)
        decay = max(0.0, float(damping))
        points = []
        for index in range(count):
            t = turns * index / (count - 1)
            envelope = math.exp(-decay * t)
            x = centre_x + amplitude * envelope * math.sin(omega_x * t + phase)
            y = centre_y + amplitude * envelope * math.sin(omega_y * t)
            points.append((x, y))
        polylines.append(points)
    return scale_polylines(
        polylines, float(scale_pct) / 100.0, width_mm, height_mm
    )


class HarmonographTab(GeneratorTab):
    NAME = "harmonograph"
    GROUP = "Patterns"
    DESCRIPTION = "Physical pendulum-harmonograph or simple Lissajous."

    def __init__(self, host):
        super().__init__(host)
        from PySide6.QtWidgets import QComboBox

        model = self.add_group("Model")
        self.model = QComboBox()
        self.model.addItem("Pendulum + rotating disk (upstream)", "physical")
        self.model.addItem("Simple damped Lissajous", "simple")
        model.addRow("Model", self.model)
        self.model.currentIndexChanged.connect(self._sync_model)

        geometry = self.add_group("Pendulum geometry")
        self.pivot_x = double_spin(900, 100, 2000, 10, 0, " mm")
        geometry.addRow("Pivot X (d)", self.pivot_x)
        self.pivot_y = double_spin(800, 100, 2000, 10, 0, " mm")
        geometry.addRow("Pivot Y (c)", self.pivot_y)
        self.arm_x = double_spin(900, 100, 2000, 10, 0, " mm")
        geometry.addRow("Arm X (p)", self.arm_x)
        self.arm_y = double_spin(700, 100, 2000, 10, 0, " mm")
        geometry.addRow("Arm Y (q)", self.arm_y)
        self.rotation_hz = double_spin(0.0008, 0.0, 0.05, 0.0002, 4)
        geometry.addRow("Rotating disk (h)", self.rotation_hz)
        self._physical_groups = [geometry]

        motion = self.add_group("Pendulum motion")
        self.amplitude_x = double_spin(10, 0, 45, 1, 0, " deg")
        motion.addRow("Amplitude X (A)", self.amplitude_x)
        self.amplitude_y = double_spin(10, 0, 45, 1, 0, " deg")
        motion.addRow("Amplitude Y (B)", self.amplitude_y)
        self.phase_x = double_spin(0.0, 0.0, 1.0, 0.05, 2)
        motion.addRow("Phase X (u)", self.phase_x)
        self.phase_y = double_spin(0.0, 0.0, 1.0, 0.05, 2)
        motion.addRow("Phase Y (v)", self.phase_y)
        self.damping_x = double_spin(0.001, 0.0, 0.05, 0.0005, 4)
        motion.addRow("Damping X (R)", self.damping_x)
        self.damping_y = double_spin(0.001, 0.0, 0.05, 0.0005, 4)
        motion.addRow("Damping Y (S)", self.damping_y)
        self.freq_x_hz = double_spin(0.300, 0.05, 2.0, 0.002, 3, " Hz")
        motion.addRow("Frequency X (f)", self.freq_x_hz)
        self.freq_y_hz = double_spin(0.302, 0.05, 2.0, 0.002, 3, " Hz")
        motion.addRow("Frequency Y (g)", self.freq_y_hz)
        self.duration = double_spin(300, 5, 3600, 10, 0, " s")
        motion.addRow("Duration", self.duration)
        self.physical_samples = int_spin(12_000, 500, 200_000, 500)
        motion.addRow("Samples", self.physical_samples)
        self.smooth_steps = int_spin(0, 0, 4, 1)
        motion.addRow("Bezier smoothing", self.smooth_steps)
        self._physical_groups.append(motion)

        curve = self.add_group("Simple curve")
        self._simple_group = curve
        self.seed = int_spin(7, 0, 999_999)
        curve.addRow("Seed", self.seed)
        self.freq_x = double_spin(3.0, 0.5, 12.0, 0.1, 2)
        curve.addRow("Frequency X", self.freq_x)
        self.freq_y = double_spin(2.0, 0.5, 12.0, 0.1, 2)
        curve.addRow("Frequency Y", self.freq_y)
        self.phase = double_spin(30, 0, 180, 5, 0, " deg")
        curve.addRow("Phase", self.phase)
        self.damping = double_spin(0.008, 0.0, 0.05, 0.001, 3)
        curve.addRow("Damping", self.damping)
        self.turns = double_spin(60, 5, 200, 5, 0)
        curve.addRow("Turns", self.turns)
        self.samples = int_spin(6000, 500, 20_000, 500)
        curve.addRow("Samples", self.samples)
        self.curves = int_spin(2, 1, 4)
        curve.addRow("Curves", self.curves)

        page = self.add_group("Page")
        self.size_pct = double_spin(45, 5, 100, 5, 0, " %")
        page.addRow("Curve size", self.size_pct)
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(10, 0, 60, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.line_width = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        page.addRow("Line width", self.line_width)
        self.scale_pct = double_spin(100, 10, 1000, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.finish_controls()
        self._sync_model()

    def _sync_model(self):
        physical = self.model.currentData() == "physical"
        for group in self._physical_groups:
            group.parentWidget().setVisible(physical)
        self._simple_group.parentWidget().setVisible(not physical)
        # `add_group` returns the form; its parent widget is the group box.

    def build_svg(self):
        if self.model.currentData() == "physical":
            polylines = harmonograph_pendulum_polylines(
                width_mm=self.page_w.value(),
                height_mm=self.page_h.value(),
                pivot_x_mm=self.pivot_x.value(),
                pivot_y_mm=self.pivot_y.value(),
                arm_x_mm=self.arm_x.value(),
                arm_y_mm=self.arm_y.value(),
                amplitude_x_deg=self.amplitude_x.value(),
                amplitude_y_deg=self.amplitude_y.value(),
                phase_x=self.phase_x.value(),
                phase_y=self.phase_y.value(),
                damping_x=self.damping_x.value(),
                damping_y=self.damping_y.value(),
                freq_x_hz=self.freq_x_hz.value(),
                freq_y_hz=self.freq_y_hz.value(),
                rotation_hz=self.rotation_hz.value(),
                duration_s=self.duration.value(),
                samples=self.physical_samples.value(),
                smooth_steps=self.smooth_steps.value(),
                size_pct=self.size_pct.value(),
                margin_mm=self.margin.value(),
                scale_pct=self.scale_pct.value(),
            )
        else:
            polylines = harmonograph_polylines(
                width_mm=self.page_w.value(),
                height_mm=self.page_h.value(),
                seed=self.seed.value(),
                freq_x=self.freq_x.value(),
                freq_y=self.freq_y.value(),
                phase_deg=self.phase.value(),
                damping=self.damping.value(),
                turns=self.turns.value(),
                samples=self.samples.value(),
                curves=self.curves.value(),
                size_pct=self.size_pct.value(),
                margin_mm=self.margin.value(),
                scale_pct=self.scale_pct.value(),
            )
        points = sum(len(line) for line in polylines)
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} harmonograph curves, {points} points.",
        )


def create_tab(host):
    return HarmonographTab(host)
