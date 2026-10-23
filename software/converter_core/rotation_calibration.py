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
import math
import re
from typing import Iterable, Sequence


DEFAULT_RATIO = 12.03324
DEFAULT_ANGLES = (90.0, 180.0, 270.0)
DEFAULT_SHEET_EDGE_MARGIN_MM = 0.0
DEFAULT_SHEET_DIAMETER_MM = 355.6  # 14 in round stock
DEFAULT_TEST_DIAMETER_MM = 330.2  # leave 1/2 in around a 14 in sheet


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
    arm_mm: float = 165.1,
    arm_step_mm: float = 5.0,
    angles: Sequence[float] = DEFAULT_ANGLES,
    control_passes: int = 1,
    closing: bool = True,
    sheet_diameter_mm: float = DEFAULT_SHEET_DIAMETER_MM,
    test_diameter_mm: float = DEFAULT_TEST_DIAMETER_MM,
    edge_margin_mm: float = DEFAULT_SHEET_EDGE_MARGIN_MM,
) -> tuple[str, tuple[tuple[str, float, float], ...]]:
    """Build a cross-replay program and return its pass manifest.

    Every pass draws a paper-frame cross centred at G54 X0/Y0. The A=0 cross is
    longest and carries +X/+Y arrowheads. Other passes are stepped shorter so
    each replay remains attributable where the crosses overlap.
    """
    arm_mm = float(arm_mm)
    arm_step_mm = float(arm_step_mm)
    sheet_diameter_mm = float(sheet_diameter_mm)
    test_diameter_mm = float(test_diameter_mm)
    edge_margin_mm = float(edge_margin_mm)
    angles = tuple(float(angle) % 360.0 for angle in angles)
    if arm_mm < 15.0:
        raise ValueError("reference arm must be at least 15 mm")
    if arm_step_mm <= 0.0:
        raise ValueError("arm step must be positive")
    if sheet_diameter_mm <= 0.0:
        raise ValueError("sheet diameter must be positive")
    if test_diameter_mm <= 0.0:
        raise ValueError("test diameter must be positive")
    if test_diameter_mm > sheet_diameter_mm:
        raise ValueError("test diameter cannot exceed the round sheet diameter")
    if edge_margin_mm < 0.0:
        raise ValueError("sheet edge margin cannot be negative")
    usable_radius = test_diameter_mm / 2.0 - edge_margin_mm
    if arm_mm > usable_radius:
        raise ValueError(
            "reference arm %.1f mm does not fit inside the %.1f mm test area "
            "with a %.1f mm edge margin"
            % (arm_mm, test_diameter_mm, edge_margin_mm)
        )
    if control_passes < 0:
        raise ValueError("control passes cannot be negative")
    if not angles and not closing and control_passes == 0:
        raise ValueError("the program must contain at least one replay")

    passes: list[tuple[str, float, float]] = []
    next_arm = arm_mm
    passes.append(("reference", 0.0, next_arm))
    for index in range(control_passes):
        next_arm -= arm_step_mm
        passes.append((f"control {index + 1}", 0.0, next_arm))
    for angle in angles:
        next_arm -= arm_step_mm
        passes.append((f"replay {_fmt(angle)}", angle, next_arm))
    if closing:
        next_arm -= arm_step_mm
        passes.append(("closing", 0.0, next_arm))
    if next_arm < 10.0:
        raise ValueError(
            "the shortest pass would have an arm under 10 mm; reduce arm step"
        )

    ratio = float(getattr(settings, "theta_drive_ratio", DEFAULT_RATIO))
    feed = float(getattr(settings, "feed_rate", 700.0))
    travel = float(getattr(settings, "travel_rate", 3000.0))
    lines = [
        "(rotation-centre cross calibration - make_rotation_center_calibration.py)",
        "(run G65 P113 first; every cross is centred on the freshly registered G54 X0 Y0)",
        "(layout: %s mm test on %s mm round stock, largest ink radius %s mm)"
        % (_fmt(test_diameter_mm), _fmt(sheet_diameter_mm), _fmt(arm_mm)),
        "(reference cross is longest and its arrowheads point machine +X and +Y)",
        "(the other crosses replay the same bed-frame cross at their labelled bed angles)",
        "(after the bed returns to A=0, measure each replay cross minus the reference cross)",
        "(positive DX/DY means the replay is toward the reference arrowheads)",
        "(longest to shortest crosses: %s)"
        % ", ".join(
            "%s %s mm" % (label, _fmt(2.0 * half))
            for label, _, half in passes
        ),
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

    for label, angle, half in passes:
        lines.append(
            "(%s cross: bed angle %s deg, arm %s mm)"
            % (label, _fmt(angle), _fmt(half))
        )
        draw_stroke(angle, [(-half, 0.0), (half, 0.0)])
        draw_stroke(angle, [(0.0, -half), (0.0, half)])

    reference_half = passes[0][2]
    arrow_back = min(4.0, reference_half * 0.03)
    arrow_side = arrow_back * 0.4
    lines.append("(reference +X and +Y arrowheads; the open end of each V is positive)")
    draw_stroke(
        0.0,
        [
            (reference_half, 0.0),
            (reference_half - arrow_back, arrow_side),
            (reference_half, 0.0),
            (reference_half - arrow_back, -arrow_side),
        ],
    )
    draw_stroke(
        0.0,
        [
            (0.0, reference_half),
            (arrow_side, reference_half - arrow_back),
            (0.0, reference_half),
            (-arrow_side, reference_half - arrow_back),
        ],
    )

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
    return program, tuple(passes)
