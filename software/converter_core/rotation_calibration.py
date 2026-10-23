"""Measure and fit the bed's residual rotation-centre offset.

The controller registers G54 X0/Y0 from the centre-magnet survey. If the true
rotation axis is a small vector ``C`` away from that origin, a bed-frame point
``p`` reaches the machine frame at

    m(theta) = C + R(theta) * (p - C)
             = R(theta) * p + e(theta)

At draw time the command ``R(theta) * p`` lands at ``C + R(theta) * (p - C)``.
After the bed returns to A=0, the bed point that was under the pen is displaced
from the intended reference by ``e(theta) = C - R(-theta) * C``; that returned
bed-frame displacement is what the pen test reads. The controller must own the
correction: P100 moves the registered origin onto the axis once, and the
converter keeps mapping every point about G54 zero. Applying the same offset
in the artwork planner would double-correct it.

The generated cross-replay program exposes ``e(theta)`` in machine X/Y. Fitting
the three quadrant measurements recovers the two-component centre vector, which
is added to P100's existing axis-centre constants.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import io
import math
import re
from typing import Iterable, Sequence


DEFAULT_RATIO = 12.03324
DEFAULT_ANGLES = (90.0, 180.0, 270.0)
DEFAULT_SHEET_EDGE_MARGIN_MM = 0.0
DEFAULT_SHEET_DIAMETER_MM = 355.6  # 14 in round stock
DEFAULT_TEST_DIAMETER_MM = 330.2  # leave 1/2 in around a 14 in sheet
DEFAULT_CALIBRATION_REPLICATES = 3


# A compact single-line stroke font for on-paper calibration labels.
_STROKE_GLYPHS = {
    "0": (((0.0, 1.0), (0.0, 4.0), (3.0, 4.0), (3.0, 1.0), (0.0, 1.0)),),
    "1": (((1.5, 1.0), (1.5, 4.0)),),
    "2": (
        ((0.0, 4.0), (3.0, 4.0), (3.0, 2.5), (0.0, 2.5), (0.0, 1.0), (3.0, 1.0)),
    ),
    "3": (
        ((0.0, 4.0), (3.0, 4.0), (3.0, 1.0), (0.0, 1.0)),
        ((1.0, 2.5), (3.0, 2.5)),
    ),
    "4": (
        ((0.0, 4.0), (0.0, 2.5), (3.0, 2.5)),
        ((3.0, 4.0), (3.0, 1.0)),
    ),
    "5": (
        ((3.0, 4.0), (0.0, 4.0), (0.0, 2.5), (3.0, 2.5), (3.0, 1.0), (0.0, 1.0)),
    ),
    "6": (
        ((3.0, 4.0), (0.0, 4.0), (0.0, 1.0), (3.0, 1.0), (3.0, 2.5), (0.0, 2.5)),
    ),
    "7": (((0.0, 4.0), (3.0, 4.0), (3.0, 1.0)),),
    "8": (
        ((0.0, 1.0), (0.0, 4.0), (3.0, 4.0), (3.0, 1.0), (0.0, 1.0)),
        ((0.0, 2.5), (3.0, 2.5)),
    ),
    "9": (
        ((3.0, 1.0), (3.0, 4.0), (0.0, 4.0), (0.0, 2.5), (3.0, 2.5)),
    ),
    "E": (
        ((3.0, 4.0), (0.0, 4.0), (0.0, 1.0), (3.0, 1.0)),
        ((0.0, 2.5), (2.2, 2.5)),
    ),
    "N": (((0.0, 1.0), (0.0, 4.0), (3.0, 1.0), (3.0, 4.0)),),
    "S": (
        ((3.0, 4.0), (0.0, 4.0), (0.0, 2.5), (3.0, 2.5), (3.0, 1.0), (0.0, 1.0)),
    ),
    "W": (((0.0, 4.0), (0.0, 1.0), (1.5, 3.0), (3.0, 1.0), (3.0, 4.0)),),
    "X": (
        ((0.0, 1.0), (3.0, 4.0)),
        ((0.0, 4.0), (3.0, 1.0)),
    ),
    "Y": (
        ((0.0, 4.0), (1.5, 2.5), (3.0, 4.0)),
        ((1.5, 2.5), (1.5, 1.0)),
    ),
    "+": (
        ((0.5, 2.5), (2.5, 2.5)),
        ((1.5, 1.5), (1.5, 3.5)),
    ),
    "-": (((0.5, 2.5), (2.5, 2.5)),),
}


@dataclass(frozen=True)
class RotationCenterMeasurement:
    angle_deg: float
    offset_x_mm: float
    offset_y_mm: float


@dataclass(frozen=True)
class RotationCenterFit:
    center_x_mm: float
    center_y_mm: float
    rms_error_mm: float
    max_error_mm: float
    predictions: tuple[tuple[float, float, float], ...]


def _fmt(value: float) -> str:
    if abs(value) < 1e-9:
        return "0"
    return ("%.4f" % value).rstrip("0").rstrip(".")


def center_error(
    angle_deg: float,
    center_x_mm: float,
    center_y_mm: float,
) -> tuple[float, float]:
    """Return the machine-frame shift caused by a centre offset at one angle."""
    angle = math.radians(-angle_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return (
        center_x_mm - (center_x_mm * cos_a - center_y_mm * sin_a),
        center_y_mm - (center_x_mm * sin_a + center_y_mm * cos_a),
    )


def fit_rotation_center(
    measurements: Iterable[RotationCenterMeasurement],
) -> RotationCenterFit:
    """Least-squares fit for ``e(theta) = C - R(-theta) * C``.

    A nonzero bed angle determines both centre components. The default
    90/180/270-degree set is overdetermined and exposes non-centre bed-shape
    errors as residual.
    """
    rows: list[tuple[float, float, float, float, RotationCenterMeasurement]] = []
    for measurement in measurements:
        angle = float(measurement.angle_deg) % 360.0
        rad = math.radians(-angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        # For rad = -theta:
        # e_x = cx*(1-cos(rad)) + cy*sin(rad)
        # e_y = -cx*sin(rad) + cy*(1-cos(rad))
        a11 = 1.0 - cos_a
        a12 = sin_a
        a21 = -sin_a
        a22 = 1.0 - cos_a
        rows.append(
            (
                a11,
                a12,
                a21,
                a22,
                RotationCenterMeasurement(
                    angle,
                    float(measurement.offset_x_mm),
                    float(measurement.offset_y_mm),
                ),
            )
        )
    if not rows:
        raise ValueError("at least one rotation-centre measurement is required")

    matrix_11 = sum(a11 * a11 + a21 * a21 for a11, _, a21, _, _ in rows)
    matrix_12 = sum(a11 * a12 + a21 * a22 for a11, a12, a21, a22, _ in rows)
    matrix_22 = sum(a12 * a12 + a22 * a22 for _, a12, _, a22, _ in rows)
    rhs_1 = sum(
        a11 * measurement.offset_x_mm + a21 * measurement.offset_y_mm
        for a11, _, a21, _, measurement in rows
    )
    rhs_2 = sum(
        a12 * measurement.offset_x_mm + a22 * measurement.offset_y_mm
        for _, a12, _, a22, measurement in rows
    )
    determinant = matrix_11 * matrix_22 - matrix_12 * matrix_12
    if abs(determinant) < 1e-12:
        raise ValueError(
            "measurements do not constrain both X and Y; include at least "
            "one nonzero bed angle"
        )

    center_x = (rhs_1 * matrix_22 - rhs_2 * matrix_12) / determinant
    center_y = (matrix_11 * rhs_2 - matrix_12 * rhs_1) / determinant
    predictions = []
    squared_errors = []
    for measurement in rows:
        measured = measurement[4]
        predicted_x, predicted_y = center_error(
            measured.angle_deg, center_x, center_y
        )
        predictions.append(
            (measured.angle_deg, predicted_x, predicted_y)
        )
        squared_errors.append(
            (predicted_x - measured.offset_x_mm) ** 2
            + (predicted_y - measured.offset_y_mm) ** 2
        )
    rms = math.sqrt(sum(squared_errors) / len(squared_errors))
    return RotationCenterFit(
        center_x_mm=center_x,
        center_y_mm=center_y,
        rms_error_mm=rms,
        max_error_mm=max(math.sqrt(value) for value in squared_errors),
        predictions=tuple(predictions),
    )


def parse_measurement(value: str) -> RotationCenterMeasurement:
    """Parse ``ANGLE,DX,DY`` in degrees and millimetres."""
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise ValueError("measurement must be ANGLE,DX,DY")
    try:
        angle, offset_x, offset_y = (float(part) for part in parts)
    except ValueError as error:
        raise ValueError("measurement values must be numeric") from error
    if not all(math.isfinite(item) for item in (angle, offset_x, offset_y)):
        raise ValueError("measurement values must be finite")
    return RotationCenterMeasurement(angle, offset_x, offset_y)


def remove_pair_baseline(
    measurements: Iterable[RotationCenterMeasurement],
    baseline_mm: float,
) -> tuple[RotationCenterMeasurement, ...]:
    """Convert raw reference-to-replay spans into centre-error vectors."""
    baseline_mm = float(baseline_mm)
    if baseline_mm < 0.0:
        raise ValueError("pair baseline cannot be negative")
    return tuple(
        RotationCenterMeasurement(
            measurement.angle_deg,
            measurement.offset_x_mm - baseline_mm,
            measurement.offset_y_mm - baseline_mm,
        )
        for measurement in measurements
    )


def remove_control_bias(
    measurements: Iterable[RotationCenterMeasurement],
) -> tuple[tuple[RotationCenterMeasurement, ...], tuple[float, float]]:
    """Subtract the mean A=0 control error from non-control measurements.

    Control rows constrain the measurement/frame bias but carry no centre
    information themselves, so they are removed from the fit after estimating
    that bias.
    """
    rows = tuple(measurements)
    controls = [
        item for item in rows if abs(item.angle_deg % 360.0) <= 1e-9
    ]
    if controls:
        bias_x = sum(item.offset_x_mm for item in controls) / len(controls)
        bias_y = sum(item.offset_y_mm for item in controls) / len(controls)
    else:
        bias_x = bias_y = 0.0
    corrected = tuple(
        RotationCenterMeasurement(
            item.angle_deg,
            item.offset_x_mm - bias_x,
            item.offset_y_mm - bias_y,
        )
        for item in rows
        if abs(item.angle_deg % 360.0) > 1e-9
    )
    return corrected, (bias_x, bias_y)


def parse_measurements_csv(text: str) -> tuple[RotationCenterMeasurement, ...]:
    """Parse the companion CSV; rows with blank gap fields are ignored."""
    reader = csv.DictReader(io.StringIO(text))
    required = ("angle_deg", "gap_x_mm", "gap_y_mm")
    if reader.fieldnames is None or not set(required).issubset(reader.fieldnames):
        raise ValueError(
            "measurement CSV needs angle_deg, gap_x_mm, and gap_y_mm columns"
        )
    measurements = []
    for row in reader:
        values = [str(row.get(name, "")).strip() for name in required]
        if not any(values[1:]):
            continue
        if not all(values):
            raise ValueError(
                "complete all gap fields or leave both gaps blank in every row"
            )
        measurements.append(parse_measurement(",".join(values)))
    if not measurements:
        raise ValueError("measurement CSV contains no completed rows")
    return tuple(measurements)


def measurement_template_csv(
    stations: Iterable[tuple[str, float, float, float]],
) -> str:
    """Return an editable companion CSV for the generated stations."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("station", "angle_deg", "gap_x_mm", "gap_y_mm"))
    for label, angle, _station_x, _station_y in stations:
        writer.writerow((label, _fmt(angle), "", ""))
    return output.getvalue()


