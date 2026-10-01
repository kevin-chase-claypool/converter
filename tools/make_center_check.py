"""Write a Cycle-Start program that proves G54 X0 Y0 is the bed's rotation axis.

Registration finds the embedded centre magnet, and G54 X0 Y0 is then written
from it plus the pen/TMAG offset. If the magnet is not exactly on the rotation
axis - or the offset is off - the registered origin sits that far from the axis,
and every drawing is displaced by the same amount.

This program draws a small cross at the registered origin, rotates the bed half
a revolution, and draws the same cross again at the same commanded position.

* Crosses on top of each other: the origin is on the rotation axis.
* Crosses separated: the separation is exactly **twice** the residual off-axis
  distance, and the direction of the separation is the direction of the error.

So it both proves the correction and measures any remainder. Run `P113` first -
the program assumes the freshly registered frame.

Usage::

    python tools\\make_center_check.py
    python tools\\make_center_check.py --arm 3.0 --out samples\\gcode\\center-check.gcode
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


def build_program(settings, arm):
    half_turn = settings.theta_drive_ratio * 180.0
    return "\n".join(
        [
            "(center registration check - is G54 X0 Y0 on the bed's rotation axis?)",
            "(run P113 first: this assumes the freshly registered frame)",
            f"(cross arm {arm:g} mm; half a bed revolution = {half_turn:.4f} A motor degrees)",
            "(crosses on top of each other = the origin is on the axis)",
            "(a gap is twice the residual off-axis error, in the gap's direction)",
            "G21",
            "G90",
            "G94",
            "G17",
            "G54",
            f"G0 F{fmt(settings.travel_rate)}",
            settings.pen_up_command,
            f"G4 P{fmt(settings.pen_up_ms / 1000.0)}",
            "G0 X0 Y0",
            settings.pen_down_command,
            f"G4 P{fmt(settings.pen_down_first_ms / 1000.0)}",
            f"G1 F{fmt(settings.feed_rate)}",
            f"G1 X{fmt(-arm / 2)} Y0",
            f"G1 X{fmt(arm / 2)} Y0",
            f"G1 X0 Y{fmt(-arm / 2)}",
            f"G1 X0 Y{fmt(arm / 2)}",
            settings.pen_up_command,
            f"G4 P{fmt(settings.pen_up_ms / 1000.0)}",
            "G91",
            f"G1 A{fmt(half_turn)} F{fmt(settings.theta_controller_limits.max_rate_deg_min)}",
            "G90",
            "G0 X0 Y0",
            settings.pen_down_command,
            f"G4 P{fmt(settings.pen_down_ms / 1000.0)}",
            f"G1 F{fmt(settings.feed_rate)}",
            f"G1 X{fmt(-arm / 2)} Y0",
            f"G1 X{fmt(arm / 2)} Y0",
            f"G1 X0 Y{fmt(-arm / 2)}",
            f"G1 X0 Y{fmt(arm / 2)}",
            settings.pen_up_command,
            f"G4 P{fmt(settings.pen_up_ms / 1000.0)}",
            "G91",
            f"G1 A{fmt(-half_turn)} F{fmt(settings.theta_controller_limits.max_rate_deg_min)}",
            "G90",
            f"G53 G0 X{fmt(settings.park_x_machine)} Y{fmt(settings.park_y_machine)} (park home)",
            "M2",
        ]
    ) + "\n"


def check_comments(program):
    for number, line in enumerate(program.splitlines(), 1):
        if line.count("(") != line.count(")"):
            raise ValueError(f"line {number} has an unbalanced comment: {line!r}")
        if "(" in line and not line.rstrip().endswith(")"):
            raise ValueError(f"line {number} wraps a comment or trails code: {line!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", type=float, default=4.0, help="cross arm in mm")
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "gcode" / "center-registration-check.gcode"),
    )
    args = parser.parse_args()

    settings = converter.Settings()
    program = build_program(settings, max(1.0, float(args.arm)))
    check_comments(program)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(program, encoding="utf-8", newline="\n")
    print(
        "wrote %s\n  cross arm %.1f mm, half turn %.4f A motor degrees (about %.1f s)"
        % (
            out,
            args.arm,
            settings.theta_drive_ratio * 180.0,
            (settings.theta_drive_ratio * 180.0)
            / settings.theta_controller_limits.max_rate_deg_min
            * 60.0,
        )
    )


if __name__ == "__main__":
    main()
