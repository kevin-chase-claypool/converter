"""Generate the CMYK pen-alignment crosses.

One file draws five crosses (centre plus four corners at +-75 mm, 10 mm
arms) with the bed parked at A = 0. Run the SAME file unchanged once per
CMYK pen on one sheet: the crosses from every pen should land on top of one
another. Any per-pen gap is that pen's XY tip offset relative to the first
pen, which is what a multi-pass registration cannot correct by itself.

Usage:
    python tools\\make_cmyk_pen_alignment.py
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "samples" / "gcode" / "cmyk-pen-alignment.gcode"

HALF_ARM_MM = 5.0
FEED_MM_MIN = 350.0
STATIONS = (
    ("centre", 0.0, 0.0),
    ("top-left", -75.0, 75.0),
    ("top-right", 75.0, 75.0),
    ("bottom-left", -75.0, -75.0),
    ("bottom-right", 75.0, -75.0),
)


def fmt(value: float) -> str:
    text = "%.4f" % value
    return text.rstrip("0").rstrip(".")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(OUTPUT))
    args = parser.parse_args()

    lines = [
        "(CMYK pen-alignment crosses - make_cmyk_pen_alignment.py)",
        "(five crosses: centre + corners at +/-75 mm, 10 mm arms)",
        "(bed parked at A0; run this SAME file once per pen, no re-registration)",
        "(crosses coincident = shared tip offset; per-pen gaps = XY pen offsets)",
        "G21",
        "G90",
        "G94",
        "G17",
        "G54",
        "G0 F3000",
        "M5",
        "G65 P115 Q0 A1 W2",
    ]
    first_down = True

    def stroke(start: tuple[float, float], end: tuple[float, float]) -> None:
        nonlocal first_down
        lines.append(
            "G0 X%s Y%s A0" % (fmt(start[0]), fmt(start[1]))
        )
        lines.append("M3")
        lines.append(
            "G65 P115 Q1 B12 A1 W2" if first_down else "G65 P115 Q1 A1 W2"
        )
        first_down = False
        lines.append("G1 F%s" % fmt(FEED_MM_MIN))
        lines.append(
            "G1 X%s Y%s A0 F%s"
            % (fmt(end[0]), fmt(end[1]), fmt(FEED_MM_MIN))
        )
        lines.append("M5")
        lines.append("G65 P115 Q1 A1 W2")

    for name, cx, cy in STATIONS:
        lines.append("(cross %s at %s,%s mm)" % (name, fmt(cx), fmt(cy)))
        stroke((cx - HALF_ARM_MM, cy), (cx + HALF_ARM_MM, cy))
        stroke((cx, cy - HALF_ARM_MM), (cx, cy + HALF_ARM_MM))

    lines.extend(
        [
            "M65 P0",
            "G65 P115 Q0 A3 W1",
            "M64 P0",
            "G53 G1 X-10 Y-436 F3000 (park home)",
            "M2",
        ]
    )

    out = Path(args.out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote %s (%d lines)" % (out, len(lines)))

    bad = [k + 1 for k, line in enumerate(lines) if line.count("(") != line.count(")")]
    if bad:
        raise SystemExit("unbalanced parentheses on lines: %s" % bad)

    move = re.compile(r"^G1 X(-?[\d.]+) Y(-?[\d.]+) A(-?[\d.]+) F")
    ends = [match for match in (move.match(line) for line in lines) if match]
    if len(ends) != 2 * len(STATIONS):
        raise SystemExit(
            "expected %d strokes, generated %d"
            % (2 * len(STATIONS), len(ends))
        )
    angles = {float(match.group(3)) for match in ends}
    if angles != {0.0}:
        raise SystemExit("alignment test must not rotate the bed: %s" % angles)
    radius = max(
        (float(m.group(1)) ** 2 + float(m.group(2)) ** 2) ** 0.5
        for m in ends
    )
    print(
        "strokes: %d, A constant at %s, max radius %.1f mm"
        % (len(ends), sorted(angles)[0], radius)
    )


if __name__ == "__main__":
    main()
