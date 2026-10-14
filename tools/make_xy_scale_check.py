"""Generate the X/Y machine-scale check sheet.

Every diagnostic so far has assumed that a commanded X/Y millimetre is a
real millimetre on the paper. This sheet tests that assumption directly and
needs no electronics: the program contains no A words at all, so the bed
holds its angle and the drawing isolates the X/Y steps-per-mm and the axis
squareness from the rotation drivetrain.

The sheet is drawn around G54 X0 Y0 (the registered bed centre):

  * an X ruler - 200 mm along machine X with ticks every 50 mm (at Y = -80);
  * a Y ruler - the same 200 mm along machine Y (at X = -80);
  * a 120 mm square in the +X/+Y quadrant, upper-right corner on the
    (+100, +100) corner of the sheet.

Measure with a steel rule:

  * the 50 mm intervals and the 200 mm end-to-end distance on both rulers;
  * the square's four sides (120.000 mm) and both diagonals (169.706 mm).
    Unequal diagonals mean X/Y skew or a scale difference between the axes.
  * an interval that is long/short by the same fraction everywhere means
    `$100` (X) or `$101` (Y) steps-per-mm is off by that fraction: new
    steps/mm = old x drawn / commanded.

Needs at least a 205 x 205 mm sheet; 8.5x11 in portrait fits with about an
8 mm margin per side, so centre the paper on the bed centre.

Usage:
    python tools\\make_xy_scale_check.py
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "samples" / "gcode" / "xy-scale-check.gcode"


def fmt(v: float) -> str:
    return ("%.4f" % v).rstrip("0").rstrip(".")


def tick_positions(span: float, spacing: float) -> list[float]:
    half = span / 2.0
    count = int(math.floor(half / spacing))
    marks = [k * spacing for k in range(-count, count + 1)]
    if not math.isclose(marks[0], -half, abs_tol=1e-9):
        marks.insert(0, -half)
    if not math.isclose(marks[-1], half, abs_tol=1e-9):
        marks.append(half)
    return marks


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUTPUT))
    ap.add_argument("--span", type=float, default=200.0, help="ruler length, mm")
    ap.add_argument("--tick", type=float, default=50.0, help="ruler tick spacing, mm")
    ap.add_argument("--square", type=float, default=120.0, help="square side, mm (0 skips it)")
    ap.add_argument("--feed", type=float, default=350.0, help="drawing feed, mm/min")
    args = ap.parse_args()

    span = float(args.span)
    spacing = float(args.tick)
    side = float(args.square)
    feed = float(args.feed)
    half = span / 2.0
    ruler_offset = -0.4 * span
    ticks = tick_positions(span, spacing)
    end_half, mid_half = 12.0, 8.0

    lines: list[str] = []
    lines.append("(X/Y machine-scale check sheet - make_xy_scale_check.py)")
    lines.append("(+X = east, +Y = north on the bed; drawn around G54 X0 Y0)")
    lines.append("(no A words: the bed must stay parked for the whole sheet)")
    lines.append("(X ruler along machine X at Y%s: marks every %s mm, ends at +/-%s)"
                 % (fmt(ruler_offset), fmt(spacing), fmt(half)))
    lines.append("(Y ruler along machine Y at X%s: same span and marks)"
                 % fmt(ruler_offset))
    if side > 0:
        lines.append("(square %s mm in the +X/+Y quadrant; diagonals %s mm)"
                     % (fmt(side), fmt(side * math.sqrt(2.0))))
    lines.append("(drag a steel rule over each interval: equal numbers = scale correct)")
    lines.extend(["G21", "G90", "G94", "G17", "G54", "G0 F3000", "M5",
                  "G65 P115 Q0 A1 W2"])

    first_down = True
    drawing_mm = 0.0
    pen_cycles = 0

    def pen_down() -> None:
        nonlocal first_down, pen_cycles
        lines.append("M3")
        lines.append("G65 P115 Q1 B12 A1 W2" if first_down else "G65 P115 Q1 A1 W2")
        lines.append("G1 F%s" % fmt(feed))
        first_down = False
        pen_cycles += 1

    def pen_up() -> None:
        lines.append("M5")
        lines.append("G65 P115 Q1 A1 W2")

    def move(x: float, y: float, drawing: bool) -> None:
        nonlocal drawing_mm
        lines.append("G1 X%s Y%s F%s" % (fmt(x), fmt(y), fmt(feed)))
        if drawing:
            drawing_mm += math.hypot(x - last[0], y - last[1])

    last = [0.0, 0.0]

    def draw_path(points: list[tuple[float, float]]) -> None:
        """Rapid to the first point, then draw through the rest in one stroke."""
        x0, y0 = points[0]
        lines.append("G0 X%s Y%s" % (fmt(x0), fmt(y0)))
        last[0], last[1] = x0, y0
        pen_down()
        for x, y in points[1:]:
            move(x, y, True)
            last[0], last[1] = x, y
        pen_up()

    # X ruler: one long stroke, then a tick across it at every mark.
    lines.append("(X ruler: -%s to +%s at Y%s)" % (fmt(half), fmt(half), fmt(ruler_offset)))
    draw_path([(-half, ruler_offset), (half, ruler_offset)])
    for x in ticks:
        h = end_half if abs(abs(x) - half) < 1e-9 else mid_half
        draw_path([(x, ruler_offset - h), (x, ruler_offset + h)])

    # Square in the +X/+Y quadrant, upper-right corner at (+half, +half).
    if side > 0:
        corner = half - side
        lines.append("(square: (%s,%s) to (%s,%s))"
                     % (fmt(corner), fmt(corner), fmt(half), fmt(half)))
        draw_path([
            (corner, corner), (half, corner), (half, half),
            (corner, half), (corner, corner),
        ])

    # Y ruler: one long stroke, then a tick across it at every mark.
    lines.append("(Y ruler: -%s to +%s at X%s)" % (fmt(half), fmt(half), fmt(ruler_offset)))
    draw_path([(ruler_offset, -half), (ruler_offset, half)])
    for y in ticks:
        h = end_half if abs(abs(y) - half) < 1e-9 else mid_half
        draw_path([(ruler_offset - h, y), (ruler_offset + h, y)])

    lines.append("M65 P0")
    lines.append("G65 P115 Q0 A3 W1")
    lines.append("M64 P0")
    lines.append("G53 G1 X-10 Y-436 F3000 (park home)")
    lines.append("M2")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("wrote %s (%d lines)" % (out, len(lines)))

    # --- self-checks -----------------------------------------------------
    bad = [k + 1 for k, ln in enumerate(lines) if ln.count("(") != ln.count(")")]
    if bad:
        raise SystemExit("unbalanced parentheses on lines: %s" % bad)

    motion = re.compile(r"^G[01] X(-?[\d.]+) Y(-?[\d.]+)")
    coords = []
    for number, ln in enumerate(lines, 1):
        code = re.sub(r"\(.*?\)", "", ln).strip()
        if not code.startswith("G65") and re.search(r"(?<![A-Za-z])A-?[\d.]", code):
            raise SystemExit("line %d carries an A word: %r" % (number, ln))
        m = motion.match(code)
        if m:
            coords.append((float(m.group(1)), float(m.group(2))))
    if not coords:
        raise SystemExit("no motion found")
    r_max = max(math.hypot(x, y) for x, y in coords)
    if r_max > 165.0:
        raise SystemExit("motion reaches r=%.1f mm, outside the 165 mm bench limit" % r_max)
    print("drawing length %.0f mm at F%s (~%.1f min); %d pen cycles"
          % (drawing_mm, fmt(feed), drawing_mm / feed + pen_cycles * 1.5 / 60.0, pen_cycles))
    print("max commanded radius %.1f mm; expected square diagonal %s mm"
          % (r_max, fmt(side * math.sqrt(2.0)) if side > 0 else "n/a"))


if __name__ == "__main__":
    main()
