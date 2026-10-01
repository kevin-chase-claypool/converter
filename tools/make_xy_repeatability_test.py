"""Write a Cycle-Start program that measures lost motion on the heavy gantry axis.

The bed test (`make_a_repeatability_test.py`) measures the rotating bed. This one
measures a linear axis that carries the gantry, where the risk is different:
the axis moves far more mass, so it is the one that stalls first, and the
converter's pen-up `G0` travels run at the controller's configured rapid rate
rather than at the `F` in the program - which is where a heavy axis is asked for
the most.

The program draws a short tick **across** the axis under test, runs the axis out
and back several times at one feed, redraws the tick, and repeats at faster
feeds. A slip in the axis moves the second tick along the axis, so the two ticks
print as two parallel lines and the gap between them is the lost motion at that
feed. The ladder ends at the configured rapid rate, so the last rung reproduces
what a `G0` travel actually does today.

Keep the bed still for this one: the moves are linear axis moves with A parked,
so what is measured is the gantry, not the bed.

Usage::

    python tools\\make_xy_repeatability_test.py                     # Y, 3000..20000
    python tools\\make_xy_repeatability_test.py --axis X --distance 120
    python tools\\make_xy_repeatability_test.py --feeds 3000,6000,12000
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


def build_program(settings, axis, distance, feeds, cycles, tick_mm=10.0, start=0.0):
    axis = axis.upper()
    if axis not in ("X", "Y"):
        raise ValueError("axis must be X or Y")
    other = "Y" if axis == "X" else "X"

    def point(value, other_value=0.0):
        return (value, other_value) if axis == "X" else (other_value, value)

    half = tick_mm / 2.0
    lines = [
        f"({axis}-axis repeatability test - lost motion under load)",
        f"(tick across the axis, {cycles} runs out and back per feed, tick again)",
        "(ticks on top of each other = no slip; a gap along the axis is the loss)",
        f"(distance {distance:g} mm, feeds {', '.join(f'{f:g}' for f in feeds)} mm/min)",
        "(keep the bed still: this measures the gantry axis, not the bed)",
        "G21",
        "G90",
        "G94",
        "G17",
        "G54",
        f"G0 F{fmt(settings.travel_rate)}",
        settings.pen_up_command,
        f"G4 P{fmt(settings.pen_up_ms / 1000.0)}",
        f"A0",
    ]

    first_down = True

    def tick_lines(prefix="G1"):
        return [
            f"{prefix} X{fmt(point(start)[0] + (half if other == 'X' else 0.0))} "
            f"Y{fmt(point(start)[1] + (half if other == 'Y' else 0.0))}",
            f"{prefix} X{fmt(point(start)[0] - (half if other == 'X' else 0.0))} "
            f"Y{fmt(point(start)[1] - (half if other == 'Y' else 0.0))}",
        ]

    def pen_down():
        nonlocal first_down
        dwell_ms = settings.pen_down_first_ms if first_down else settings.pen_down_ms
        first_down = False
        return [settings.pen_down_command, f"G4 P{fmt(dwell_ms / 1000.0)}"]

    def pen_up():
        return [settings.pen_up_command, f"G4 P{fmt(settings.pen_up_ms / 1000.0)}"]

    for feed in feeds:
        lines.append(f"(feed {feed:g} mm/min)")
        start_point = point(start)
        end_point = point(start + distance)
        lines.append(f"G0 X{fmt(start_point[0])} Y{fmt(start_point[1])}")
        # Tick before, with the pen down.
        lines.extend(pen_down())
        lines.append(f"G1 F{fmt(settings.feed_rate)}")
        # A tick across the axis: a slip along it separates the two ticks.
        lines.extend(tick_lines())
        lines.extend(pen_up())
        # Fed travels with the pen UP - the ladder is real (a G0 would run at the
        # axis rapid rate regardless of any F in the program), and this is the
        # motion a normal job's pen-up travel actually makes.
        for _ in range(cycles):
            lines.append(
                f"G1 X{fmt(end_point[0])} Y{fmt(end_point[1])} F{fmt(feed)}"
            )
            lines.append(
                f"G1 X{fmt(start_point[0])} Y{fmt(start_point[1])} F{fmt(feed)}"
            )
        # Tick after, same machine position: any gap is the axis's own error.
        lines.extend(pen_down())
        lines.append(f"G1 F{fmt(settings.feed_rate)}")
        lines.extend(tick_lines())
        lines.extend(pen_up())

    lines.append(
        f"G53 G0 X{fmt(settings.park_x_machine)} Y{fmt(settings.park_y_machine)} (park home)"
    )
    lines.append("M2")
    return "\n".join(lines) + "\n"


def check_comments(program):
    """A G-code comment must open and close on the same line (ioSender rejects
    anything else while loading the file)."""
    for number, line in enumerate(program.splitlines(), 1):
        if line.count("(") != line.count(")"):
            raise ValueError(f"line {number} has an unbalanced comment: {line!r}")
        if "(" in line and not line.rstrip().endswith(")"):
            raise ValueError(f"line {number} wraps a comment or trails code: {line!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--axis", default="Y")
    parser.add_argument("--distance", type=float, default=160.0)
    parser.add_argument("--cycles", type=int, default=5)
    parser.add_argument(
        "--feeds",
        default=None,
        help="comma-separated feed ladder in mm/min (default 3000,6000,12000,<rapid>)",
    )
    parser.add_argument(
        "--rapid",
        type=float,
        default=20000.0,
        help="top of the ladder; set this to the controller's $110/$111 max rate, "
        "because that is what a G0 pen-up travel actually runs at",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "gcode" / "y-repeatability-test.gcode"),
    )
    args = parser.parse_args()

    settings = converter.Settings()
    rapid = float(args.rapid)
    feeds = (
        [float(part) for part in args.feeds.split(",")]
        if args.feeds
        else [3000.0, 6000.0, 12000.0, rapid]
    )
    program = build_program(
        settings, args.axis, args.distance, feeds, max(1, int(args.cycles))
    )
    check_comments(program)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(program, encoding="utf-8", newline="\n")

    per_run_seconds = args.distance / min(feeds) * 60.0
    print(
        "wrote %s\n"
        "  axis %s, %.0f mm, %d runs out and back per feed\n"
        "  feeds %s mm/min\n"
        "  slowest rung alone is %.0f s of travel; the whole ladder is a few minutes"
        % (
            out,
            args.axis.upper(),
            args.distance,
            args.cycles,
            ", ".join(f"{f:g}" for f in feeds),
            per_run_seconds * 2 * args.cycles,
        )
    )
    print(
        "  note: the G0 pen-up travels in normal jobs run at the controller's "
        "rapid rate (%g mm/min for X/Y in the settings dump), which the last "
        "rung reproduces." % rapid
    )


if __name__ == "__main__":
    main()
