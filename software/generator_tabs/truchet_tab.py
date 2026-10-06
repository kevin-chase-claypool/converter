"""Truchet tile generator tab.

Classic Truchet tiles: a square grid where each tile is one of two rotations
of a pair of quarter-circle arcs (or one of two diagonals), so the tiles meet
at their edge midpoints and form a continuous wandering pattern. Implemented
from the public-domain tile concept; the unlicensed r/plotterart Truchet
repositories were not used.
"""

from __future__ import annotations

import math
import random

from PySide6.QtWidgets import QComboBox

from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Truchet"
ORDER = 60


def _quarter_arc(centre_x, centre_y, radius, start_deg, steps):
    points = []
    for index in range(steps + 1):
        angle = math.radians(start_deg + 90.0 * index / steps)
        points.append(
            (
                centre_x + radius * math.cos(angle),
                centre_y + radius * math.sin(angle),
            )
        )
    return points


def truchet_polylines(
    width_mm=200.0,
    height_mm=200.0,
    seed=7,
    tile_mm=12.0,
    style="arcs",
    arc_steps=10,
    margin_mm=6.0,
    scale_pct=100.0,
):
    """Return Truchet tile paths in page millimetres."""
    width_mm = max(20.0, float(width_mm))
    height_mm = max(20.0, float(height_mm))
    tile = max(3.0, float(tile_mm))
    margin = max(0.0, min(float(margin_mm), min(width_mm, height_mm) / 2.0 - 1.0))
    cols = max(1, int((width_mm - 2 * margin) // tile))
    rows = max(1, int((height_mm - 2 * margin) // tile))
    offset_x = (width_mm - cols * tile) / 2.0
    offset_y = (height_mm - rows * tile) / 2.0
    rng = random.Random(int(seed))
    steps = max(3, min(40, int(arc_steps)))
    polylines = []
    for row in range(rows):
        for col in range(cols):
            x0 = offset_x + col * tile
            y0 = offset_y + row * tile
            use_arc = style == "arcs" or (
                style == "mixed" and rng.random() < 0.7
            )
            if use_arc:
                corners = (
                    (x0, y0, 0.0),
                    (x0 + tile, y0, 90.0),
                    (x0 + tile, y0 + tile, 180.0),
                    (x0, y0 + tile, 270.0),
                )
                first = rng.randrange(4)
                second = (first + 2) % 4
                for index in (first, second):
                    centre_x, centre_y, start = corners[index]
                    polylines.append(
                        _quarter_arc(
                            centre_x, centre_y, tile / 2.0, start, steps
                        )
                    )
            elif rng.randrange(2) == 0:
                polylines.append([(x0, y0), (x0 + tile, y0 + tile)])
            else:
                polylines.append([(x0 + tile, y0), (x0, y0 + tile)])
    return scale_polylines(
        polylines, float(scale_pct) / 100.0, width_mm, height_mm
    )


class TruchetTab(GeneratorTab):
    NAME = "truchet"

    def __init__(self, host):
        super().__init__(host)
        tiles = self.add_group("Tiles")
        self.seed = int_spin(7, 0, 999_999)
        tiles.addRow("Seed", self.seed)
        self.tile = double_spin(12.0, 3.0, 60.0, 1.0, 2, " mm")
        tiles.addRow("Tile size", self.tile)
        self.style = QComboBox()
        self.style.addItem("Quarter arcs", "arcs")
        self.style.addItem("Diagonals", "diagonal")
        self.style.addItem("Mixed", "mixed")
        tiles.addRow("Style", self.style)
        self.arc_steps = int_spin(10, 3, 40, 1)
        tiles.addRow("Arc segments", self.arc_steps)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(6, 0, 60, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.line_width = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        page.addRow("Line width", self.line_width)
        self.scale_pct = double_spin(100, 10, 200, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.finish_controls()

    def build_svg(self):
        polylines = truchet_polylines(
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            seed=self.seed.value(),
            tile_mm=self.tile.value(),
            style=self.style.currentData(),
            arc_steps=self.arc_steps.value(),
            margin_mm=self.margin.value(),
            scale_pct=self.scale_pct.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} Truchet tile paths.",
        )


def create_tab(host):
    return TruchetTab(host)
