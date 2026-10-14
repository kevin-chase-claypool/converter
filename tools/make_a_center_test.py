"""Generate the bed-rotation-centre test.

One paper point is visited at eight bed angles (0..315 deg in 45 deg steps),
drawing a small paper-aligned tick each time, plus a four-pass control at a
single angle. If the registered centre (G54 X0 Y0) is exactly on the physical
bed axis, every tick lands on the same spot. If the centre is off by a vector
C, each tick at angle theta is displaced by

    e(theta) = C - R(-theta) C

so the eight ticks spread into a ring of radius |C| centred on C; the offset
between opposite angles is exactly 2|C| and its direction reads C directly.
This error is invisible to fixed-bed plots (constant theta), to round-trip
tests, and to any single-angle diagnostic - which is why it is the last
mechanism standing.

Usage:
    python tools\\make_a_center_test.py
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATIO = 12.03324
OUTPUT = ROOT / "samples" / "gcode" / "a-center-test.gcode"

POINT = (0.0, 80.0)   # paper-frame point, top of the sheet
HALF_TICK = 1.5       # mm, along paper X


def fmt(v: float) -> str:
    return ("%.4f" % v).rstrip("0").rstrip(".")


def to_machine(bed_x: float, bed_y: float, theta_deg: float) -> tuple[float, float]:
    t = math.radians(theta_deg)
    c, s = math.cos(t), math.sin(t)
    return (bed_x * c - bed_y * s, bed_x * s + bed_y * c)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUTPUT))
    args = ap.parse_args()

    lines: list[str] = []
    lines.append("(bed-rotation-centre test - make_a_center_test.py)")
    lines.append("(one paper point at 8 bed angles, paper-aligned ticks)")
    lines.append("(ticks coincident = centre correct; spread up to 2*|C| = centre offset)")
    lines.append("(control: four ticks at a single angle - must overlap exactly)")
    lines.extend(["G21", "G90", "G94", "G17", "G54", "G0 F3000", "M5", "G65 P115 Q0 A1 W2"])

    first_down = True

    def tick(theta_deg: float) -> None:
        nonlocal first_down
        a = theta_deg * RATIO
        x0, y0 = to_machine(POINT[0] - HALF_TICK, POINT[1], theta_deg)
        x1, y1 = to_machine(POINT[0] + HALF_TICK, POINT[1], theta_deg)
        lines.append("G0 X%s Y%s A%s" % (fmt(x0), fmt(y0), fmt(a)))
        lines.append("M3")
        lines.append("G65 P115 Q1 B12 A1 W2" if first_down else "G65 P115 Q1 A1 W2")
        first_down = False
        lines.append("G1 F350")
        lines.append("G1 X%s Y%s A%s F350" % (fmt(x1), fmt(y1), fmt(a)))
        lines.append("M5")
        lines.append("G65 P115 Q1 A1 W2")

    lines.append("(control: four ticks at theta=0)")
    for _ in range(4):
        tick(0.0)
    lines.append("(station: ticks at theta = 0..315)")
    for theta in (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0):
        tick(theta)

    lines.append("M65 P0")
    lines.append("G65 P115 Q0 A3 W1")
    lines.append("M64 P0")
    lines.append("G53 G1 X-10 Y-436 F3000 (park home)")
    lines.append("M2")

    out = Path(args.out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote %s (%d lines)" % (out, len(lines)))

    bad = [k + 1 for k, ln in enumerate(lines) if ln.count("(") != ln.count(")")]
    if bad:
        raise SystemExit("unbalanced parentheses on lines: %s" % bad)

    import re

    mv = re.compile(r"^G1 X(-?[\d.]+) Y(-?[\d.]+) A(-?[\d.]+) F")
    a_vals = [float(m.group(3)) for m in (mv.match(ln) for ln in lines) if m]
    print("ticks: %d, A range %.1f..%.1f motor deg" % (len(a_vals), min(a_vals), max(a_vals)))


if __name__ == "__main__":
    main()
