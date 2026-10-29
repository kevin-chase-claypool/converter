"""Generate a one-page T-01H pen-clear no-drag diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter  # noqa: E402


def fmt(value):
    return converter.format_float(float(value))


def witness_points():
    points = []
    for row in range(6):
        columns = range(5) if row % 2 == 0 else range(4, -1, -1)
        for column in columns:
            points.append((-60.0 + 30.0 * column, -95.0 + 38.0 * row))
    return tuple(points)


def build_program(settings):
    points = witness_points()
    if len(points) != 30:
        raise ValueError("pen-clear test must contain exactly 30 witness marks")
    lines = []

    def comment(text):
        lines.append("(%s)" % str(text).replace("(", "[").replace(")", "]"))

    comment("T-01H pen-clear no-drag diagnostic - 30 witness marks")
    comment("use ordinary paper at normal plotting height with the installed pen")
    comment("one initial Cycle Start; inspect every pen-up connector for ink")
    comment("travel feeds test slow, medium, and production-speed jogs")
    comment("run G65 P113 first and do not change G54/G92 during this test")
    lines.extend(["G21", "G90", "G94", "G17", "G54"])
    converter.append_custom_command(lines, settings.pen_up_command)
    converter.append_pen_dwell(
        lines,
        settings,
        "up",
        requires_transition=False,
    )

    first_pen_down = True
    for index, (x_value, y_value) in enumerate(points):
        if index == 0:
            comment("SLOW TRAVEL GROUP")
        elif index == 10:
            comment("MEDIUM TRAVEL GROUP")
        elif index == 20:
            comment("PRODUCTION-SPEED TRAVEL GROUP")
        travel_feed = 300.0 if index < 10 else 1000.0 if index < 20 else 3000.0
        lines.append(
            "G1 X%s Y%s A0 F%s (travel)"
            % (fmt(x_value), fmt(y_value), fmt(travel_feed))
        )
        converter.append_custom_command(lines, settings.pen_down_command)
        converter.append_pen_dwell(
            lines,
            settings,
            "down",
            is_first_down=first_pen_down,
        )
        first_pen_down = False
        lines.append(
            "G1 X%s Y%s A0 F420 (witness)"
            % (fmt(x_value + 6.0), fmt(y_value))
        )
        converter.append_custom_command(lines, settings.pen_up_command)
        converter.append_pen_dwell(lines, settings, "up")

    converter.append_full_retract(lines, settings)
    lines.append(converter.park_home_command(settings))
    lines.append("M2")
    return "\n".join(lines) + "\n", points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "gcode" / "pen-clear-no-drag-30.gcode"),
    )
    args = parser.parse_args()
    program, points = build_program(converter.Settings())
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(program, encoding="utf-8", newline="\n")
    print("wrote %s (%d witness marks)" % (output, len(points)))


if __name__ == "__main__":
    main()
