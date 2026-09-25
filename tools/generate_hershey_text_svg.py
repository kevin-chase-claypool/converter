#!/usr/bin/env python3
"""Render text as single-centerline (single-stroke) SVG paths using the
Hershey vector fonts, suitable for the Theta pen plotter.

The Hershey fonts are stroke-based, not outline-based, so each glyph is a set
of pen strokes instead of a closed outline. This is exactly what a pen plotter
needs for single-pass "handwriting" that does not re-trace letter edges.
"""

import argparse
from pathlib import Path

from HersheyFonts import HersheyFonts


def format_number(value):
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text if text not in ("", "-") else "0"


def stroke_to_path_d(stroke):
    coords = [f"{format_number(x)},{format_number(y)}" for x, y in stroke]
    return "M" + " L".join(coords)


def wrap_text(hf, text, max_width):
    words = text.split()
    lines = []
    current = []
    for word in words:
        trial = " ".join(current + [word])
        width = measure_width(hf, trial)
        if current and width > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def measure_width(hf, text):
    strokes = list(hf.strokes_for_text(text))
    if not strokes:
        return 0.0
    xs = [point[0] for stroke in strokes for point in stroke]
    return max(xs) - min(xs)


def render_svg(text, font, text_height, line_spacing, max_width, out_path):
    hf = HersheyFonts()
    hf.load_default_font(font)
    hf.normalize_rendering(text_height)
    hf.render_options.spacing = text_height * 0.08

    lines = wrap_text(hf, text, max_width)

    paths = []
    for line_index, line in enumerate(lines):
        top_y = line_index * line_spacing
        for stroke in hf.strokes_for_text(line):
            # normalize_rendering returns y increasing upward (bottom=0,
            # top=text_height). Convert to standard SVG y-down so the text is
            # upright and lines advance downward.
            points = [(x, top_y + (text_height - y)) for x, y in stroke]
            paths.append(stroke_to_path_d(points))

    width = max(measure_width(hf, line) for line in lines) if lines else 0.0
    height = (len(lines) - 1) * line_spacing + text_height if lines else 0.0

    path_elements = "\n".join(
        f'  <path d="{d}" fill="none" stroke="#000000" stroke-width="0.3" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        for d in paths
    )
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{format_number(width)}mm" '
        f'height="{format_number(height)}mm" viewBox="0 0 {format_number(width)} '
        f'{format_number(height)}">\n'
        f"{path_elements}\n"
        "</svg>\n"
    )
    Path(out_path).write_text(svg, encoding="utf-8")
    return len(lines), len(paths), width, height


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="Text to render (use a file path starting with @ to read from a file)")
    parser.add_argument("--font", default="scripts", help="Hershey font name (default scripts)")
    parser.add_argument("--height", type=float, default=12.0, help="Cap-to-bottom text height in mm")
    parser.add_argument("--spacing", type=float, default=1.4, help="Line spacing as a multiple of text height")
    parser.add_argument("--width", type=float, default=380.0, help="Maximum line width in mm")
    parser.add_argument("--out", required=True, help="Output SVG path")
    args = parser.parse_args()

    text = args.text
    if text.startswith("@"):
        text = Path(text[1:]).read_text(encoding="utf-8")

    lines, strokes, width, height = render_svg(
        text,
        args.font,
        args.height,
        args.height * args.spacing,
        args.width,
        args.out,
    )
    print(f"wrote {args.out}: {lines} lines, {strokes} strokes, {width:.1f} x {height:.1f} mm")


if __name__ == "__main__":
    main()
