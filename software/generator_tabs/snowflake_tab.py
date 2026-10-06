"""Snowflake generator tab.

Independent dendritic snowflake generator, inspired by the snowflake art
shared from the MIT-licensed vishnubob/snowflake project
(https://github.com/vishnubob/snowflake). Repeated arms grow from the centre
with side branches at a fixed angle, scaled and jittered per level, producing
a radial snowflake of straight segments. The upstream project is a mesoscopic
lattice-growth simulation of ice crystals; this tab is a simpler branch
generator, not that model. Output is SVG.
"""

from __future__ import annotations

import math
import random

from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Snowflake"
ORDER = 50


def snowflake_polylines(
    width_mm=200.0,
    height_mm=200.0,
    seed=7,
    arms=6,
    depth=3,
    length_pct=45.0,
    branch_angle_deg=35.0,
    branch_scale_pct=55.0,
    jitter_angle_deg=8.0,
    jitter_length_pct=15.0,
    margin_mm=8.0,
    scale_pct=100.0,
):
    """Return snowflake branch segments in page millimetres."""
    width_mm = max(20.0, float(width_mm))
    height_mm = max(20.0, float(height_mm))
    radius = (min(width_mm, height_mm) / 2.0 - margin_mm) * max(
        0.05, min(1.0, float(length_pct) / 100.0)
    )
    radius = max(2.0, radius)
    centre_x = width_mm / 2.0
    centre_y = height_mm / 2.0
    rng = random.Random(int(seed))
    level = max(0, min(5, int(depth)))
    angle = math.radians(max(5.0, min(85.0, float(branch_angle_deg))))
    scale = max(0.2, min(0.85, float(branch_scale_pct) / 100.0))
    jitter_angle = math.radians(max(0.0, float(jitter_angle_deg)))
    jitter_length = max(0.0, float(jitter_length_pct) / 100.0)
    polylines = []

    def grow(x, y, heading, length, remaining):
        tip_x = x + math.cos(heading) * length
        tip_y = y + math.sin(heading) * length
        polylines.append([(x, y), (tip_x, tip_y)])
        if remaining <= 0:
            return
        for side in (-1.0, 1.0):
            branch_angle = heading + side * (
                angle + rng.uniform(-jitter_angle, jitter_angle)
            )
            branch_length = length * scale * (
                1.0 + rng.uniform(-jitter_length, jitter_length)
            )
            grow(tip_x, tip_y, branch_angle, branch_length, remaining - 1)

    for arm in range(max(3, min(12, int(arms)))):
        heading = 2.0 * math.pi * arm / max(3, int(arms))
        heading += rng.uniform(-jitter_angle, jitter_angle)
        grow(centre_x, centre_y, heading, radius, level)
    return scale_polylines(
        polylines, float(scale_pct) / 100.0, width_mm, height_mm
    )


class SnowflakeTab(GeneratorTab):
    NAME = "snowflake"
    GROUP = "Algorithm only"
    DESCRIPTION = "Radial branch snowflakes."

    def __init__(self, host):
        super().__init__(host)
        shape = self.add_group("Shape")
        self.seed = int_spin(7, 0, 999_999)
        shape.addRow("Seed", self.seed)
        self.arms = int_spin(6, 3, 12)
        shape.addRow("Arms", self.arms)
        self.depth = int_spin(3, 1, 5)
        shape.addRow("Branch depth", self.depth)
        self.length_pct = double_spin(45, 10, 100, 5, 0, " %")
        shape.addRow("Arm length", self.length_pct)
        self.branch_angle = double_spin(35, 10, 80, 5, 0, " deg")
        shape.addRow("Branch angle", self.branch_angle)
        self.branch_scale = double_spin(55, 30, 80, 5, 0, " %")
        shape.addRow("Branch scale", self.branch_scale)
        self.jitter_angle = double_spin(8, 0, 25, 1, 0, " deg")
        shape.addRow("Angle jitter", self.jitter_angle)
        self.jitter_length = double_spin(15, 0, 40, 5, 0, " %")
        shape.addRow("Length jitter", self.jitter_length)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(8, 0, 60, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.line_width = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        page.addRow("Line width", self.line_width)
        self.scale_pct = double_spin(100, 10, 1000, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.finish_controls()

    def build_svg(self):
        polylines = snowflake_polylines(
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            seed=self.seed.value(),
            arms=self.arms.value(),
            depth=self.depth.value(),
            length_pct=self.length_pct.value(),
            branch_angle_deg=self.branch_angle.value(),
            branch_scale_pct=self.branch_scale.value(),
            jitter_angle_deg=self.jitter_angle.value(),
            jitter_length_pct=self.jitter_length.value(),
            margin_mm=self.margin.value(),
            scale_pct=self.scale_pct.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} snowflake branches.",
        )


def create_tab(host):
    return SnowflakeTab(host)
