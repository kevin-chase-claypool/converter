"""Build the full-field, one-pen bed compensation calibration.

The standard sheet contains:

* a 37-station A=0 spatial lattice on rings at 50, 95, and 150 mm;
* four large sheet fiducials that remove photo scale/translation/rotation;
* one A=0 reference mark at every station;
* fixed-position 45/90/135/180/225/270/315 replays, each in its own
  10 mm-separated lane;
* a second A=0 lane as a control after the complete rotation sweep.

The `dense-91` layout keeps the same sheet and nine-angle protocol but uses
smaller L marks and tighter lanes to measure 91 stations at roughly 30 mm
neighbour spacing.

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
    CALIBRATION_LAYOUTS,
    STANDARD_LAYOUT,
    calibration_layout,
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


def build_program(
    settings,
    *,
    layout=STANDARD_LAYOUT,
    feed_rate=420.0,
    compensation=None,
    pass_dwell_seconds=None,
):
    layout = calibration_layout(layout)
    feed_rate = float(feed_rate)
    if not math.isfinite(feed_rate) or feed_rate <= 0.0:
        raise ValueError("feed rate must be finite and positive")
    if pass_dwell_seconds is not None:
        pass_dwell_seconds = float(pass_dwell_seconds)
        if not math.isfinite(pass_dwell_seconds) or pass_dwell_seconds < 0.0:
            raise ValueError("pass dwell must be finite and non-negative")
    stations = calibration_stations(layout)
    lines = []

    def comment(text):
        lines.append("(%s)" % str(text).replace("(", "[").replace(")", "]"))

    comment(
        "full-field bed compensation calibration v3 - %s"
        % layout.display_name
    )
    comment(
        "one 0.20 mm pen for all %d passes; do not swap or re-register"
        % len(layout.pass_specs)
    )
    comment("13 in planned field on 14 in round stock")
    comment(
        "pass angles at every station: "
        + ", ".join(
            "%g" % calibration_pass.angle_deg
            for calibration_pass in layout.pass_specs
            if calibration_pass.mark_kind.startswith("angle_")
        )
        + "; A0 controls are separate"
    )
    comment("station numbers are drawn in the A0 reference pass")
    if pass_dwell_seconds is None:
        comment("let each pass dry at the M0 pause, then Cycle Start")
    elif pass_dwell_seconds > 0.0:
        comment(
            "automatic %s s pass dwell; one initial Cycle Start"
            % fmt(pass_dwell_seconds)
        )
    else:
        comment("continuous pass changes; one initial Cycle Start")
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
        if pass_dwell_seconds is None:
            lines.append(
                "M0 (allow pass to dry; install same pen only if removed; "
                "%s next)" % next_pass.pass_name
            )
        elif pass_dwell_seconds > 0.0:
            lines.append(
                "G4 P%s (automatic pass dwell; %s next)"
                % (fmt(pass_dwell_seconds), next_pass.pass_name)
            )
        else:
            comment("%s next" % next_pass.pass_name)

    # The four large, asymmetric Ls define the sheet coordinate frame. They are
    # outside the 150 mm sampling radius but remain inside the 13-inch field.
    for number, angle_deg, x_mm, y_mm in fiducial_points(layout):
        comment("fiducial F%d" % number)
        draw_stroke(
            fiducial_mark_points(
                angle_deg,
                x_mm,
                y_mm,
                radial_arm_mm=layout.fiducial_radial_arm_mm,
                tangent_arm_mm=layout.fiducial_tangent_arm_mm,
            ),
            0.0,
        )

    for pass_index, calibration_pass in enumerate(layout.pass_specs):
        comment(
            "PASS %d/%d %s at A=%s deg"
            % (
                pass_index + 1,
                len(layout.pass_specs),
                calibration_pass.pass_name,
                fmt(calibration_pass.angle_deg),
            )
        )
        if calibration_pass.mark_kind == "reference":
            for station in stations:
                label_x, label_y = station_label_position(station, layout)
                for polyline in station_label_points(
                    station.station_id,
                    label_x,
                    label_y,
                    height_mm=layout.label_height_mm,
                ):
                    draw_stroke(polyline, 0.0)
        for station in stations:
            _target_x, _target_y, points = mark_geometry(
                station,
                calibration_pass,
                layout,
            )
            draw_stroke(points, calibration_pass.angle_deg)
        if pass_index < len(layout.pass_specs) - 1:
            pause_and_restore_reference(layout.pass_specs[pass_index + 1])

    converter.append_full_retract(lines, settings)
    lines.append(converter.park_home_command(settings))
    lines.append("M2")
    program = "\n".join(lines) + "\n"
    for number, line in enumerate(program.splitlines(), 1):
        if line.count("(") != line.count(")"):
            raise ValueError("unbalanced comment at generated line %d" % number)
    return program, stations


def layout_extent_mm(layout=STANDARD_LAYOUT):
    layout = calibration_layout(layout)
    maximum = 0.0
    for station in calibration_stations(layout):
        for calibration_pass in layout.pass_specs:
            _x_mm, _y_mm, points = mark_geometry(
                station,
                calibration_pass,
                layout,
            )
            maximum = max(maximum, *(math.hypot(*point) for point in points))
        label_x, label_y = station_label_position(station, layout)
        maximum = max(maximum, math.hypot(label_x, label_y) + 3.0)
    for _number, angle_deg, x_mm, y_mm in fiducial_points(layout):
        maximum = max(
            maximum,
            *(
                math.hypot(*point)
                for point in fiducial_mark_points(
                    angle_deg,
                    x_mm,
                    y_mm,
                    radial_arm_mm=layout.fiducial_radial_arm_mm,
                    tangent_arm_mm=layout.fiducial_tangent_arm_mm,
                )
            ),
        )
    return maximum


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=None,
    )
    parser.add_argument(
        "--measurement-out",
        default=None,
    )
    parser.add_argument(
        "--layout",
        choices=tuple(CALIBRATION_LAYOUTS),
        default=STANDARD_LAYOUT.layout_id,
        help="station density and mark footprint",
    )
    parser.add_argument("--feed", type=float, default=420.0)
    parser.add_argument(
        "--pass-dwell-seconds",
        type=float,
        default=None,
        help=(
            "replace manual M0 pass stops with this timed dwell; zero runs "
            "passes continuously"
        ),
    )
    parser.add_argument(
        "--compensation",
        default="",
        help="optional v2 profile; writes a compensated verification sheet",
    )
    args = parser.parse_args()

    settings = converter.Settings()
    layout = calibration_layout(args.layout)
    compensation = load_bed_compensation(args.compensation)
    stem = (
        "bed-error-verify"
        if compensation is not None
        else "bed-error-map"
    )
    if layout.layout_id != STANDARD_LAYOUT.layout_id:
        stem += "-" + layout.layout_id
    if args.pass_dwell_seconds is not None:
        stem += "-auto"
    if args.out is None:
        args.out = str(ROOT / "samples" / "gcode" / (stem + ".gcode"))
    if args.measurement_out is None:
        args.measurement_out = str(
            ROOT / "samples" / "gcode" / (stem + ".csv")
        )
    program, stations = build_program(
        settings,
        layout=layout,
        feed_rate=args.feed,
        compensation=compensation,
        pass_dwell_seconds=args.pass_dwell_seconds,
    )
    out = Path(args.out)
    measurement_out = Path(args.measurement_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    measurement_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(program, encoding="utf-8", newline="\n")
    measurement_out.write_text(
        measurement_template_csv(layout=layout),
        encoding="utf-8",
        newline="\n",
    )
    extent = layout_extent_mm(layout)
    if extent > layout.test_radius_mm:
        raise ValueError(
            "calibration ink extends to %.3f mm, outside the %.3f mm test radius"
            % (extent, layout.test_radius_mm)
        )
    print("wrote %s (%d lines)" % (out, len(program.splitlines())))
    print(
        "wrote %s (%d stations x %d passes plus 4 fiducials)"
        % (measurement_out, len(stations), len(layout.pass_specs))
    )
    print(
        "layout extent %.3f mm radius; test radius %.3f mm; sheet radius %.3f mm"
        % (extent, layout.test_radius_mm, 355.6 / 2.0)
    )
    if args.pass_dwell_seconds is None:
        print(
            "use one 0.20 mm pen for all passes; "
            "wait at every M0 before continuing"
        )
    elif args.pass_dwell_seconds > 0.0:
        print(
            "use one 0.20 mm pen for all passes; automatic %s s pass dwell"
            % fmt(args.pass_dwell_seconds)
        )
    else:
        print("use one 0.20 mm pen for all passes; continuous pass changes")
    if compensation is not None:
        print("verification compensation fingerprint %s" % compensation.fingerprint)


if __name__ == "__main__":
    main()
