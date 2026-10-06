"""Hershey simplex single-stroke font: parser and text layout.

Format facts used here (from the Hershey font distribution notes): each line
is one glyph, line order maps to ASCII 32 upward, the first five characters are
the glyph number, the next three the vertex count, then one character each for
the left and right bearing, then coordinate pairs encoded as ``char - 'R'``.
The pair ``" R"`` marks a pen-up between paths. Glyph coordinates have their
baseline at value 9 and cap top at value -12, so SVG y is ``value - 9``.
"""

from __future__ import annotations

from pathlib import Path


FONT_PATH = Path(__file__).resolve().parent / "fonts" / "futural.jhf"
CAP_HEIGHT = 21.0
BASELINE_VALUE = 9.0


def _value(char):
    return ord(char) - ord("R")


def load_font(path=None):
    """Return ``{ascii_code: {"left", "right", "paths"}}``."""
    source = Path(path) if path else FONT_PATH
    glyphs = {}
    for index, line in enumerate(source.read_text(encoding="utf-8").splitlines()):
        if len(line) < 10:
            continue
        try:
            vertex_count = int(line[5:8])
        except ValueError:
            continue
        left = _value(line[8])
        right = _value(line[9])
        data = line[10:]
        paths = []
        current = []
        for vertex in range(max(0, vertex_count - 1)):
            pair = data[vertex * 2:vertex * 2 + 2]
            if len(pair) < 2:
                break
            if pair == " R":
                if current:
                    paths.append(current)
                    current = []
                continue
            current.append(
                (float(_value(pair[0])), float(_value(pair[1]) - BASELINE_VALUE))
            )
        if current:
            paths.append(current)
        glyphs[32 + index] = {"left": left, "right": right, "paths": paths}
    return glyphs


_FONT = None


def font():
    global _FONT
    if _FONT is None:
        _FONT = load_font()
    return _FONT


def text_polylines(
    text,
    origin_x,
    origin_y,
    size_mm,
    tracking_mm=0.0,
    line_spacing_pct=140.0,
    align="left",
):
    """Lay out text as stroke polylines.

    ``origin_x`` is the left, centre, or right edge of each line according to
    ``align``; ``origin_y`` is the first baseline.
    """
    glyphs = font()
    scale = max(0.01, float(size_mm)) / CAP_HEIGHT
    line_height = max(0.01, float(size_mm)) * max(
        10.0, float(line_spacing_pct)
    ) / 100.0
    lines = text.split("\n")
    polylines = []

    def line_width(line):
        width = 0.0
        for char in line:
            glyph = glyphs.get(ord(char)) or glyphs.get(ord("?"))
            if glyph:
                width += (glyph["right"] - glyph["left"]) * scale + tracking_mm
        return max(0.0, width - tracking_mm)

    for row, line in enumerate(lines):
        width = line_width(line)
        if align == "center":
            pen_x = origin_x - width / 2.0
        elif align == "right":
            pen_x = origin_x - width
        else:
            pen_x = origin_x
        baseline = origin_y + row * line_height
        for char in line:
            glyph = glyphs.get(ord(char))
            if glyph is None:
                glyph = glyphs.get(ord("?"))
            if glyph is None:
                continue
            for path in glyph["paths"]:
                polylines.append(
                    [
                        (
                            pen_x + (x - glyph["left"]) * scale,
                            baseline + y * scale,
                        )
                        for x, y in path
                    ]
                )
            pen_x += (glyph["right"] - glyph["left"]) * scale + tracking_mm
    return polylines
