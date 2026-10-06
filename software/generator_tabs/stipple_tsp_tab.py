"""Stipple and TSP-art generator tab.

Weighted density stippling: image darkness gives a sampling density, points
are placed by weighted sampling and relaxed with a k-means/Lloyd pass (the
same idea as weighted Voronoi stippling). The result can be drawn as dots, as
a single TSP-art line ordered by greedy nearest neighbour plus a 2-opt
improvement, or both.
"""

from __future__ import annotations

import math

from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel

from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Stipple / TSP"
ORDER = 170


def stipple_points(
    image_path,
    count=600,
    iterations=3,
    gamma=1.0,
    invert=False,
    seed=7,
    max_pixels=200,
):
    """Return stipple sites in image-grid coordinates."""
    import numpy as np
    from PIL import Image

    image = Image.open(image_path).convert("L")
    fit = min(1.0, float(max_pixels) / max(image.size))
    if fit < 1.0:
        image = image.resize(
            (max(8, int(image.width * fit)), max(8, int(image.height * fit))),
            Image.LANCZOS,
        )
    density = np.asarray(image, dtype=float) / 255.0
    density = density if invert else 1.0 - density
    density = np.power(density, max(0.05, float(gamma))) + 1e-3
    rows, cols = density.shape
    samples = np.stack(
        np.meshgrid(np.arange(cols), np.arange(rows)), axis=-1
    ).reshape(-1, 2).astype(float)
    weights = density.reshape(-1)
    weights /= weights.sum()
    rng = np.random.default_rng(int(seed))
    count = max(10, min(3000, int(count)))
    picks = rng.choice(len(samples), size=count, replace=True, p=weights)
    sites = samples[picks] + rng.uniform(-0.5, 0.5, (count, 2))
    for _ in range(max(0, min(10, int(iterations)))):
        totals = np.zeros_like(sites)
        mass = np.zeros(count)
        for start in range(0, len(samples), 5000):
            chunk = samples[start:start + 5000]
            chunk_weights = weights[start:start + 5000]
            distances = (
                (chunk[:, None, :] - sites[None, :, :]) ** 2
            ).sum(axis=-1)
            assignment = distances.argmin(axis=1)
            np.add.at(totals, assignment, chunk * chunk_weights[:, None])
            np.add.at(mass, assignment, chunk_weights)
        occupied = mass > 0
        sites[occupied] = totals[occupied] / mass[occupied, None]
    return sites


def tsp_order(points, passes=0):
    """Greedy nearest-neighbour order with optional open-path 2-opt passes."""
    import numpy as np

    sites = np.asarray(points, dtype=float)
    size = len(sites)
    if size < 3:
        return list(range(size))
    start = int(np.argmin(sites[:, 0] ** 2 + sites[:, 1] ** 2))
    unvisited = set(range(size))
    unvisited.discard(start)
    order = [start]
    current = start
    while unvisited:
        best = min(
            unvisited,
            key=lambda index: (
                (sites[index, 0] - sites[current, 0]) ** 2
                + (sites[index, 1] - sites[current, 1]) ** 2
            ),
        )
        order.append(best)
        unvisited.discard(best)
        current = best
    if passes <= 0:
        return order
    route = np.array(order)

    def distance(first, second):
        return np.hypot(
            sites[first, 0] - sites[second, 0],
            sites[first, 1] - sites[second, 1],
        )

    for _ in range(max(0, min(50, int(passes)))):
        improved = False
        for i in range(1, size - 2):
            a = route[i - 1]
            b = route[i]
            js = np.arange(i + 1, size - 1)
            c = route[js]
            d = route[js + 1]
            deltas = (
                distance(a, c) + distance(b, d)
                - distance(a, b) - distance(c, d)
            )
            best = int(deltas.argmin())
            if deltas[best] < -1e-9:
                route[i:js[best] + 1] = route[i:js[best] + 1][::-1]
                improved = True
        if not improved:
            break
    return route.tolist()


def _dot(centre_x, centre_y, radius, sides=8):
    return [
        (
            centre_x + radius * math.cos(2.0 * math.pi * index / sides),
            centre_y + radius * math.sin(2.0 * math.pi * index / sides),
        )
        for index in range(sides + 1)
    ]


