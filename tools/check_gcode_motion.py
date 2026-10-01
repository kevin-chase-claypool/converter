"""Pre-flight a saved G-code file against the A-axis guards the planner emits.

Everything here is measured from the file, not from the settings that produced
it, so one command answers two questions:

* was this program generated *before* the bed-step and A-rate guards existed?
* if it was generated now, does it actually obey them?

It reports the largest bed rotation inside one drawing move, the largest A rate
any move asks for, whether pen-up moves carry rotation as bare `G0` rapids, and
the worst commanded bed-path bow with the radius and strategy that caused it -
the number that explains a bulge on paper when the tolerance is coarse.

Usage::

    python tools\\check_gcode_motion.py samples\\gcode\\ben.gcode
    python tools\\check_gcode_motion.py samples\\gcode\\my-job.gcode --strict
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter  # noqa: E402
from converter_core import kinematics  # noqa: E402


MOVE = re.compile(
    r"G([01])\s+X(-?[\d.]+)\s+Y(-?[\d.]+)(?:\s+A(-?[\d.]+))?(?:\s+F([\d.]+))?"
)
LABEL = re.compile(r"\(([a-z_ ]+)\)\s*$")


def analyse(path, settings):
    ratio = settings.theta_drive_ratio
    cap = float(getattr(settings, "theta_max_step_deg", kinematics.MAX_BED_STEP_DEG))
    rate_cap = settings.theta_controller_limits.max_rate_deg_min / 60.0

    drawing = travel = hold = 0
    strategies = {}
    worst_step = (0.0, 0)
    worst_rate = (0.0, 0)
    worst_deviation = (0.0, 0.0, 0, "")
    rapids_with_rotation = fed_rotations = unwinds = 0

    previous = None
    with open(path, encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            match = MOVE.match(line)
            if not match:
                continue
            kind, x, y, a, feed = match.groups()
            point = (float(x), float(y), float(a) if a is not None else None)
            label_match = LABEL.search(line.rstrip())
            label = label_match.group(1) if label_match else ""
            if label:
                strategies[label] = strategies.get(label, 0) + 1
                if label == "hold":
                    hold += 1
            # A pen-up move is either a `G0` or a fed re-registration labelled
            # `(travel)`; both carry the bed's whole-revolution unwinds, which are
            # allowed there and irrelevant to ink.
            is_travel = kind == "0" or label == "travel"
            if previous is not None and point[2] is not None and previous[2] is not None:
                delta = abs(point[2] - previous[2])
                if is_travel:
                    travel += 1
                    if delta > 1e-9:
                        if "(travel)" in line:
                            fed_rotations += 1
                        else:
                            rapids_with_rotation += 1
                    if delta > ratio * 300.0:
                        unwinds += 1
                else:
                    drawing += 1
                    if delta > worst_step[0]:
                        worst_step = (delta, number)
                    if delta > 1e-9 and feed:
                        xy = math.hypot(point[0] - previous[0], point[1] - previous[1])
                        seconds = (math.hypot(xy, delta) / float(feed)) * 60.0
                        if seconds > 0.0 and delta / seconds > worst_rate[0]:
                            worst_rate = (delta / seconds, number)
                if delta > 1e-9 and not is_travel:
                    deviation = kinematics._polar_move_deviation(
                        (previous[0], previous[1]),
                        (point[0], point[1]),
                        (0.0, 0.0),
                        previous[2] / ratio,
                        point[2] / ratio,
                    )
                    if deviation > worst_deviation[0]:
                        worst_deviation = (
                            deviation,
                            0.5
                            * (
                                math.hypot(previous[0], previous[1])
                                + math.hypot(point[0], point[1])
                            ),
                            number,
                            label or kind,
                        )
            previous = point

    return {
        "drawing": drawing,
        "travel": travel,
        "hold": hold,
        "strategies": strategies,
        "step": worst_step[0] / ratio,
        "step_line": worst_step[1],
        "rate": worst_rate[0],
        "rate_line": worst_rate[1],
        "deviation": worst_deviation,
        "rapids_with_rotation": rapids_with_rotation,
        "fed_rotations": fed_rotations,
        "unwinds": unwinds,
        "cap": cap,
        "rate_cap": rate_cap,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gcode")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero when the file does not meet the current guards",
    )
    args = parser.parse_args()

    settings = converter.Settings()
    result = analyse(args.gcode, settings)
    deviation, radius, line, label = result["deviation"]

    print("file: %s" % args.gcode)
    print(
        "  moves: %d drawing, %d travel (%d parked-bed moves)"
        % (result["drawing"], result["travel"], result["hold"])
    )
    print(
        "  largest bed rotation in one drawing move: %.2f deg (cap %.1f, line %d)"
        % (result["step"], result["cap"], result["step_line"])
    )
    print(
        "  largest A rate demanded: %.0f motor deg/s (limit %.0f, line %d)"
        % (result["rate"], result["rate_cap"], result["rate_line"])
    )
    print(
        "  pen-up moves carrying rotation: %d fed, %d as bare G0 rapids"
        % (result["fed_rotations"], result["rapids_with_rotation"])
    )
    print(
        "  worst commanded bed-path bow: %.3f mm at %.0f mm radius (line %d, %s)"
        % (deviation, radius, line, label or "draw")
    )
    if result["strategies"]:
        print(
            "  strategies: "
            + ", ".join("%s %d" % item for item in sorted(result["strategies"].items()))
        )
    if result["unwinds"]:
        print("  bed re-registrations (travel moves over 300 deg): %d" % result["unwinds"])

    problems = []
    if result["step"] > result["cap"] + 1e-6:
        problems.append(
            "a drawing move rotates %.1f deg, over the %.0f deg cap"
            % (result["step"], result["cap"])
        )
    if result["rate"] > result["rate_cap"] * 1.01:
        problems.append(
            "a move asks for %.0f motor deg/s, over the %.0f limit"
            % (result["rate"], result["rate_cap"])
        )
    if result["rapids_with_rotation"]:
        problems.append(
            "%d pen-up moves carry rotation as bare G0 rapids"
            % result["rapids_with_rotation"]
        )
    if problems:
        print("\nFAIL against the current guards:")
        for problem in problems:
            print("  - " + problem)
        if not result["hold"] and result["step"] > result["cap"]:
            print(
                "  (no parked-bed move appears at all, which usually means this file "
                "was written before the guard existed)"
            )
        return 1 if args.strict else 0

    print("\nPASS: within the bed-step cap, the A-rate limit, and no bare G0 rotation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
