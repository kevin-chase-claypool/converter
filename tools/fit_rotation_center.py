"""Fit a residual rotation-centre offset from the cross-replay pen test.

Each measurement is ``ANGLE,GAP_X,GAP_Y`` in degrees and millimetres. The gaps
are the raw distances between the longer reference arms and shorter replay arms
at that station. The default 20 mm pair baseline is subtracted before fitting.
Supply 90/180/270 readings; a two-axis 180-degree reading is also sufficient.

The result is added to P100's existing axis-centre correction because the test
measures the residual left by the constants currently installed on the
controller. The tool prints replacement constants but does not silently edit
or flash firmware.

Usage::

    python tools\\fit_rotation_center.py ^
        --measurement 90,20.6,19.4 ^
        --measurement 180,20,18.8 ^
        --measurement 270,19.4,19.4
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

from converter_core.rotation_calibration import (  # noqa: E402
    corrected_axis_center,
    current_axis_center_correction,
    fit_rotation_center,
    parse_measurement,
    remove_pair_baseline,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--measurement",
        action="append",
        required=True,
        metavar="ANGLE,GAP_X,GAP_Y",
        help="raw reference-to-replay spans; repeat for each bed angle",
    )
    parser.add_argument(
        "--baseline-mm",
        type=float,
        default=20.0,
        help="nominal reference-to-replay gap in both axes (default 20)",
    )
    parser.add_argument(
        "--macro",
        default=str(ROOT / "firmware" / "grblhal" / "macros" / "P100.macro"),
    )
    parser.add_argument("--max-residual-mm", type=float, default=0.20)
    args = parser.parse_args()

    try:
        spans = [parse_measurement(value) for value in args.measurement]
        measurements = remove_pair_baseline(spans, args.baseline_mm)
        fit = fit_rotation_center(measurements)
        macro_text = Path(args.macro).read_text(encoding="utf-8")
        current_x, current_y = current_axis_center_correction(macro_text)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error

    suggested_x, suggested_y = corrected_axis_center(current_x, current_y, fit)
    print("rotation-centre fit")
    print(f"  measurements: {len(measurements)}")
    print(
        "  residual centre C: X %+.4f mm, Y %+.4f mm"
        % (fit.center_x_mm, fit.center_y_mm)
    )
    print(
        "  model residual: rms %.4f mm, max %.4f mm"
        % (fit.rms_error_mm, fit.max_error_mm)
    )
    for angle, predicted_x, predicted_y in fit.predictions:
        measured = next(
            item for item in spans if item.angle_deg % 360.0 == angle % 360.0
        )
        print(
            "  %6.1f deg: gaps %7.3f,%7.3f  predicted %7.3f,%7.3f"
            % (
                angle,
                measured.offset_x_mm,
                measured.offset_y_mm,
                predicted_x + args.baseline_mm,
                predicted_y + args.baseline_mm,
            )
        )
    print(f"  P100 current: X {current_x:.4f}, Y {current_y:.4f}")
    print("  P100 replacement:")
    print(f"#<axis_center_correction_x> = {suggested_x:.4f}")
    print(f"#<axis_center_correction_y> = {suggested_y:.4f}")
    if len(measurements) < 3:
        print(
            "  caution: fewer than three angles cannot test the centre model; "
            "use 90/180/270 for acceptance"
        )
    if fit.max_error_mm > max(0.0, float(args.max_residual_mm)):
        print(
            "  warning: the centre-offset model does not explain the readings "
            f"within {args.max_residual_mm:.3f} mm; do not apply these constants "
            "until the bed plane/runout is investigated"
        )


if __name__ == "__main__":
    main()
