"""Pixel art generator tab.

Algorithm ported from the MIT-licensed vpype-pixelart
(https://github.com/abey79/vpype-pixelart). All three upstream modes are
implemented: ``big`` (a 5x5 square spiral per pixel), ``line`` (horizontal
runs of one colour, with overdraw), and ``snake`` (a connected path through
each colour's pixels, singletons drawn as ticks). The upstream tool creates
one layer per colour; this tab fuses the colours into one pen path, which is
the single-pen workflow of this app.
"""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel

from ._tab_common import (
    GeneratorTab,
    double_spin,
    int_spin,
    scale_polylines,
)


TITLE = "Pixel Art"
ORDER = 110

PIXEL_TRAJECTORY = (
    (0, 0),
    (0, 1),
    (-1, 1),
    (-1, -1),
    (1, -1),
    (1, 2),
    (-2, 2),
    (-2, -2),
    (2, -2),
    (2, 2),
)
PIXEL_OFFSET = 5
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _load_grid(image_path, max_pixels, alpha_threshold, ignore_white):
    import numpy as np
    from PIL import Image

    image = Image.open(image_path).convert("RGBA")
    scale = min(1.0, float(max_pixels) / max(image.size))
    if scale < 1.0:
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.NEAREST,
        )
    grid = np.asarray(image)
    threshold = max(0, min(255, int(alpha_threshold)))
    opaque = grid[:, :, 3] >= threshold
    if ignore_white:
        white = (
            (grid[:, :, 0] >= 250)
            & (grid[:, :, 1] >= 250)
            & (grid[:, :, 2] >= 250)
        )
        opaque = opaque & ~white
    return grid, opaque


def _colors_of(grid, opaque):
    return sorted(
        {
            (int(grid[y, x, 0]), int(grid[y, x, 1]), int(grid[y, x, 2]))
            for y, x in zip(*_nonzero(opaque))
        }
    )


def _nonzero(mask):
    import numpy as np

    rows, cols = np.nonzero(mask)
    return rows, cols


def _big_paths(grid, opaque, color, pitch):
    rows, cols = _nonzero(
        opaque
        & (grid[:, :, 0] == color[0])
        & (grid[:, :, 1] == color[1])
        & (grid[:, :, 2] == color[2])
    )
    paths = []
    for y, x in zip(rows, cols):
        paths.append(
            [
                (
                    (x * PIXEL_OFFSET + dx) * pitch,
                    (y * PIXEL_OFFSET + dy) * pitch,
                )
                for dx, dy in PIXEL_TRAJECTORY
            ]
        )
    return paths


def _line_paths(grid, opaque, color, pitch, overdraw):
    rows, cols = _nonzero(
        opaque
        & (grid[:, :, 0] == color[0])
        & (grid[:, :, 1] == color[1])
        & (grid[:, :, 2] == color[2])
    )
    by_row = {}
    for y, x in zip(rows, cols):
        by_row.setdefault(int(y), []).append(int(x))
    paths = []
    for y, columns in sorted(by_row.items()):
        columns.sort()
        start = columns[0]
        previous = columns[0]
        for x in columns[1:] + [None]:
            if x is None or x != previous + 1:
                paths.append(
                    [
                        ((start - overdraw) * pitch, y * pitch),
                        ((previous + overdraw) * pitch, y * pitch),
                    ]
                )
                if x is not None:
                    start = x
            previous = x if x is not None else previous
    return paths


def _snake_paths(grid, opaque, color, pitch):
    rows, cols = _nonzero(
        opaque
        & (grid[:, :, 0] == color[0])
        & (grid[:, :, 1] == color[1])
        & (grid[:, :, 2] == color[2])
    )
    pixels = {(int(x), int(y)) for y, x in zip(rows, cols)}
    lines = [[]]
    current = None
    direction = (1, 0)
    while pixels:
        if current is None:
            current = min(pixels, key=lambda p: (p[1], p[0]))
            while True:
                up = (current[0], current[1] - 1)
                left = (current[0] - 1, current[1])
                if up in pixels:
                    current = up
                elif left in pixels:
                    current = left
                else:
                    break
            pixels.remove(current)
            lines[-1].append(current)
            direction = (1, 0)
        candidate = (current[0] + direction[0], current[1] + direction[1])
        if candidate in pixels:
            current = candidate
            pixels.remove(candidate)
            lines[-1].append(current)
            continue
        moved = False
        for new_direction in DIRECTIONS:
            if new_direction == direction:
                continue
            candidate = (
                current[0] + new_direction[0],
                current[1] + new_direction[1],
            )
            if candidate in pixels:
                current = candidate
                direction = new_direction
                pixels.remove(candidate)
                lines[-1].append(current)
                moved = True
                break
        if not moved:
            lines.append([])
            current = None
    paths = []
    for line in lines:
        if len(line) == 1:
            x, y = line[0]
            paths.append(
                [
                    ((x - 0.1) * pitch, y * pitch),
                    ((x + 0.1) * pitch, y * pitch),
                ]
            )
        elif len(line) > 1:
            paths.append([(x * pitch, y * pitch) for x, y in line])
    return paths


