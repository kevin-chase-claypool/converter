"""Generate the rotating-bed centre-offset calibration pen test.

Run this after HOME + REGISTER. It draws 12 balanced stations around 14-inch
round stock: three 0-degree controls and three replays each at 90/180/270
degrees. At each station a longer A=0 reference cross and a shorter replay cross
are separated by a known 20 mm baseline in both axes, so the wet strokes do not
overlap. Read the raw vertical-arm X gap as GAP_X and the raw horizontal-arm Y
gap as GAP_Y. The fitter subtracts the 20 mm baseline and recovers the signed
error at each location.

The planned test footprint is 13 inches (330.2 mm) on 14-inch (355.6 mm)
stock. The default station layout reaches a 154.0 mm radius, leaving 23.8 mm
to the stock edge. The G-code prints angle/replicate labels such as `0-1` and
`270-3`, a +X/+Y direction key, and an L-shaped fiducial beside every A=0
reference cross. It also writes a companion measurement CSV.

Usage::

    python tools\\make_rotation_center_calibration.py
    python tools\\make_rotation_center_calibration.py --baseline 24
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
    DEFAULT_CALIBRATION_REPLICATES,
    DEFAULT_SHEET_DIAMETER_MM,
    DEFAULT_SHEET_EDGE_MARGIN_MM,
    DEFAULT_TEST_DIAMETER_MM,
    build_rotation_center_test_program,
    measurement_template_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "gcode" / "rotation-center-calibration.gcode"),
    )
    parser.add_argument(
        "--measurement-out",
        default=str(ROOT / "samples" / "gcode" / "rotation-center-calibration.csv"),
        help="editable gap worksheet written beside the G-code",
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
    parser.add_argument("--arm", type=float, default=18.0)
    parser.add_argument("--replay-arm", type=float, default=15.0)
    parser.add_argument("--baseline", type=float, default=20.0)
    parser.add_argument("--station-offset", type=float, default=120.0)
    parser.add_argument(
        "--replicates",
        type=int,
        default=DEFAULT_CALIBRATION_REPLICATES,
        help="repeats per angle distributed around the bed (default 3)",
    )
    parser.add_argument(
        "--angles",
        default=",".join(str(angle) for angle in DEFAULT_ANGLES),
        help="comma-separated replay angles (default 90,180,270)",
    )
    args = parser.parse_args()

    try:
        angles = tuple(
            float(part) for part in args.angles.split(",") if part.strip()
        )
        program, stations = build_rotation_center_test_program(
            converter.Settings(),
            arm_mm=args.arm,
            replay_arm_mm=args.replay_arm,
            baseline_mm=args.baseline,
            station_offset_mm=args.station_offset,
            angles=angles,
            replicates=args.replicates,
            sheet_diameter_mm=args.sheet_diameter,
            test_diameter_mm=args.test_diameter,
            edge_margin_mm=args.edge_margin,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(program, encoding="utf-8", newline="\n")
    measurement_out = Path(args.measurement_out)
    measurement_out.parent.mkdir(parents=True, exist_ok=True)
    measurement_out.write_text(
        measurement_template_csv(stations),
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {out} ({len(program.splitlines())} lines)")
    print(f"wrote {measurement_out} (fill gap_x_mm and gap_y_mm)")
    print("stations:", len(stations))
    print(", ".join(f"{name}@{angle:g}deg" for name, angle, _x, _y in stations))
    print(
        "measure raw gap between the longer reference and shorter replay arms; "
        f"the nominal gap is {args.baseline:g} mm"
    )
    print(
        "then: python tools\\fit_rotation_center.py "
        f"--measurements-csv {measurement_out} --baseline-mm {args.baseline:g}"
    )


if __name__ == "__main__":
    main()
