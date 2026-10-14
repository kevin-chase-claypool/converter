"""Generate the bed-angle line-replay test.

One origin line is drawn at A = 0 - the reference, like the screw you leave
alone in a 3D-printer bed-tilt adjustment. The same bed-frame line is then
replayed with the bed indexed to other angles; every replay should land
exactly on the origin. A translation error shows as a parallel gap between
the lines; a rotation error shows as a fan, the ends spreading by
``2 * half * sin(dtheta / 2)`` - half a degree over a 60 mm half-line is
already 0.52 mm of spread. Draw with the finest pen available: a 0.15 mm
Pigma Micron 003 makes roughly 0.2 mm offsets visible under a loupe or a
close-up photo.

Passes, in draw order, with a stepped end-length code so each line is
identifiable with calipers (total lengths for the defaults):

* ``origin`` - the longest line, 140 mm, drawn at A = 0; the reference.
* ``control`` - ``--control-passes`` A = 0 replays, 120 mm; they must sit
  exactly on the origin, or the machine's repeatability is the story, not
  the bed.
* ``replay`` - one pass per angle in ``--angles`` (default 90/180/270, the
  quadrant comparison); each replay is 8 mm shorter in total length than the
  previous one, so the default staircase is 112 / 104 / 96 mm for
  90 / 180 / 270 deg. ``--replay-step 0`` disables the stepping.
* ``closing`` - a final A = 0 pass after the highest angle, 128 mm; it must
  land on the origin for the drivetrain to pass, and it exercises the A
  reversal.

Reading: a constant gap between a replay and the origin is that quadrant's
offset; a fan opening at the ends is rotation about the centre. Measure the
gap with calipers or a straight-down photo; a caliper across a line's ends
reads its total length and attributes it to the right angle. Adjust the bed
tilt rail ends and re-run until the lines collapse.

Requires HOME + bed registration, so G54 X0 Y0 is the physical bed centre.

Usage::

    python tools\\make_a_line_replay_test.py
    python tools\\make_a_line_replay_test.py --angles 45,90,135,180,225,270,315
    python tools\\make_a_line_replay_test.py --no-closing
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATIO = 12.03324
OUTPUT = ROOT / "samples" / "gcode" / "a-line-replay-test.gcode"


def fmt(v: float) -> str:
    if abs(v) < 1e-9:
        return "0"
    return ("%.4f" % v).rstrip("0").rstrip(".")


def to_machine(bed_x: float, bed_y: float, theta_deg: float) -> tuple[float, float]:
    t = math.radians(theta_deg)
    c, s = math.cos(t), math.sin(t)
    return (bed_x * c - bed_y * s, bed_x * s + bed_y * c)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(OUTPUT))
    parser.add_argument(
        "--half-length", type=float, default=70.0,
        help="origin line half length in mm (default 70)",
    )
    parser.add_argument(
        "--replay-half-length", type=float, default=60.0, dest="replay_half",
        help="replay and control half length in mm (default 60)",
    )
    parser.add_argument(
        "--angles", default="90,180,270",
        help="replay bed angles in degrees, comma separated (default quadrants)",
    )
    parser.add_argument(
        "--control-passes", type=int, default=2, dest="control_passes",
        help="A=0 replays drawn right after the origin (default 2)",
    )
    parser.add_argument(
        "--closing", action=argparse.BooleanOptionalAction, default=True,
        help="draw a final A=0 replay after the highest angle (default on)",
    )
    parser.add_argument(
        "--replay-step", type=float, default=4.0, dest="replay_step",
        help="each replay is this much shorter per half end, so the end "
             "staircase identifies it (default 4 mm; 0 disables)",
    )
    parser.add_argument(
        "--line-angle", type=float, default=0.0, dest="line_angle",
        help="paper-frame direction of the line in degrees (default 0, along X)",
    )
    parser.add_argument("--feed", type=float, default=350.0)
    args = parser.parse_args()

    angles = sorted(
        float(part) for part in args.angles.split(",") if part.strip()
    )
    if not angles or any(angle <= 0.0 or angle >= 360.0 for angle in angles):
        raise SystemExit("replay angles must each be between 0 and 360 degrees")
    if args.replay_half >= args.half_length:
        raise SystemExit(
            "replay half length must be shorter than the origin half length"
        )
    if args.control_passes < 0:
        raise SystemExit("control passes cannot be negative")
    if args.replay_step < 0:
        raise SystemExit("replay step cannot be negative")

    replay_halves = [
        args.replay_half - args.replay_step * (index + 1)
        for index in range(len(angles))
    ]
    if replay_halves and replay_halves[-1] < 20.0:
        raise SystemExit(
            "the shortest replay would fall under a 20 mm half length; "
            "reduce --replay-step or --replay-half-length"
        )
    closing_half = args.replay_half + args.replay_step
    if args.closing and closing_half >= args.half_length:
        raise SystemExit(
            "the closing pass must stay shorter than the origin; reduce "
            "--replay-step or --replay-half-length"
        )

    direction = math.radians(args.line_angle)
    ux, uy = math.cos(direction), math.sin(direction)

    def pass_points(half: float, theta_deg: float) -> tuple[float, float, float, float]:
        x0, y0 = to_machine(-half * ux, -half * uy, theta_deg)
        x1, y1 = to_machine(half * ux, half * uy, theta_deg)
        return x0, y0, x1, y1

    lines: list[str] = []
    lines.append("(bed-angle line-replay test - make_a_line_replay_test.py)")
    lines.append("(origin = longest line at A=0; every other pass must land on it)")
    lines.append("(parallel gap between lines = that angle's offset; fan at the ends = rotation)")
    lines.append("(requires HOME + bed registration; pen: finest available, e.g. Pigma Micron 003)")
    lines.append(
        "(draw order: origin, %d control passes at A=0, replays %s, closing pass)"
        % (args.control_passes, "/".join(fmt(angle) for angle in angles))
    )
    length_bits = ["origin %s" % fmt(args.half_length * 2)]
    if args.control_passes:
        length_bits.append("control %s" % fmt(args.replay_half * 2))
    if angles and args.replay_step > 0:
        length_bits.append(
            "replays %s" % "/".join(fmt(half * 2) for half in replay_halves)
        )
    if args.closing:
        length_bits.append("closing %s" % fmt(closing_half * 2))
    length_code = ", ".join(length_bits)
    lines.append("(identification by total length in mm: %s)" % length_code)
    lines.extend(
        ["G21", "G90", "G94", "G17", "G54", "G0 F3000", "M5", "G65 P115 Q0 A1 W2"]
    )

    first_down = True

    def draw_pass(label: str, theta_deg: float, half: float) -> None:
        nonlocal first_down
        a = theta_deg * RATIO
        x0, y0, x1, y1 = pass_points(half, theta_deg)
        lines.append(
            "(%s: bed angle %s deg, half length %s)"
            % (label, fmt(theta_deg), fmt(half))
        )
        lines.append("G0 X%s Y%s A%s" % (fmt(x0), fmt(y0), fmt(a)))
        lines.append("M3")
        lines.append("G65 P115 Q1 B12 A1 W2" if first_down else "G65 P115 Q1 A1 W2")
        first_down = False
        lines.append(
            "G1 X%s Y%s A%s F%s" % (fmt(x1), fmt(y1), fmt(a), fmt(args.feed))
        )
        lines.append("M5")
        lines.append("G65 P115 Q1 A1 W2")

    draw_pass("origin, %s mm total" % fmt(args.half_length * 2), 0.0, args.half_length)
    for index in range(args.control_passes):
        draw_pass(
            "control %d, %s mm total" % (index + 1, fmt(args.replay_half * 2)),
            0.0,
            args.replay_half,
        )
    for index, theta in enumerate(angles):
        draw_pass(
            "replay %s, %s mm total" % (fmt(theta), fmt(replay_halves[index] * 2)),
            theta,
            replay_halves[index],
        )
    if args.closing:
        draw_pass("closing, %s mm total" % fmt(closing_half * 2), 0.0, closing_half)

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
    passes = 1 + args.control_passes + len(angles) + (1 if args.closing else 0)
    if len(a_values) != passes:
        raise SystemExit(
            "expected %d drawing passes, generated %d" % (passes, len(a_values))
        )
    print(
        "passes: %d (origin 1, control %d, replays %d, closing %d)"
        % (passes, args.control_passes, len(angles), 1 if args.closing else 0)
    )
    print("identification by total length in mm: %s" % length_code)
    print("A range %.1f..%.1f motor deg" % (min(a_values), max(a_values)))
    print(
        "max commanded radius: %.1f mm" % max(args.half_length, args.replay_half)
    )


if __name__ == "__main__":
    main()
