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

    def __init__(self, host):
        super().__init__(host)
        curve = self.add_group("Curve")
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
        self.scale_pct = double_spin(100, 10, 200, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.finish_controls()

    def build_svg(self):
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