def pixel_art_polylines(
    image_path,
    mode="big",
    pitch_mm=0.6,
    overdraw=0.1,
    max_pixels=96,
    alpha_threshold=128,
    ignore_white=True,
    width_mm=200.0,
    height_mm=200.0,
    scale_pct=100.0,
):
    """Return pixel-art paths in page millimetres."""
    grid, opaque = _load_grid(
        image_path, max_pixels, alpha_threshold, ignore_white
    )
    pitch = max(0.05, float(pitch_mm))
    paths = []
    if not opaque.any():
        return []
    for color in _colors_of(grid, opaque):
        if mode == "line":
            paths.extend(_line_paths(grid, opaque, color, pitch, overdraw))
        elif mode == "snake":
            paths.extend(_snake_paths(grid, opaque, color, pitch))
        else:
            paths.extend(_big_paths(grid, opaque, color, pitch))
    if not paths:
        return []
    xs = [x for path in paths for x, _y in path]
    ys = [y for path in paths for _x, y in path]
    centre_x = (max(xs) + min(xs)) / 2.0
    centre_y = (max(ys) + min(ys)) / 2.0
    page_x = width_mm / 2.0
    page_y = height_mm / 2.0
    paths = [
        [(page_x + x - centre_x, page_y + y - centre_y) for x, y in path]
        for path in paths
    ]
    return scale_polylines(
        paths, float(scale_pct) / 100.0, width_mm, height_mm
    )


class PixelArtTab(GeneratorTab):
    NAME = "pixel-art"
    GROUP = "Line art"
    DESCRIPTION = "Pixel-art paths in big, line, or snake mode."

    def __init__(self, host):
        super().__init__(host)
        image_group = self.add_group("Image")
        self.image_label = QLabel()
        self.image_label.setWordWrap(True)
        image_group.addRow("Artwork", self.image_label)
        self.ignore_white = QCheckBox("Ignore white pixels")
        self.ignore_white.setChecked(True)
        image_group.addRow("", self.ignore_white)
        self.alpha_threshold = int_spin(128, 1, 255, 1)
        image_group.addRow("Alpha threshold", self.alpha_threshold)

        pixels = self.add_group("Pixels")
        self.mode = QComboBox()
        self.mode.addItem("Big (5x5 spiral)", "big")
        self.mode.addItem("Line (runs)", "line")
        self.mode.addItem("Snake (connected)", "snake")
        pixels.addRow("Mode", self.mode)
        self.pitch = double_spin(0.6, 0.1, 3.0, 0.1, 2, " mm")
        pixels.addRow("Pixel pitch", self.pitch)
        self.overdraw = double_spin(0.1, 0.0, 0.5, 0.05, 2, " px")
        pixels.addRow("Overdraw (line)", self.overdraw)
        self.max_pixels = int_spin(96, 8, 256, 8)
        pixels.addRow("Max grid", self.max_pixels)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
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
        polylines = pixel_art_polylines(
            self._artwork,
            mode=self.mode.currentData(),
            pitch_mm=self.pitch.value(),
            overdraw=self.overdraw.value(),
            max_pixels=self.max_pixels.value(),
            alpha_threshold=self.alpha_threshold.value(),
            ignore_white=self.ignore_white.isChecked(),
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            scale_pct=self.scale_pct.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"{len(polylines)} pixel paths ({self.mode.currentText()}).",
        )


def create_tab(host):
    return PixelArtTab(host)
