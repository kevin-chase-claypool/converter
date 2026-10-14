"""Generate the bed-tilt quadrant pair test.

Four pairs of lines are drawn at separated spots on the sheet. Each pair is
one paper segment drawn twice: the "constant" pass at A = 0, drawn longer,
and the "test" pass with the bed indexed to that pair's angle, drawn
shorter. With perfect geometry and the same bed height at both angles the
two passes land on top of one another; any offset between them is that
quadrant's error - the height difference coupling through the pen carriage
plus any residual mapping term. Measure the offsets with calipers, adjust
the rail ends until the pairs collapse, and re-run; the control pair is the
constant quadrant against which the other three are read.

Layout (paper / G54 frame): pairs at (-50,-50), (50,-50), (50,50),
(-50,50); lines run along X. Constant half length 40 mm, test half length
33 mm, so inside a pair the LONGER line is always the constant pass. Each
pair carries a zigzag tick label above it whose number of teeth says the
tested angle: 1 = 0 deg (control, A0 drawn twice), 2 = 90, 3 = 180,
4 = 270 deg.

``--station-shift-y`` shifts the four station positions up or down so a
re-run after an adjustment lands on clean paper on the same sheet:
``--station-shift-y -25`` puts the layout between the previous rows and
uses clean bands. ``--station-rot`` rotates the stations about the sheet
centre when there is room - the X lines extend 40 mm past each station, so
keep the rotated stations' x positions modest.

Reading: for each pair measure the perpendicular gap between the two lines
in the middle and near both ends (a fan shows as unequal end gaps), plus
the end overhangs - the shorter line sits 7 mm inside the longer one at each
end when the pair is clean. Report each pair by its tooth count.

Requires HOME + bed registration, so G54 X0 Y0 is the physical bed centre.
The whole layout spans about +-90 mm in X and +-62 mm in Y, so it fits the
sheet already on the bed and clears the earlier test's ink at y = 0.

Usage:

    python tools\\make_a_tilt_pairs_test.py
    python tools\\make_a_tilt_pairs_test.py --station-rot 60
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATIO = 12.03324
OUTPUT = ROOT / "samples" / "gcode" / "a-tilt-pairs-test.gcode"

CONSTANT_HALF = 40.0
TEST_HALF = 33.0
PAIRS = (
    ("control", 0.0, -50.0, -50.0),
    ("90 deg", 90.0, 50.0, -50.0),
    ("180 deg", 180.0, 50.0, 50.0),
    ("270 deg", 270.0, -50.0, 50.0),
)


def fmt(v: float) -> str:
    if abs(v) < 1e-9:
        return "0"
    return ("%.4f" % v).rstrip("0").rstrip(".")


def to_machine(bed_x: float, bed_y: float, theta_deg: float) -> tuple[float, float]:
    t = math.radians(theta_deg)
    c, s = math.cos(t), math.sin(t)
    return (bed_x * c - bed_y * s, bed_x * s + bed_y * c)


def comb_points(teeth: int) -> list[tuple[float, float]]:
    y_bot = 8.0
    y_top = 12.0
    x_start = -41.0
    points: list[tuple[float, float]] = [(x_start, y_bot), (x_start, y_top)]
    for k in range(1, teeth):
        x = x_start + 5.0 * k
        if k % 2 == 1:
            points.append((x, y_top))
            points.append((x, y_bot))
        else:
            points.append((x, y_bot))
            points.append((x, y_top))
    return points


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(OUTPUT))
    parser.add_argument("--feed", type=float, default=350.0)
    parser.add_argument(
        "--station-rot", type=float, default=0.0, dest="station_rot",
        help="rotate the four station positions about the sheet centre, "
             "in degrees (default 0)",
    )
    parser.add_argument(
        "--station-shift-y", type=float, default=0.0, dest="station_shift_y",
        help="shift the four station positions along Y in mm, for fresh "
             "spots on the same sheet (default 0)",
    )
    args = parser.parse_args()

    rot = math.radians(args.station_rot)
    rot_c, rot_s = math.cos(rot), math.sin(rot)

    def rotxy(x: float, y: float) -> tuple[float, float]:
        return (x * rot_c - y * rot_s, x * rot_s + y * rot_c)

    lines: list[str] = []
    lines.append("(bed-tilt quadrant pair test - make_a_tilt_pairs_test.py)")
    lines.append("(four pairs of two lines; inside a pair the LONGER line is the A=0 constant)")
    lines.append("(and the SHORTER line is the re-draw at that pair's angle - they should land on top)")
    lines.append("(zigzag label above each pair counts the angle: 1 tooth = control, A0 into A0)")
    lines.append("(2 teeth = 90 deg, 3 teeth = 180, 4 teeth = 270; the control pair sets the baseline)")
    lines.append("(measure between the pair's lines: middle gap plus both end overhangs)")
    lines.append("(requires HOME + bed registration; pen: finest available, e.g. Pigma Micron 003)")
    lines.extend(
        ["G21", "G90", "G94", "G17", "G54", "G0 F3000", "M5", "G65 P115 Q0 A1 W2"]
    )

    first_down = True

    def stroke(a_deg: float, paper_points: list[tuple[float, float]], comment: str) -> None:
        nonlocal first_down
        a = a_deg * RATIO
        lines.append(comment)
        m0 = to_machine(paper_points[0][0], paper_points[0][1], a_deg)
        lines.append("G0 X%s Y%s A%s" % (fmt(m0[0]), fmt(m0[1]), fmt(a)))
        lines.append("M3")
        lines.append("G65 P115 Q1 B12 A1 W2" if first_down else "G65 P115 Q1 A1 W2")
        first_down = False
        for index, (bx, by) in enumerate(paper_points[1:]):
            mx, my = to_machine(bx, by, a_deg)
            feed = " F%s" % fmt(args.feed) if index == 0 else ""
            lines.append("G1 X%s Y%s A%s%s" % (fmt(mx), fmt(my), fmt(a), feed))
        lines.append("M5")
        lines.append("G65 P115 Q1 A1 W2")

    for name, theta, cx, cy in PAIRS:
        teeth = int(round(theta / 90.0)) + 1
        ccx, ccy = rotxy(cx, cy)
        ccy += args.station_shift_y
        comb = [
            (ccx + lx * rot_c - ly * rot_s, ccy + lx * rot_s + ly * rot_c)
            for (lx, ly) in comb_points(teeth)
        ]
        stroke(
            0.0,
            comb,
            "(pair %s: %d-teeth label)" % (name, teeth),
        )
        stroke(
            0.0,
            [(ccx - CONSTANT_HALF, ccy), (ccx + CONSTANT_HALF, ccy)],
            "(pair %s: constant pass at A=0, %s mm)"
            % (name, fmt(CONSTANT_HALF * 2)),
        )
        stroke(
            theta,
            [(ccx - TEST_HALF, ccy), (ccx + TEST_HALF, ccy)],
            "(pair %s: test pass at bed angle %s, %s mm)"
            % (name, fmt(theta), fmt(TEST_HALF * 2)),
        )

    lines.append("M65 P0")
    lines.append("G65 P115 Q0 A3 W1")
    lines.append("M64 P0")
    lines.append("G53 G1 X-10 Y-436 F3000 (park home)")
    lines.append("M2")

    out = Path(args.out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote %s (%d lines)" % (out, len(lines)))

    bad = [
        number + 1
        for number, line in enumerate(lines)
        if line.count("(") != line.count(")")
    ]
    if bad:
        raise SystemExit("unbalanced parentheses on lines: %s" % bad)

    move = re.compile(r"^G1 X(-?[\d.]+) Y(-?[\d.]+) A(-?[\d.]+) F")
    a_values = [
        float(match.group(3))
        for match in (move.match(line) for line in lines)
        if match
    ]
    passes = len(PAIRS) * 3
    if len(a_values) != passes:
        raise SystemExit(
            "expected %d drawing strokes, generated %d" % (passes, len(a_values))
        )
    print(
        "strokes: %d (4 pairs x label/constant/test); A values %s"
        % (passes, "/".join(fmt(v / RATIO) for v in sorted(set(a_values))))
    )
    coord = re.compile(r"[XY](-?[\d.]+)")
    radii = []
    for line in lines:
        if line.startswith(("G0 X", "G1 X")):
            values = coord.findall(line)
            if len(values) >= 2:
                radii.append(math.hypot(float(values[0]), float(values[1])))
    print("max commanded radius: %.1f mm" % max(radii))


if __name__ == "__main__":
    main()