def stipple_tsp_polylines(
    image_path,
    count=600,
    iterations=3,
    gamma=1.0,
    invert=False,
    seed=7,
    style="both",
    dot_mm=0.6,
    tsp_passes=5,
    width_mm=200.0,
    height_mm=200.0,
    margin_mm=6.0,
    scale_pct=100.0,
):
    """Return dots, a TSP-art line, or both, in page millimetres."""
    sites = stipple_points(
        image_path,
        count=count,
        iterations=iterations,
        gamma=gamma,
        invert=invert,
        seed=seed,
    )
    if not len(sites):
        return []
    draw_w = max(5.0, width_mm - 2 * margin_mm)
    draw_h = max(5.0, height_mm - 2 * margin_mm)
    import numpy as np

    xs = sites[:, 0]
    ys = sites[:, 1]
    span_x = max(1e-9, float(xs.max() - xs.min()))
    span_y = max(1e-9, float(ys.max() - ys.min()))
    scale = min(draw_w / span_x, draw_h / span_y)
    offset_x = (width_mm - span_x * scale) / 2.0 - xs.min() * scale
    offset_y = (height_mm - span_y * scale) / 2.0 - ys.min() * scale
    points = [
        (offset_x + float(x) * scale, offset_y + float(y) * scale)
        for x, y in sites
    ]
    paths = []
    if style in ("dots", "both"):
        radius = max(0.05, float(dot_mm) / 2.0)
        paths.extend(_dot(x, y, radius) for x, y in points)
    if style in ("tsp", "both"):
        order = tsp_order(points, passes=tsp_passes)
        paths.append([points[index] for index in order])
    return scale_polylines(
        paths, float(scale_pct) / 100.0, width_mm, height_mm
    )


class StippleTspTab(GeneratorTab):
    NAME = "stipple-tsp"
    GROUP = "Photo-based"
    DESCRIPTION = "Density stippling and route-optimized TSP art."

    def __init__(self, host):
        super().__init__(host)
        source = self.add_group("Source")
        self.image_label = QLabel()
        self.image_label.setWordWrap(True)
        source.addRow("Artwork", self.image_label)
        self.invert = QCheckBox("Invert tone")
        source.addRow("", self.invert)
        self.gamma = double_spin(1.0, 0.2, 3.0, 0.1, 2)
        source.addRow("Density gamma", self.gamma)

        stipple = self.add_group("Stipple")
        self.count = int_spin(600, 10, 3000, 25)
        stipple.addRow("Points", self.count)
        self.iterations = int_spin(3, 0, 10, 1)
        stipple.addRow("Lloyd passes", self.iterations)
        self.seed = int_spin(7, 0, 999_999)
        stipple.addRow("Seed", self.seed)
        self.style = QComboBox()
        self.style.addItem("Dots + TSP line", "both")
        self.style.addItem("Dots", "dots")
        self.style.addItem("TSP line", "tsp")
        stipple.addRow("Style", self.style)
        self.dot = double_spin(0.6, 0.2, 4.0, 0.2, 1, " mm")
        stipple.addRow("Dot size", self.dot)
        self.passes = int_spin(5, 0, 50, 1)
        stipple.addRow("2-opt passes", self.passes)

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

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_artwork()

    def _refresh_artwork(self):
        import os

        path = ""
        if self.host is not None and hasattr(self.host, "artwork_path"):
            path = self.host.artwork_path()
        self._artwork = path
        self.image_label.setText(
            os.path.basename(path) if path else "(use File > Open Artwork)"
        )

    def build_svg(self):
        self._refresh_artwork()
        if not self._artwork:
            raise ValueError("Open an image with File > Open Artwork first.")
        polylines = stipple_tsp_polylines(
            self._artwork,
            count=self.count.value(),
            iterations=self.iterations.value(),
            gamma=self.gamma.value(),
            invert=self.invert.isChecked(),
            seed=self.seed.value(),
            style=self.style.currentData(),
            dot_mm=self.dot.value(),
            tsp_passes=self.passes.value(),
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            margin_mm=self.margin.value(),
            scale_pct=self.scale_pct.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} paths ({self.style.currentText()}).",
        )


def create_tab(host):
    return StippleTspTab(host)
