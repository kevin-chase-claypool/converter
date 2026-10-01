"""Write a Cycle-Start program that measures A-axis lost motion on paper.

The bed has no encoder: grblHAL counts steps and assumes the bed went where it
was told. If the A axis stalls - which is what happens when ``$113`` promises a
rate the 12:1 bed cannot hold - the paper keeps the evidence: everything drawn
afterwards is rotated by the angle that was lost.

This program makes that measurable without any instrumentation:

* it parks the pen at a radius (default 100 mm, then 160 mm) and draws a short
  **radial tick**,
* rotates the bed a whole number of revolutions outward and back with the pen
  down, so the same circle is retraced in both directions,
* redraws the radial tick in the same place.

If the bed returns exactly, the two ticks print on top of each other. If steps
were lost, the second tick is rotated away from the first, and the gap is
measured directly with a rule: at radius ``R`` a gap of ``s`` mm is
``degrees(s / R)`` of lost motion for the whole out-and-back.

The program uses the converter's own pen contract (``M3``/``M5`` with the
configured dwells, the travel rate, and the end-of-program park), so it can be
started from ioSender exactly like a normal job. Run ``P100`` first: work
``X0 Y0`` must be the registered bed centre, or the circle is not centred on the
bed and the test measures the wrong thing.

Usage::

    python tools\\make_a_repeatability_test.py
    python tools\\make_a_repeatability_test.py --radius 160 --revolutions 3
    python tools\\make_a_repeatability_test.py --feed 12000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter  # noqa: E402


def fmt(value):
    return converter.format_float(float(value))


def build_program(settings, radii, revolutions, feed, tick_mm=10.0):
    turn = settings.theta_drive_ratio * 360.0
    lines = [
        "(A-axis repeatability test - lost motion after a full bed revolution)",
        f"(one bed revolution = {turn:.4f} A motor degrees; ratio "
        f"{settings.theta_drive_ratio:.5f} motor deg per bed deg)",
        "(prerequisite: HOME and P100, so work X0 Y0 is the registered bed centre)",
        "(each station draws a radial tick, rotates out and back, redraws the tick)",
        "(ticks on top of each other = the bed returned)",
        "(a gap s mm at radius R mm is degrees(s/R) of lost motion for that out-and-back)",
        f"(stations at radii {', '.join(f'{r:g}' for r in radii)} mm; "
        f"{revolutions} revolutions each way at F{feed:g})",
        "G21",
        "G90",
        "G94",
        "G17",
        "G54",
        f"G0 F{fmt(settings.travel_rate)}",
        settings.pen_up_command,
        f"G4 P{fmt(settings.pen_up_ms / 1000.0)}",
    ]

    first_down = True
    for radius in radii:
        lines.append(f"(station: r={radius:g} mm)")
        lines.append(f"G0 X{fmt(radius)} Y0")
        lines.append(settings.pen_down_command)
        dwell_ms = settings.pen_down_first_ms if first_down else settings.pen_down_ms
        lines.append(f"G4 P{fmt(dwell_ms / 1000.0)}")
        first_down = False
        lines.append(f"G1 F{fmt(settings.feed_rate)}")
        # Tick before: inward then back out, so the mark straddles the radius.
        lines.append(f"G1 X{fmt(radius - tick_mm / 2.0)} Y0")
        lines.append(f"G1 X{fmt(radius + tick_mm / 2.0)} Y0")
        # Rotate with the pen down: the paper turns under a stationary pen, so
        # one revolution draws a circle and the return pass retraces it.
        lines.append("G91")
        for _ in range(revolutions):
            lines.append(f"G1 A{fmt(turn)} F{fmt(feed)}")
        for _ in range(revolutions):
            lines.append(f"G1 A{fmt(-turn)} F{fmt(feed)}")
        lines.append("G90")
        # Tick after: same machine position, so any gap is the bed's own error.
        lines.append(f"G1 X{fmt(radius - tick_mm / 2.0)} Y0")
        lines.append(f"G1 X{fmt(radius + tick_mm / 2.0)} Y0")
        lines.append(settings.pen_up_command)
        lines.append(f"G4 P{fmt(settings.pen_up_ms / 1000.0)}")

    lines.append(
        f"G53 G0 X{fmt(settings.park_x_machine)} Y{fmt(settings.park_y_machine)} (park home)"
    )
    lines.append("M2")
    return "\n".join(lines) + "\n"


def check_comments(program):
    """A G-code comment must open and close on the same line.

    ioSender's loader reads a parenthesized comment as a single-line token; a
    wrapped one makes it throw `Index and length must refer to a location within
    the string` and refuse the file, so this is checked before writing.
    """
    for number, line in enumerate(program.splitlines(), 1):
        if line.count("(") != line.count(")"):
            raise ValueError(
                f"line {number} has an unbalanced or wrapped G-code comment: {line!r}"
            )
        if "(" in line and not line.rstrip().endswith(")"):
            raise ValueError(
                f"line {number} puts code after a comment, or wraps one: {line!r}"
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "gcode" / "a-repeatability-test.gcode"),
    )
    parser.add_argument(
        "--radius",
        type=float,
        action="append",
        default=None,
        help="station radius in mm; repeat for several (default 100 and 160)",
    )
    parser.add_argument(
        "--revolutions",
        type=int,
        default=2,
        help="bed revolutions outward (and the same back) per station",
    )
    parser.add_argument(
        "--feed",
        type=float,
        default=None,
        help="A feed in motor deg/min; defaults to the converter's assumed A limit",
    )
    args = parser.parse_args()

    settings = converter.Settings()
    radii = args.radius or [100.0, 160.0]
    feed = args.feed or settings.theta_controller_limits.max_rate_deg_min
    revolutions = max(1, int(args.revolutions))

    program = build_program(settings, radii, revolutions, feed)
    check_comments(program)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # LF, like every other file in the repo.
    out.write_text(program, encoding="utf-8", newline="\n")

    turn = settings.theta_drive_ratio * 360.0
    per_rotation_seconds = turn / feed * 60.0
    print(
        "wrote %s\n"
        "  %d station(s) x %d revolutions out and back at F%g\n"
        "  one revolution = %.4f motor deg = %.1f s of rotation\n"
        "  total bed rotation %.1f s (plus pen moves and dwells)"
        % (
            out,
            len(radii),
            revolutions,
            feed,
            turn,
            per_rotation_seconds,
            len(radii) * revolutions * 2 * per_rotation_seconds,
        )
    )


if __name__ == "__main__":
    main()