def current_axis_center_correction(macro_text: str) -> tuple[float, float]:
    """Read P100's current numeric axis-centre correction."""
    values = []
    for name in ("axis_center_correction_x", "axis_center_correction_y"):
        match = re.search(
            rf"(?m)^#<{name}>\s*=\s*(-?\d+(?:\.\d+)?)\s*$",
            macro_text,
        )
        if not match:
            raise ValueError(f"P100 is missing a numeric {name} assignment")
        values.append(float(match.group(1)))
    return values[0], values[1]


def corrected_axis_center(
    current_x_mm: float,
    current_y_mm: float,
    fit: RotationCenterFit,
) -> tuple[float, float]:
    """Return the P100 constants that remove the measured residual centre."""
    return current_x_mm + fit.center_x_mm, current_y_mm + fit.center_y_mm


def _to_machine(
    bed_x: float,
    bed_y: float,
    theta_deg: float,
) -> tuple[float, float]:
    angle = math.radians(theta_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return bed_x * cos_a - bed_y * sin_a, bed_x * sin_a + bed_y * cos_a


def validate_program_comments(program: str) -> None:
    for number, line in enumerate(program.splitlines(), start=1):
        if line.count("(") != line.count(")"):
            raise ValueError(f"line {number} has an unbalanced comment: {line!r}")
        if "(" in line and not line.rstrip().endswith(")"):
            raise ValueError(f"line {number} does not end with its comment")


def build_rotation_center_test_program(
    settings,
    *,
    arm_mm: float = 18.0,
    replay_arm_mm: float = 15.0,
    baseline_mm: float = 20.0,
    station_offset_mm: float = 120.0,
    angles: Sequence[float] = DEFAULT_ANGLES,
    replicates: int = DEFAULT_CALIBRATION_REPLICATES,
    sheet_diameter_mm: float = DEFAULT_SHEET_DIAMETER_MM,
    test_diameter_mm: float = DEFAULT_TEST_DIAMETER_MM,
    edge_margin_mm: float = DEFAULT_SHEET_EDGE_MARGIN_MM,
) -> tuple[str, tuple[tuple[str, float, float, float], ...]]:
    """Build a spaced-pair rotation-centre calibration program.

    A balanced circular set of stations repeats each angle around the bed. At
    each station, a longer reference cross sits at the station origin and a
    shorter replay cross sits at ``baseline_mm, baseline_mm`` in the bed frame.
    The raw X gap between the vertical arms and Y gap between the horizontal
    arms therefore starts at the baseline instead of having wet lines overlap.
    """
    arm_mm = float(arm_mm)
    replay_arm_mm = float(replay_arm_mm)
    baseline_mm = float(baseline_mm)
    station_offset_mm = float(station_offset_mm)
    sheet_diameter_mm = float(sheet_diameter_mm)
    test_diameter_mm = float(test_diameter_mm)
    edge_margin_mm = float(edge_margin_mm)
    angles = tuple(float(angle) % 360.0 for angle in angles)
    if len(angles) != 3:
        raise ValueError("the calibration needs exactly 90, 180, and 270 degree replays")
    if replicates < 1 or replicates > 3:
        raise ValueError("replicates must be between 1 and 3")
    if arm_mm < 10.0:
        raise ValueError("reference arm must be at least 10 mm")
    if replay_arm_mm <= 0.0 or replay_arm_mm >= arm_mm:
        raise ValueError("replay arm must be positive and shorter than the reference")
    if baseline_mm < 8.0:
        raise ValueError("pair baseline must be at least 8 mm")
    if station_offset_mm <= arm_mm:
        raise ValueError("station offset must clear the reference cross")
    if sheet_diameter_mm <= 0.0:
        raise ValueError("sheet diameter must be positive")
    if test_diameter_mm <= 0.0:
        raise ValueError("test diameter must be positive")
    if test_diameter_mm > sheet_diameter_mm:
        raise ValueError("test diameter cannot exceed the round sheet diameter")
    if edge_margin_mm < 0.0:
        raise ValueError("sheet edge margin cannot be negative")
    usable_radius = test_diameter_mm / 2.0 - edge_margin_mm
    station_groups = (0.0, angles[0], angles[1], angles[2])
    column_x = (
        -0.75 * station_offset_mm,
        -0.25 * station_offset_mm,
        0.25 * station_offset_mm,
        0.75 * station_offset_mm,
    )
    row_spacing = 7.0 * station_offset_mm / 12.0
    row_y = tuple(
        (row - (replicates - 1) / 2.0) * row_spacing
        for row in range(replicates)
    )
    angle_grid = tuple(
        tuple(
            station_groups[(column_index + row_index) % len(station_groups)]
            for column_index in range(4)
        )
        for row_index in range(replicates)
    )
    stations = []
    for angle in station_groups:
        replicate = 0
        for row_index, row in enumerate(angle_grid):
            for column_index, value in enumerate(row):
                if value != angle:
                    continue
                replicate += 1
                stations.append(
                    (
                        "%s-%d" % (_fmt(angle), replicate),
                        angle,
                        column_x[column_index],
                        row_y[row_index],
                    )
                )
    station_count = len(stations)
    station_centres = tuple(
        (station_x, station_y)
        for _label, _angle, station_x, station_y in stations
    )
    pair_offsets = (
        (-arm_mm, 0.0),
        (arm_mm, 0.0),
        (0.0, -arm_mm),
        (0.0, arm_mm),
        (baseline_mm - replay_arm_mm, baseline_mm),
        (baseline_mm + replay_arm_mm, baseline_mm),
        (baseline_mm, baseline_mm - replay_arm_mm),
        (baseline_mm, baseline_mm + replay_arm_mm),
        (-arm_mm - 10.0, -arm_mm - 10.0),
        (-arm_mm - 10.0, -arm_mm - 4.0),
        (-arm_mm - 4.0, -arm_mm - 4.0),
    )
    label_centres = tuple(
        (station_x, station_y + arm_mm + 24.0)
        for _label, _angle, station_x, station_y in stations
    )
    direction_key = (0.0, -140.0)
    key_text_centres = (
        (direction_key[0] + 31.0, direction_key[1] - 8.0),
        (direction_key[0] - 8.0, direction_key[1] + 32.0),
    )
    pattern_radius = max(
        max(math.hypot(*label_centre) for label_centre in label_centres),
        max(math.hypot(*key_centre) for key_centre in key_text_centres),
        max(
            math.hypot(centre_x + offset_x, centre_y + offset_y)
            for centre_x, centre_y in station_centres
            for offset_x, offset_y in pair_offsets
        ),
    )
    if pattern_radius > usable_radius:
        raise ValueError(
            "pattern radius %.1f mm does not fit inside the %.1f mm test area"
            % (pattern_radius, usable_radius)
        )
    ratio = float(getattr(settings, "theta_drive_ratio", DEFAULT_RATIO))
    feed = float(getattr(settings, "feed_rate", 700.0))
    travel = float(getattr(settings, "travel_rate", 3000.0))
    lines = [
        "(rotation-centre cross calibration - make_rotation_center_calibration.py)",
        "(run G65 P113 first; G54 X0 Y0 is the freshly registered rotation origin)",
        "(layout: %s mm test on %s mm round stock, largest ink radius %s mm)"
        % (_fmt(test_diameter_mm), _fmt(sheet_diameter_mm), "%.1f" % pattern_radius),
        "(%d balanced stations repeat 0/90/180/270 degrees around the bed)" % station_count,
        "(each printed label is ANGLE-REPLICATE; its small L bracket marks the A=0 reference)",
        "(inside each station the LONGER cross is A=0; the SHORTER cross is the replay, +20,+20 mm)",
        "(measure raw vertical-arm X gap and horizontal-arm Y gap at each station)",
        "(the fitter subtracts the %s mm nominal gap from each reading)" % _fmt(baseline_mm),
        "G21",
        "G90",
        "G94",
        "G17",
        "G54",
        getattr(settings, "pen_up_command", "M5"),
        f"G4 P{_fmt(getattr(settings, 'pen_up_ms', 300.0) / 1000.0)}",
        "G65 P115 Q0 A1 W2",
    ]
    first_down = True
    previous_machine = (0.0, 0.0)
    previous_motor_theta = 0.0
    a_rate_cap = float(
        getattr(
            getattr(settings, "theta_controller_limits", None),
            "max_rate_deg_min",
            30000.0,
        )
    )

    def draw_stroke(theta_deg: float, points: Sequence[tuple[float, float]]) -> None:
        nonlocal first_down, previous_machine, previous_motor_theta
        machine = [_to_machine(x, y, theta_deg) for x, y in points]
        motor_a = theta_deg * ratio
        xy_length = math.hypot(
            machine[0][0] - previous_machine[0],
            machine[0][1] - previous_machine[1],
        )
        motor_delta = abs(motor_a - previous_motor_theta)
        duration_min = max(
            xy_length / max(travel, 1e-9),
            motor_delta / max(a_rate_cap, 1e-9),
        )
        travel_feed = math.hypot(xy_length, motor_delta) / max(
            duration_min, 1e-9
        )
        lines.append(
            "G1 X%s Y%s A%s F%s (travel)"
            % (
                _fmt(machine[0][0]),
                _fmt(machine[0][1]),
                _fmt(motor_a),
                _fmt(travel_feed),
            )
        )
        lines.append(getattr(settings, "pen_down_command", "M3"))
        lines.append(
            "G65 P115 Q1 B12 A1 W2"
            if first_down
            else "G65 P115 Q1 A1 W2"
        )
        first_down = False
        for index, (machine_x, machine_y) in enumerate(machine[1:]):
            feed_word = f" F{_fmt(feed)}" if index == 0 else ""
            lines.append(
                "G1 X%s Y%s A%s%s"
                % (
                    _fmt(machine_x),
                    _fmt(machine_y),
                    _fmt(motor_a),
                    feed_word,
                )
            )
        lines.append(getattr(settings, "pen_up_command", "M5"))
        lines.append("G65 P115 Q1 A1 W2")
        previous_machine = machine[-1]
        previous_motor_theta = motor_a

    def draw_text(
        text: str,
        centre_x: float,
        centre_y: float,
        height_mm: float = 7.0,
    ) -> None:
        scale = height_mm / 5.0
        spacing = 1.8
        char_width = 3.0 * scale
        total_width = len(text) * char_width + max(0, len(text) - 1) * spacing
        start_x = centre_x - total_width / 2.0
        base_y = centre_y - height_mm / 2.0
        lines.append("(label %s at %s,%s)" % (text, _fmt(centre_x), _fmt(centre_y)))
        for char_index, char in enumerate(text):
            glyph = _STROKE_GLYPHS.get(char)
            if glyph is None:
                raise ValueError("no calibration stroke glyph for %r" % char)
            char_x = start_x + char_index * (char_width + spacing)
            for polyline in glyph:
                draw_stroke(
                    0.0,
                    [
                        (char_x + x * scale, base_y + y * scale)
                        for x, y in polyline
                    ],
                )

    for label, angle, station_x, station_y in stations:
        lines.append(
            "(%s station: bed angle %s deg, reference arm %s mm)"
            % (label, _fmt(angle), _fmt(arm_mm))
        )
        draw_stroke(
            0.0,
            [
                (station_x - arm_mm, station_y),
                (station_x + arm_mm, station_y),
            ],
        )
        draw_stroke(
            0.0,
            [
                (station_x, station_y - arm_mm),
                (station_x, station_y + arm_mm),
            ],
        )
        fiducial_x = station_x - arm_mm - 10.0
        fiducial_y = station_y - arm_mm - 10.0
        draw_stroke(
            0.0,
            [
                (fiducial_x, fiducial_y),
                (fiducial_x, fiducial_y + 6.0),
                (fiducial_x + 6.0, fiducial_y + 6.0),
            ],
        )
        replay_x = station_x + baseline_mm
        replay_y = station_y + baseline_mm
        draw_stroke(
            angle,
            [
                (replay_x - replay_arm_mm, replay_y),
                (replay_x + replay_arm_mm, replay_y),
            ],
        )
        draw_stroke(
            angle,
            [
                (replay_x, replay_y - replay_arm_mm),
                (replay_x, replay_y + replay_arm_mm),
            ],
        )
    for (label, _angle, _station_x, _station_y), (label_x, label_y) in zip(
        stations, label_centres
    ):
        draw_text(label, label_x, label_y, height_mm=5.2)

    arrow_length = 18.0
    arrow_back = 3.0
    arrow_side = arrow_back * 0.4
    lines.append("(lower-centre direction key: arrow open ends point machine +X and +Y)")
    draw_stroke(
        0.0,
        [
            direction_key,
            (direction_key[0] + arrow_length, direction_key[1]),
            (direction_key[0] + arrow_length - arrow_back, direction_key[1] + arrow_side),
            (direction_key[0] + arrow_length, direction_key[1]),
            (direction_key[0] + arrow_length - arrow_back, direction_key[1] - arrow_side),
        ],
    )
    draw_stroke(
        0.0,
        [
            direction_key,
            (direction_key[0], direction_key[1] + arrow_length),
            (direction_key[0] + arrow_side, direction_key[1] + arrow_length - arrow_back),
            (direction_key[0], direction_key[1] + arrow_length),
            (direction_key[0] - arrow_side, direction_key[1] + arrow_length - arrow_back),
        ],
    )
    draw_text("+X", *key_text_centres[0], height_mm=5.0)
    draw_text("+Y", *key_text_centres[1], height_mm=5.0)

    lines.extend(
        [
            "M65 P0",
            "G65 P115 Q0 A3 W1",
            "M64 P0",
            "G53 G1 X%s Y%s F%s (park home)"
            % (
                _fmt(getattr(settings, "park_x_machine", -10.0)),
                _fmt(getattr(settings, "park_y_machine", -436.0)),
                _fmt(travel),
            ),
            "M2",
        ]
    )
    program = "\n".join(lines) + "\n"
    validate_program_comments(program)
    return program, stations
