"""Substitution system generator tab.

Algorithm re-implemented in Python from the MIT-licensed
piebro/substitution-system (https://github.com/piebro/substitution-system):
each colour in a small palette is given a random 2x2 replacement rule, the
grid starts at 2x2, and every iteration replaces each cell with its rule,
doubling the grid. Because the converter drives one pen, the pattern is drawn
as the boundaries between colours (or as one diagonal per cell).
"""

from __future__ import annotations

import random

from PySide6.QtWidgets import QComboBox

from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Substitution"
ORDER = 80


def substitution_grid(seed=7, palette=3, iterations=4):
    """Return the colour grid after *iterations* of 2x2 substitution."""
    rng = random.Random(int(seed))
    palette = max(2, min(6, int(palette)))
    rules = {
        colour: tuple(rng.randrange(palette) for _ in range(4))
        for colour in range(palette)
    }
    grid = [[rng.randrange(palette) for _ in range(2)] for _ in range(2)]
    for _ in range(max(0, min(7, int(iterations)))):
        grown = []
        for row in grid:
            top = []
            bottom = []
            for cell in row:
                first, second, third, fourth = rules[cell]
                top.extend((first, second))
                bottom.extend((third, fourth))
            grown.append(top)
            grown.append(bottom)
        grid = grown
    return grid


def substitution_polylines(
    width_mm=200.0,
    height_mm=200.0,
    seed=7,
    palette=3,
    iterations=4,
    style="outlines",
    margin_mm=6.0,
    scale_pct=100.0,
):
    """Return the substitution pattern as plotter polylines."""
    grid = substitution_grid(seed=seed, palette=palette, iterations=iterations)
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    if not rows or not cols:
        return []
    width_mm = max(20.0, float(width_mm))
    height_mm = max(20.0, float(height_mm))
    cell = min(
        (width_mm - 2 * margin_mm) / cols,
        (height_mm - 2 * margin_mm) / rows,
    )
    cell = max(0.5, cell)
    offset_x = (width_mm - cols * cell) / 2.0
    offset_y = (height_mm - rows * cell) / 2.0
    paths = []
    if style == "diagonals":
        for row in range(rows):
            for col in range(cols):
                x0 = offset_x + col * cell
                y0 = offset_y + row * cell
                if grid[row][col] % 2 == 0:
                    paths.append([(x0, y0), (x0 + cell, y0 + cell)])
                else:
                    paths.append([(x0 + cell, y0), (x0, y0 + cell)])
    else:
        for row in range(rows):
            for col in range(cols):
                x0 = offset_x + col * cell
                y0 = offset_y + row * cell
                if col + 1 < cols and grid[row][col] != grid[row][col + 1]:
                    paths.append([(x0 + cell, y0), (x0 + cell, y0 + cell)])
                if row + 1 < rows and grid[row][col] != grid[row + 1][col]:
                    paths.append([(x0, y0 + cell), (x0 + cell, y0 + cell)])
        paths.append(
            [
                (offset_x, offset_y),
                (offset_x + cols * cell, offset_y),
                (offset_x + cols * cell, offset_y + rows * cell),
                (offset_x, offset_y + rows * cell),
                (offset_x, offset_y),
            ]
        )
    return scale_polylines(
        paths, float(scale_pct) / 100.0, width_mm, height_mm
    )


class SubstitutionTab(GeneratorTab):
    NAME = "substitution"
    GROUP = "Algorithm only"
    DESCRIPTION = "2x2 colour-substitution patterns."

    def __init__(self, host):
        super().__init__(host)
        pattern = self.add_group("Pattern")
        self.seed = int_spin(7, 0, 999_999)
        pattern.addRow("Seed", self.seed)
        self.palette = int_spin(3, 2, 6)
        pattern.addRow("Colours", self.palette)
        self.iterations = int_spin(4, 1, 7)
        pattern.addRow("Iterations", self.iterations)
        self.style = QComboBox()
        self.style.addItem("Colour boundaries", "outlines")
        self.style.addItem("Cell diagonals", "diagonals")
        pattern.addRow("Style", self.style)

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
        polylines = substitution_polylines(
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            seed=self.seed.value(),
            palette=self.palette.value(),
            iterations=self.iterations.value(),
            style=self.style.currentData(),
            margin_mm=self.margin.value(),
            scale_pct=self.scale_pct.value(),
        )
        cells = 2 ** (self.iterations.value() + 1)
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{cells} x {cells} substitution grid, {len(polylines)} paths.",
        )


def create_tab(host):
    return SubstitutionTab(host)
