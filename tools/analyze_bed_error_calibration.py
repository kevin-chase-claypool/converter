"""Turn a measured full-field calibration sheet into a compensation profile.

Measured coordinates may be in any rectified sheet coordinate system. The four
large fiducials fit and remove common scale, rotation, and translation before
the residual bed/A map is calculated. P100 still owns registration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

from converter_core.bed_calibration import analyze_measurements  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--measurements",
        default=str(ROOT / "samples" / "gcode" / "bed-error-map.csv"),
    )
    parser.add_argument(
        "--profile-out",
        default=str(ROOT / "samples" / "gcode" / "bed-error-compensation.json"),
    )
    parser.add_argument(
        "--report-out",
        default=str(ROOT / "samples" / "gcode" / "bed-error-analysis.json"),
    )
    parser.add_argument(
        "--bed-mesh",
        default="",
        help="optional bed_mesh_probe CSV with x,y,gap_mm columns",
    )
    parser.add_argument("--max-cross-validation-rms-mm", type=float, default=0.35)
    parser.add_argument("--max-cross-validation-error-mm", type=float, default=0.90)
    parser.add_argument("--minimum-improvement-pct", type=float, default=10.0)
    parser.add_argument(
        "--allow-high-residual",
        action="store_true",
        help="write the profile even when validation gates fail",
    )
    args = parser.parse_args()

    measurements_path = Path(args.measurements)
    try:
        measurements_csv = measurements_path.read_text(encoding="utf-8")
    except OSError as error:
        raise SystemExit("cannot read measurements: %s" % error) from error
    bed_mesh_csv = None
    if args.bed_mesh:
        try:
            bed_mesh_csv = Path(args.bed_mesh).read_text(encoding="utf-8")
        except OSError as error:
            raise SystemExit("cannot read bed mesh: %s" % error) from error

    profile, report, accepted = analyze_measurements(
        measurements_csv,
        bed_mesh_csv=bed_mesh_csv,
        source=measurements_path.name,
        max_cross_validation_rms_mm=args.max_cross_validation_rms_mm,
        max_cross_validation_error_mm=args.max_cross_validation_error_mm,
        minimum_improvement_pct=args.minimum_improvement_pct,
    )
    report_path = Path(args.report_out)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("wrote analysis %s" % report_path)
    print(
        "A0 spatial RMS %.3f mm / max %.3f mm"
        % (
            report["a0_spatial_error"]["rms_mm"],
            report["a0_spatial_error"]["max_mm"],
        )
    )
    print(
        "A0 control residual RMS %.3f mm / max %.3f mm"
        % (
            report["a0_control_residual"]["rms_mm"],
            report["a0_control_residual"]["max_mm"],
        )
    )
    print(
        "leave-one-out profile RMS %.3f mm / max %.3f mm; improvement %.1f%%"
        % (
            report["leave_one_out"]["rms_mm"],
            report["leave_one_out"]["max_mm"],
            report["leave_one_out"]["improvement_pct"],
        )
    )
    print(report["diagnosis"])
    if not accepted and not args.allow_high_residual:
        raise SystemExit(
            "profile validation gates failed; analysis was written but no "
            "planner profile was created (use --allow-high-residual only after "
            "reviewing the report)"
        )
    profile_path = Path(args.profile_out)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(profile.to_json(), encoding="utf-8", newline="\n")
    print(
        "wrote profile %s (fingerprint %s, max correction %.3f mm)"
        % (profile_path, profile.fingerprint, profile.max_correction_mm)
    )


if __name__ == "__main__":
    main()
