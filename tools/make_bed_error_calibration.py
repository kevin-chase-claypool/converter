"""Build the full-field, one-pen bed compensation calibration.

The sheet contains:

* a 37-station A=0 spatial lattice on rings at 50, 95, and 150 mm;
* four large sheet fiducials that remove photo scale/translation/rotation;
* one A=0 reference mark at every station;
* fixed-position 45/90/135/180/225/270/315 replays, each in its own
  10 mm-separated lane;
* a second A=0 lane as a control after the complete rotation sweep.

Use one Pigma Micron 005 (or another 0.20 mm pen) for all nine passes. The
separated lanes remove loose-registration error from the measurement, and the
program pauses after each pass so the ink can dry without swapping the pen.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter  # noqa: E402
from converter_core.bed_calibration import (  # noqa: E402
    PASS_SPECS,
    TEST_DIAMETER_MM,
    calibration_stations,
    fiducial_mark_points,
    fiducial_points,
    mark_geometry,
    measurement_template_csv,
    station_label_position,
    station_label_points,
)
from converter_core.bed_compensation import (  # noqa: E402
    load_bed_compensation,
)


def fmt(value: float) -> str:
    return converter.format_float(float(value))


def to_machine(point, angle_deg, compensation=None):
    if compensation is not None:
        return converter.compensated_machine_point(
            point, angle_deg, (0.0, 0.0), compensation
        )
    angle = math.radians(angle_deg)
    cosine, sine = math.cos(angle), math.sin(angle)
    return (
        point[0] * cosine - point[1] * sine,
        point[0] * sine + point[1] * cosine,
    )


def build_program(settings, *, feed_rate=420.0, compensation=None):
    feed_rate = float(feed_rate)
    if not math.isfinite(feed_rate) or feed_rate <= 0.0:
        raise ValueError("feed rate must be finite and positive")
    stations = calibration_stations()
    lines = []

    def comment(text):
        lines.append("(%s)" % str(text).replace("(", "[").replace(")", "]"))

    comment("full-field bed compensation calibration v3")
    comment(
        "one 0.20 mm pen for all %d passes; do not swap or re-register"
        % len(PASS_SPECS)
    )
    comment("13 in planned field on 14 in round stock")
    comment(
        "pass angles at every station: "
        + ", ".join(
            "%g" % calibration_pass.angle_deg
            for calibration_pass in PASS_SPECS
            if calibration_pass.mark_kind.startswith("angle_")
        )
        + "; A0 controls are separate"
    )
    comment("station numbers are drawn in the A0 reference pass")
    comment("let each pass dry at the M0 pause, then Cycle Start")
    comment("run G65 P113 first and do not change G54/G92 during this sheet")
    if compensation is not None:
        comment(
            "verification pass with bed compensation %s"
            % compensation.fingerprint
        )
        comment("angular interpolation bed-frame")
    lines.extend(["G21", "G90", "G94", "G17", "G54"])
    converter.append_custom_command(lines, settings.pen_up_command)
    converter.append_pen_dwell(
        lines, settings, "up", requires_transition=False
    )

    current_machine = (0.0, 0.0)
    current_theta = 0.0
    first_pen_down = True

    def travel(point, angle_deg):
        nonlocal current_machine, current_theta
        target = to_machine(point, angle_deg, compensation)
        xy_length = math.hypot(
            target[0] - current_machine[0], target[1] - current_machine[1]
        )
        motor_delta = abs(angle_deg - current_theta) * settings.theta_drive_ratio
        plan = converter.plan_travel_move(settings, xy_length, motor_delta)
        lines.append(
            "G1 X%s Y%s A%s F%s (travel)"
            % (
                fmt(target[0]),
                fmt(target[1]),
                fmt(angle_deg * settings.theta_drive_ratio),
                fmt(plan["feed_rate"]),
            )
        )
        current_machine = target
        current_theta = angle_deg

    def draw_stroke(points, angle_deg):
        nonlocal current_machine, current_theta, first_pen_down
        if len(points) < 2:
            raise ValueError("a calibration stroke needs at least two points")
        machine = [
            to_machine(point, angle_deg, compensation) for point in points
        ]
        travel(points[0], angle_deg)
        converter.append_custom_command(lines, settings.pen_down_command)
        converter.append_pen_dwell(
            lines,
            settings,
            "down",
            is_first_down=first_pen_down,
        )
        first_pen_down = False
        for index, (x_machine, y_machine) in enumerate(machine[1:]):
            feed_text = " F%s" % fmt(feed_rate) if index == 0 else ""
            lines.append(
                "G1 X%s Y%s A%s%s"
                % (
                    fmt(x_machine),
                    fmt(y_machine),
                    fmt(angle_deg * settings.theta_drive_ratio),
                    feed_text,
                )
            )
        converter.append_custom_command(lines, settings.pen_up_command)
        converter.append_pen_dwell(lines, settings, "up")
        current_machine = machine[-1]
        current_theta = angle_deg

    def pause_and_restore_reference(next_pass):
        travel((0.0, 0.0), 0.0)
        lines.append(
            "M0 (allow pass to dry; install same pen only if removed; %s next)"
            % next_pass.pass_name
        )

    # The four large, asymmetric Ls define the sheet coordinate frame. They are
    # outside the 150 mm sampling radius but remain inside the 13-inch field.
    for number, angle_deg, x_mm, y_mm in fiducial_points():
        comment("fiducial F%d" % number)
        draw_stroke(fiducial_mark_points(angle_deg, x_mm, y_mm), 0.0)

    for pass_index, calibration_pass in enumerate(PASS_SPECS):
        comment(
            "PASS %d/%d %s at A=%s deg"
            % (
                pass_index + 1,
                len(PASS_SPECS),
                calibration_pass.pass_name,
                fmt(calibration_pass.angle_deg),
            )
        )
        if calibration_pass.mark_kind == "reference":
            for station in stations:
                label_x, label_y = station_label_position(station)
                for polyline in station_label_points(
                    station.station_id, label_x, label_y
                ):
                    draw_stroke(polyline, 0.0)
        for station in stations:
            _target_x, _target_y, points = mark_geometry(
                station, calibration_pass
            )
            draw_stroke(points, calibration_pass.angle_deg)
        if pass_index < len(PASS_SPECS) - 1:
            pause_and_restore_reference(PASS_SPECS[pass_index + 1])

    converter.append_full_retract(lines, settings)
    lines.append(converter.park_home_command(settings))
    lines.append("M2")
    program = "\n".join(lines) + "\n"
    for number, line in enumerate(program.splitlines(), 1):
        if line.count("(") != line.count(")"):
            raise ValueError("unbalanced comment at generated line %d" % number)
    return program, stations


def layout_extent_mm():
    maximum = 0.0
    for station in calibration_stations():
        for calibration_pass in PASS_SPECS:
            _x_mm, _y_mm, points = mark_geometry(station, calibration_pass)
            maximum = max(maximum, *(math.hypot(*point) for point in points))
        label_x, label_y = station_label_position(station)
        maximum = max(maximum, math.hypot(label_x, label_y) + 3.0)
    for _number, angle_deg, x_mm, y_mm in fiducial_points():
        maximum = max(
            maximum,
            *(
                math.hypot(*point)
                for point in fiducial_mark_points(angle_deg, x_mm, y_mm)
            ),
        )
    return maximum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "gcode" / "bed-error-map.gcode"),
    )
    parser.add_argument(
        "--measurement-out",
        default=str(ROOT / "samples" / "gcode" / "bed-error-map.csv"),
    )
    parser.add_argument("--feed", type=float, default=420.0)
    parser.add_argument(
        "--compensation",
        default="",
        help="optional v2 profile; writes a compensated verification sheet",
    )
    args = parser.parse_args()

    settings = converter.Settings()
    compensation = load_bed_compensation(args.compensation)
    out_default = str(ROOT / "samples" / "gcode" / "bed-error-map.gcode")
    measurement_default = str(
        ROOT / "samples" / "gcode" / "bed-error-map.csv"
    )
    if compensation is not None:
        if args.out == out_default:
            args.out = str(
                ROOT / "samples" / "gcode" / "bed-error-verify.gcode"
            )
        if args.measurement_out == measurement_default:
            args.measurement_out = str(
                ROOT / "samples" / "gcode" / "bed-error-verify.csv"
            )
    program, stations = build_program(
        settings,
        feed_rate=args.feed,
        compensation=compensation,
    )
    out = Path(args.out)
    measurement_out = Path(args.measurement_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    measurement_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(program, encoding="utf-8", newline="\n")
    measurement_out.write_text(
        measurement_template_csv(), encoding="utf-8", newline="\n"
    )
    extent = layout_extent_mm()
    if extent > TEST_DIAMETER_MM / 2.0:
        raise ValueError(
            "calibration ink extends to %.3f mm, outside the %.3f mm test radius"
            % (extent, TEST_DIAMETER_MM / 2.0)
        )
    print("wrote %s (%d lines)" % (out, len(program.splitlines())))
    print(
        "wrote %s (%d stations x %d passes plus 4 fiducials)"
        % (measurement_out, len(stations), len(PASS_SPECS))
    )
    print(
        "layout extent %.3f mm radius; test radius %.3f mm; sheet radius %.3f mm"
        % (extent, TEST_DIAMETER_MM / 2.0, 355.6 / 2.0)
    )
    print("use one 0.20 mm pen for all passes; wait at every M0 before continuing")
    if compensation is not None:
        print("verification compensation fingerprint %s" % compensation.fingerprint)


if __name__ == "__main__":
    main()
