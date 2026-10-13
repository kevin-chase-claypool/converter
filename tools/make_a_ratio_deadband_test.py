"""Generate the A-axis ratio / directional deadband test.

Two parts, all with A as the only commanded axis while drawing:

  Part A - full-turn ratio and hysteresis, at r=100 mm, base angles
  45/135/225/315 deg: a tick, then A += 4332 motor deg (one full bed turn at
  the calibrated 12.03324), tick, A -= back, tick. If the calibrated ratio is
  right, all three ticks coincide; if the true ratio is the pure tooth count
  12.000, each commanded "turn" lands ~1.0 bed degree off (1.75 mm at r=100).
  Tick-1 vs tick-2 separation shows direction-dependent hysteresis.

  Part B - directional deadband at r=70 mm, psi=90 deg: ticks drawn with the
  bed arriving at A=0 first from the + side, then from the - side, twice
  each. The offset between the two tick families is the reverse deadband
  (approach-dependent lost motion) at that radius.

Usage:
    python tools\\make_a_ratio_deadband_test.py
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATIO = 12.03324
FULL_TURN_MOTOR_DEG = 360.0 * RATIO
OUTPUT = ROOT / "samples" / "gcode" / "a-ratio-deadband-test.gcode"


def fmt(v: float) -> str:
    return ("%.4f" % v).rstrip("0").rstrip(".")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUTPUT))
    args = ap.parse_args()

    lines: list[str] = []
    lines.append("(A-axis ratio + directional deadband test - make_a_ratio_deadband_test.py)")
    lines.append("(part A: r=100, psi 45/135/225/315: tick / A+4332 / tick / A-4332 / tick)")
    lines.append("(tick offset after a commanded full turn = ratio error; tick1-tick2 = hysteresis)")
    lines.append("(part B: r=70, psi=90: ticks arriving at A=0 from +, then -, twice each)")
    lines.append("(tick family offset = reverse deadband at that radius)")
    lines.extend(["G21", "G90", "G94", "G17", "G54", "G0 F3000", "M5", "G65 P115 Q0 A1 W2"])

    first_down = True

    def pen_down() -> None:
        nonlocal first_down
        lines.append("M3")
        lines.append("G65 P115 Q1 B12 A1 W2" if first_down else "G65 P115 Q1 A1 W2")
        lines.append("G1 F350")
        first_down = False

    def pen_up() -> None:
        lines.append("M5")
        lines.append("G65 P115 Q1 A1 W2")

    def tick(x: float, y: float) -> None:
        """Draw a 4 mm tangential tick centred on (x, y) with A unchanged."""
        r = math.hypot(x, y)
        ux, uy = x / r, y / r
        ax, ay = x - uy * 2.0, y + ux * 2.0
        bx, by = x + uy * 2.0, y - ux * 2.0
        lines.append("G0 X%s Y%s" % (fmt(ax), fmt(ay)))
        pen_down()
        lines.append("G1 X%s Y%s F350" % (fmt(bx), fmt(by)))
        pen_up()

    # Part A: full-turn ratio / hysteresis
    for psi_deg in (45.0, 135.0, 225.0, 315.0):
        psi = math.radians(psi_deg)
        x, y = 100.0 * math.cos(psi), 100.0 * math.sin(psi)
        lines.append("(station: ratio at r=100 psi=%s)" % fmt(psi_deg))
        tick(x, y)
        lines.append("G1 X%s Y%s A%s F12000" % (fmt(x), fmt(y), fmt(FULL_TURN_MOTOR_DEG)))
        tick(x, y)
        lines.append("G1 X%s Y%s A0 F12000" % (fmt(x), fmt(y)))
        tick(x, y)

    # Part B: directional deadband
    lines.append("(station: deadband at r=70 psi=90)")
    dx, dy = 0.0, 70.0
    for _ in range(2):
        lines.append("G1 X%s Y%s A24.0665 F3000" % (fmt(dx), fmt(dy)))
        lines.append("G1 X%s Y%s A0 F3000" % (fmt(dx), fmt(dy)))
        tick(dx, dy)
    for _ in range(2):
        lines.append("G1 X%s Y%s A-24.0665 F3000" % (fmt(dx), fmt(dy)))
        lines.append("G1 X%s Y%s A0 F3000" % (fmt(dx), fmt(dy)))
        tick(dx, dy)

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

    mv = re.compile(r"^G1 X(-?[\d.]+) Y(-?[\d.]+) A(-?[\d.]+) F([\d.]+)")
    a_vals = [float(m.group(3)) for m in (mv.match(ln) for ln in lines) if m]
    print("A moves: %d, A range %.1f..%.1f motor deg, full turn = %.1f"
          % (len(a_vals), min(a_vals), max(a_vals), FULL_TURN_MOTOR_DEG))


if __name__ == "__main__":
    main()
