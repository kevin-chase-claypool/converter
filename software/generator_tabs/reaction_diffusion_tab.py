"""Reaction-Diffusion generator tab.

Independent implementation of the Gray-Scott model (Pearson's parameter space)
with a nine-point Laplacian and contour extraction through the shared marching
squares. Each contour level becomes plotter paths, so the organic pattern is
drawn as clean lines rather than a raster.
"""

from __future__ import annotations

import random

from ._raster import marching_squares
from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Reaction-Diffusion"
ORDER = 180


def _simulate(grid, steps, feed, kill, da, db):
    import numpy as np

    a = np.ones_like(grid)
    b = grid.copy()
    for _ in range(int(steps)):
        lap_a = (
            -a
            + 0.2 * (np.roll(a, 1, 0) + np.roll(a, -1, 0) + np.roll(a, 1, 1) + np.roll(a, -1, 1))
            + 0.05
            * (
                np.roll(np.roll(a, 1, 0), 1, 1)
                + np.roll(np.roll(a, 1, 0), -1, 1)
                + np.roll(np.roll(a, -1, 0), 1, 1)
                + np.roll(np.roll(a, -1, 0), -1, 1)
            )
        )
        lap_b = (
            -b
            + 0.2 * (np.roll(b, 1, 0) + np.roll(b, -1, 0) + np.roll(b, 1, 1) + np.roll(b, -1, 1))
            + 0.05
            * (
                np.roll(np.roll(b, 1, 0), 1, 1)
                + np.roll(np.roll(b, 1, 0), -1, 1)
                + np.roll(np.roll(b, -1, 0), 1, 1)
                + np.roll(np.roll(b, -1, 0), -1, 1)
            )
        )
        reaction = a * b * b
        a += (da * lap_a - reaction + feed * (1.0 - a))
        b += (db * lap_b + reaction - (kill + feed) * b)
    return a, b


def reaction_diffusion_polylines(
    width_mm=200.0,
    height_mm=200.0,
    grid=128,
    steps=4000,
    feed=0.037,
    kill=0.060,
    da=0.16,
    db=0.08,
    seeds=1,
    seed_size=8,
    level=0.20,
    levels=1,
    seed=7,
    margin_mm=6.0,
    scale_pct=100.0,
):
    """Run Gray-Scott and return contour polylines in page millimetres."""
    import numpy as np

    grid = max(32, min(200, int(grid)))
    steps = max(50, min(20_000, int(steps)))
    rng = random.Random(int(seed))
    b = np.zeros((grid, grid), dtype=float)
    seed_size = max(2, min(grid // 2, int(seed_size)))
    for index in range(max(1, int(seeds))):
        if int(seeds) == 1:
            row = col = grid // 2 - seed_size // 2
        else:
            row = rng.randrange(0, max(1, grid - seed_size))
            col = rng.randrange(0, max(1, grid - seed_size))
        b[row:row + seed_size, col:col + seed_size] = 1.0
    _a, b_field = _simulate(b, steps, feed, kill, da, db)

    level = max(0.02, min(0.8, float(level)))
    contours = []
    for index in range(max(1, min(5, int(levels)))):
        current = max(0.02, level - index * 0.05)
        contours.extend(marching_squares(b_field, current))
    if not contours:
        return []

    draw_w = max(5.0, width_mm - 2 * margin_mm)
    draw_h = max(5.0, height_mm - 2 * margin_mm)
    scale = min(draw_w / grid, draw_h / grid)
    offset_x = (width_mm - grid * scale) / 2.0
    offset_y = (height_mm - grid * scale) / 2.0
    polylines = [
        [(offset_x + x * scale, offset_y + y * scale) for x, y in contour]
        for contour in contours
    ]
    return scale_polylines(
        polylines, float(scale_pct) / 100.0, width_mm, height_mm
    )


class ReactionDiffusionTab(GeneratorTab):
    NAME = "reaction-diffusion"
    GROUP = "Algorithm only"
    DESCRIPTION = "Gray-Scott reaction-diffusion patterns as contour lines."

    def __init__(self, host):
        super().__init__(host)
        simulation = self.add_group("Simulation")
        self.grid = int_spin(128, 32, 200, 16)
        simulation.addRow("Grid", self.grid)
        self.steps = int_spin(4000, 200, 20_000, 200)
        simulation.addRow("Steps", self.steps)
        self.feed = double_spin(0.037, 0.010, 0.080, 0.001, 3)
        simulation.addRow("Feed (f)", self.feed)
        self.kill = double_spin(0.060, 0.030, 0.070, 0.001, 3)
        simulation.addRow("Kill (k)", self.kill)
        self.da = double_spin(0.16, 0.05, 0.30, 0.01, 2)
        simulation.addRow("Diffusion A", self.da)
        self.db = double_spin(0.08, 0.02, 0.12, 0.01, 2)
        simulation.addRow("Diffusion B", self.db)
        self.seeds = int_spin(1, 1, 25, 1)
        simulation.addRow("Seeds", self.seeds)
        self.seed_size = int_spin(8, 2, 40, 1)
        simulation.addRow("Seed size", self.seed_size)
        self.seed = int_spin(7, 0, 999_999)
        simulation.addRow("Seed", self.seed)

        contours = self.add_group("Contours")
        self.level = double_spin(0.20, 0.02, 0.80, 0.01, 2)
        contours.addRow("Level", self.level)
        self.levels = int_spin(1, 1, 5, 1)
        contours.addRow("Levels", self.levels)

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

    def build_svg(self):
        polylines = reaction_diffusion_polylines(
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            grid=self.grid.value(),
            steps=self.steps.value(),
            feed=self.feed.value(),
            kill=self.kill.value(),
            da=self.da.value(),
            db=self.db.value(),
            seeds=self.seeds.value(),
            seed_size=self.seed_size.value(),
            level=self.level.value(),
            levels=self.levels.value(),
            seed=self.seed.value(),
            margin_mm=self.margin.value(),
            scale_pct=self.scale_pct.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} reaction-diffusion contours.",
        )


def create_tab(host):
    return ReactionDiffusionTab(host)
