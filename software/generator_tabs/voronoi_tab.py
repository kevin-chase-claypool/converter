"""Voronoi generator tab.

Independent implementation of the classic bounded Voronoi diagram: each site's
cell starts as the page rectangle and is clipped by the perpendicular bisector
against every other site. Optional Lloyd relaxation evens the cells out; cell
boundaries are deduplicated into one pen path set. The r/plotterart Voronoi
artwork inspired the feature; no upstream code was copied.
"""

from __future__ import annotations

import random

from PySide6.QtWidgets import QComboBox

from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Voronoi"
ORDER = 140


def _clip_half_plane(polygon, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    mx = (ax + bx) / 2.0
    my = (ay + by) / 2.0
    if abs(dx) < 1e-12 and abs(dy) < 1e-12:
        return polygon

    def inside(point):
        return (point[0] - mx) * dx + (point[1] - my) * dy <= 1e-9

    result = []
    for index, current in enumerate(polygon):
        following = polygon[(index + 1) % len(polygon)]
        current_in = inside(current)
        following_in = inside(following)
        if current_in:
            result.append(current)
        if current_in != following_in:
            ex = following[0] - current[0]
            ey = following[1] - current[1]
            denominator = ex * dx + ey * dy
            if abs(denominator) > 1e-12:
                t = (
                    (mx - current[0]) * dx + (my - current[1]) * dy
                ) / denominator
                result.append(
                    (current[0] + ex * t, current[1] + ey * t)
                )
    return result


def _cell_polygon(site, sites, rectangle):
    polygon = list(rectangle)
    for other in sites:
        if other is site:
            continue
        polygon = _clip_half_plane(
            polygon, site[0], site[1], other[0], other[1]
        )
        if len(polygon) < 3:
            return []
    return polygon


def _centroid(polygon):
    area = 0.0
    cx = 0.0
    cy = 0.0
    for index, (x0, y0) in enumerate(polygon):
        x1, y1 = polygon[(index + 1) % len(polygon)]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if abs(area) < 1e-9:
        return None
    area *= 0.5
    return (cx / (6.0 * area), cy / (6.0 * area))


def voronoi_polylines(
    width_mm=200.0,
    height_mm=200.0,
    count=120,
    seed=7,
    relax=1,
    style="cells",
    dot_mm=0.6,
    margin_mm=6.0,
    scale_pct=100.0,
):
    """Return bounded Voronoi cells, sites, or both, in page millimetres."""
    rng = random.Random(int(seed))
    left = margin_mm
    top = margin_mm
    right = max(left + 5.0, width_mm - margin_mm)
    bottom = max(top + 5.0, height_mm - margin_mm)
    rectangle = [(left, top), (right, top), (right, bottom), (left, bottom)]
    count = max(3, min(400, int(count)))
    sites = [
        (rng.uniform(left, right), rng.uniform(top, bottom))
        for _ in range(count)
    ]
    cells = []
    for _ in range(max(0, min(4, int(relax)))):
        cells = [_cell_polygon(site, sites, rectangle) for site in sites]
        relaxed = []
        for polygon, site in zip(cells, sites):
            centroid = _centroid(polygon) if len(polygon) >= 3 else None
            relaxed.append(centroid or site)
        sites = relaxed
    cells = [_cell_polygon(site, sites, rectangle) for site in sites]

    paths = []
    if style in ("cells", "both"):
        edges = {}
        for polygon in cells:
            for index, first in enumerate(polygon):
                second = polygon[(index + 1) % len(polygon)]
                key = tuple(
                    sorted(
                        (
                            (round(first[0], 2), round(first[1], 2)),
                            (round(second[0], 2), round(second[1], 2)),
                        )
                    )
                )
                edges[key] = (first, second)
        paths.extend([list(edge) for edge in edges.values()])
    if style in ("sites", "both"):
        radius = max(0.05, float(dot_mm) / 2.0)
        for sx, sy in sites:
            paths.append(
                [
                    (sx - radius, sy - radius),
                    (sx + radius, sy - radius),
                    (sx + radius, sy + radius),
                    (sx - radius, sy + radius),
                    (sx - radius, sy - radius),
                ]
            )
    return scale_polylines(
        paths, float(scale_pct) / 100.0, width_mm, height_mm
    )


class VoronoiTab(GeneratorTab):
    NAME = "voronoi"
    GROUP = "Algorithm only"
    DESCRIPTION = "Bounded Voronoi cells with optional Lloyd relaxation."

    def __init__(self, host):
        super().__init__(host)
        cells = self.add_group("Cells")
        self.count = int_spin(120, 3, 400, 5)
        cells.addRow("Points", self.count)
        self.seed = int_spin(7, 0, 999_999)
        cells.addRow("Seed", self.seed)
        self.relax = int_spin(1, 0, 4, 1)
        cells.addRow("Lloyd relax", self.relax)
        self.style = QComboBox()
        self.style.addItem("Cell boundaries", "cells")
        self.style.addItem("Site dots", "sites")
        self.style.addItem("Both", "both")
        cells.addRow("Style", self.style)
        self.dot = double_spin(0.6, 0.2, 4.0, 0.2, 1, " mm")
        cells.addRow("Dot size", self.dot)

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
        polylines = voronoi_polylines(
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            count=self.count.value(),
            seed=self.seed.value(),
            relax=self.relax.value(),
            style=self.style.currentData(),
            dot_mm=self.dot.value(),
            margin_mm=self.margin.value(),
            scale_pct=self.scale_pct.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} Voronoi paths ({self.style.currentText()}).",
        )


def create_tab(host):
    return VoronoiTab(host)
