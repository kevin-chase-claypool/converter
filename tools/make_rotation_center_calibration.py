"""Generate the rotating-bed centre-offset calibration pen test.

Run this after HOME + REGISTER. It draws a long reference cross at A=0 and
shorter replays of the same bed-frame cross at 90/180/270 degrees. The default
layout is 13 inches (330.2 mm) across on 14-inch (355.6 mm) round stock,
leaving 12.7 mm of clearance to the stock edge.
The bed returns to A=0, leaving each replay displaced by the residual
rotation-centre error. Read the horizontal gap between vertical arms as DX and
the vertical gap between horizontal arms as DY, both signed toward the
reference arrowheads.

Give those readings to ``tools\\fit_rotation_center.py``. It fits the physical
axis offset and prints replacement P100 axis-centre constants.

Usage::

    python tools\\make_rotation_center_calibration.py
    python tools\\make_rotation_center_calibration.py --angles 180
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter  # noqa: E402
from converter_core.rotation_calibration import (  # noqa: E402
    DEFAULT_ANGLES,
    DEFAULT_SHEET_DIAMETER_MM,
    DEFAULT_SHEET_EDGE_MARGIN_MM,
    DEFAULT_TEST_DIAMETER_MM,
    build_rotation_center_test_program,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "gcode" / "rotation-center-calibration.gcode"),
    )
    parser.add_argument(
        "--sheet-diameter",
        type=float,
        default=DEFAULT_SHEET_DIAMETER_MM,
        help="round stock diameter in mm (default 355.6, 14 in)",
    )
    parser.add_argument(
        "--test-diameter",
        type=float,
        default=DEFAULT_TEST_DIAMETER_MM,
        help="planned test footprint diameter in mm (default 330.2, 13 in)",
    )
    parser.add_argument(
        "--edge-margin",
        type=float,
        default=DEFAULT_SHEET_EDGE_MARGIN_MM,
        help="unused radius inside the planned test diameter in mm (default 0)",
    )
    parser.add_argument("--arm", type=float, default=165.1)
    parser.add_argument("--arm-step", type=float, default=5.0)
    parser.add_argument(
        "--angles",
        default=",".join(str(angle) for angle in DEFAULT_ANGLES),
        help="comma-separated replay angles (default 90,180,270)",
    )
    parser.add_argument("--control-passes", type=int, default=1)
    parser.add_argument("--closing", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    try:
        angles = tuple(
            float(part) for part in args.angles.split(",") if part.strip()
        )
        program, passes = build_rotation_center_test_program(
            converter.Settings(),
            arm_mm=args.arm,
            arm_step_mm=args.arm_step,
            angles=angles,
            control_passes=args.control_passes,
            closing=args.closing,
            sheet_diameter_mm=args.sheet_diameter,
            test_diameter_mm=args.test_diameter,
            edge_margin_mm=args.edge_margin,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(program, encoding="utf-8", newline="\n")
    print(f"wrote {out} ({len(program.splitlines())} lines)")
    print("crosses:", ", ".join(f"{name}@{angle:g}deg" for name, angle, _ in passes))
    print(
        "measure each replay relative to the longest reference cross; "
        "positive is toward the reference arrowheads"
    )
    print(
        "then: python tools\\fit_rotation_center.py "
        "--measurement 90,DX,DY --measurement 180,DX,DY "
        "--measurement 270,DX,DY"
    )


if __name__ == "__main__":
    main()
