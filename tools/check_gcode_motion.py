"""Pre-flight a saved G-code file against the A-axis guards the planner emits.

Everything here is measured from the file, not from the settings that produced
it, so one command answers two questions:

* was this program generated *before* the bed-step and A-rate guards existed?
* if it was generated now, does it actually obey them?

It reports the largest bed rotation inside one drawing move, the largest A rate
any move asks for, whether pen-up moves carry rotation as bare `G0` rapids, and
the worst commanded bed-path bow with the radius and strategy that caused it -
the number that explains a bulge on paper when the tolerance is coarse. It also
counts emitted moves that exceed the tolerance stated in the file header.

Usage::

    python tools\\check_gcode_motion.py samples\\gcode\\ben.gcode
    python tools\\check_gcode_motion.py samples\\gcode\\my-job.gcode --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter  # noqa: E402


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
    result = converter.analyse_file(args.gcode, settings)
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
    if result["over_tolerance"]:
        print(
            "  moves exceeding the %.3f mm tolerance: %d "
            "(the subdivision cap may have bound)"
            % (result["tolerance"], result["over_tolerance"])
        )
    if result["strategies"]:
        print(
            "  strategies: "
            + ", ".join("%s %d" % item for item in sorted(result["strategies"].items()))
        )
    if result["unwinds"]:
        print("  bed re-registrations (travel moves over 300 deg): %d" % result["unwinds"])

    problems = converter.preflight_problems(result)
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
