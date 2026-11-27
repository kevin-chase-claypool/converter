"""Pointwise software-registration audit for a CMYK G-code set.

The audit reconstructs the bed-frame location of stable registration marks
from the final emitted ``G1`` machine coordinates and their ``A`` values. It
then removes the configured host bed compensation and each ink's declared pen
offset before comparing the recovered marks. This is software geometry
evidence only; it does not measure ink on paper.
"""

from __future__ import annotations

import math
import re

from .bed_compensation import (
    load_bed_compensation,
    row_locked_bed_compensation_set,
)
from .cmyk import SCREEN_ANGLES_DEG
from .motion_check import (
    MOVE,
    gcode_program_identity,
    validate_program_set_identity,
)


REGISTRATION_TOLERANCE_MM = 0.10
REGISTRATION_RMS_TOLERANCE_MM = 0.05
MIN_REGISTRATION_MARKS = 4

REGISTRATION_MARK = re.compile(
    r"^\(registration mark id=([A-Za-z0-9_.-]+) "
    r"arm=([A-Za-z0-9_.-]+) "
    r"center=(-?[\d.]+),(-?[\d.]+) "
    r"offset=(-?[\d.]+),(-?[\d.]+) mm\)$"
)
THETA_RATIO_HEADER = re.compile(
    r"^\(theta ratio ([\d.]+) motor deg per bed deg, "
    r"offset (-?[\d.]+)\)$",
    re.MULTILINE,
)


def _mean(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _rotate(point, angle_deg):
    angle = math.radians(float(angle_deg))
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return (
        point[0] * cosine - point[1] * sine,
        point[0] * sine + point[1] * cosine,
    )


def _distance(first, second):
    return math.hypot(first[0] - second[0], first[1] - second[1])


def _rounded_point(point):
    return [round(float(point[0]), 6), round(float(point[1]), 6)]


def _inverse_compensated_point(machine, theta_deg, profile):
    """Invert ``machine = R(theta) * bed + correction(theta, bed)``."""
    if profile is None or bool(getattr(profile, "identity", False)):
        return _rotate(machine, -float(theta_deg))
    bed = _rotate(machine, -float(theta_deg))
    for _iteration in range(40):
        correction = profile.correction(
            float(theta_deg),
            bed[0],
            bed[1],
        )
        candidate = _rotate(
            (
                machine[0] - correction[0],
                machine[1] - correction[1],
            ),
            -float(theta_deg),
        )
        if _distance(candidate, bed) <= 1e-10:
            return candidate
        bed = candidate
    raise ValueError(
        "compensation inversion did not converge at %.6f,%.6f mm"
        % (machine[0], machine[1])
    )


def _parse_registration_arms(
    text,
    profile,
    channel,
    row_angle_deg,
):
    theta_match = THETA_RATIO_HEADER.search(text)
    if theta_match is None:
        raise ValueError("the emitted G-code has no theta-ratio identity")
    theta_ratio = float(theta_match.group(1))
    body = profile
    current = None
    pen_down = False
    previous = None
    draw_points = []
    arms = {}
    errors = []

    def finish_arm():
        nonlocal current, draw_points
        if not current or len(draw_points) < 2:
            return
        channel_profile = body
        recovered = []
        try:
            for machine_x, machine_y, motor_a in (
                draw_points[0],
                draw_points[-1],
            ):
                recovered.append(
                    _inverse_compensated_point(
                        (machine_x, machine_y),
                        motor_a / theta_ratio,
                        channel_profile,
                    )
                )
        except (ValueError, OverflowError) as error:
            errors.append(
                "%s marker %s/%s could not be recovered: %s"
                % (
                    current["channel"],
                    current["mark_id"],
                    current["arm"],
                    error,
                )
            )
            current = None
            draw_points = []
            return
        center = (
            0.5 * (recovered[0][0] + recovered[-1][0]),
            0.5 * (recovered[0][1] + recovered[-1][1]),
        )
        key = (current["mark_id"], current["arm"])
        if key in arms:
            errors.append(
                "%s repeats registration mark %s/%s"
                % (current["channel"], key[0], key[1])
            )
        else:
            arms[key] = {
                **current,
                "center_mm": center,
                "endpoints_mm": recovered,
                "line_number": current["line_number"],
            }
        current = None
        draw_points = []

    last_a = None
    for number, line in enumerate(str(text).splitlines(), 1):
        stripped = line.strip()
        mark_match = REGISTRATION_MARK.match(stripped)
        if mark_match is not None:
            if current is not None:
                finish_arm()
            current = {
                "mark_id": mark_match.group(1),
                "arm": mark_match.group(2),
                "channel": channel,
                "expected_center_mm": (
                    float(mark_match.group(3)),
                    float(mark_match.group(4)),
                ),
                "pen_offset_mm": (
                    float(mark_match.group(5)),
                    float(mark_match.group(6)),
                ),
                "row_angle_deg": row_angle_deg,
                "line_number": number,
            }
            pen_down = False
            previous = None
            draw_points = []
            continue
        if stripped.startswith("M3"):
            pen_down = True
            draw_points = [previous] if previous is not None else []
            continue
        if stripped.startswith("M5"):
            if current is not None:
                finish_arm()
            pen_down = False
            continue
        match = MOVE.match(line)
        if not match:
            continue
        kind, x_text, y_text, a_text, _feed_text = match.groups()
        if a_text is not None:
            last_a = float(a_text)
        point = (
            float(x_text),
            float(y_text),
            last_a,
        )
        previous = point
        if pen_down and current is not None and kind == "1":
            draw_points.append(point)
    if current is not None:
        finish_arm()
    return arms, theta_ratio, errors


def _registration_marks_for_channel(programs, settings):
    paths = {}
    try:
        path = str(getattr(settings, "bed_compensation_path", "") or "")
        profile = load_bed_compensation(path)
    except (OSError, ValueError) as error:
        return {}, [str(error)]
    errors = []
    row_lock_set = None
    if (
        profile is not None
        and bool(getattr(settings, "row_locked_compensation", False))
    ):
        bed_angle = None
        if str(getattr(settings, "theta_mode", "")).strip().lower() == "fixed":
            bed_angle = float(getattr(settings, "theta_offset", 0.0))
        row_lock_set = row_locked_bed_compensation_set(
            profile,
            tuple(SCREEN_ANGLES_DEG.values()),
            bed_angle_deg=bed_angle,
        )
    for channel, text in programs.items():
        identity = gcode_program_identity(text)
        row_angle = identity.get("row_angle_deg")
        if row_angle is None:
            row_angle = SCREEN_ANGLES_DEG.get(channel, 0.0)
        channel_profile = (
            row_lock_set.for_screen_angle(float(row_angle))
            if row_lock_set is not None
            else profile
        )
        try:
            arms, _ratio, channel_errors = _parse_registration_arms(
                text,
                channel_profile,
                channel,
                row_angle,
            )
        except ValueError as error:
            arms = {}
            channel_errors = [str(error)]
        errors.extend(channel_errors)
        paths[channel] = arms
    return paths, errors


def _marks_from_arms(arms):
    grouped = {}
    for (mark_id, arm_name), arm in arms.items():
        record = grouped.setdefault(
            mark_id,
            {
                "arms": {},
                "observed_points": [],
                "expected_centers": [],
                "pen_offsets": [],
            },
        )
        record["arms"][arm_name] = {
            "center_mm": _rounded_point(arm["center_mm"]),
            "endpoints_mm": [
                _rounded_point(point)
                for point in arm["endpoints_mm"]
            ],
        }
        record["observed_points"].append(arm["center_mm"])
        record["expected_centers"].append(arm["expected_center_mm"])
        record["pen_offsets"].append(arm["pen_offset_mm"])
    marks = {}
    errors = []
    for mark_id, record in grouped.items():
        if set(record["arms"]) != {"horizontal", "vertical"}:
            errors.append(
                "registration mark %s does not have both horizontal and "
                "vertical arms" % mark_id
            )
            continue
        expected_center = record["expected_centers"][0]
        pen_offset = record["pen_offsets"][0]
        if any(
            _distance(value, expected_center) > 1e-6
            for value in record["expected_centers"]
        ):
            errors.append(
                "registration mark %s arms declare different centers"
                % mark_id
            )
        if any(
            _distance(value, pen_offset) > 1e-6
            for value in record["pen_offsets"]
        ):
            errors.append(
                "registration mark %s arms declare different pen offsets"
                % mark_id
            )
        observed = (
            _mean(point[0] for point in record["observed_points"]),
            _mean(point[1] for point in record["observed_points"]),
        )
        marks[mark_id] = {
            "observed_center_mm": observed,
            "expected_center_mm": expected_center,
            "pen_offset_mm": pen_offset,
            "arms": record["arms"],
        }
    return marks, errors


def _similarity_metrics(reference_points, points):
    reference_centroid = (
        _mean(point[0] for point in reference_points),
        _mean(point[1] for point in reference_points),
    )
    centroid = (
        _mean(point[0] for point in points),
        _mean(point[1] for point in points),
    )
    denominator = 0.0
    dot = 0.0
    cross = 0.0
    for reference, point in zip(reference_points, points):
        reference_x = reference[0] - reference_centroid[0]
        reference_y = reference[1] - reference_centroid[1]
        point_x = point[0] - centroid[0]
        point_y = point[1] - centroid[1]
        denominator += reference_x * reference_x + reference_y * reference_y
        dot += reference_x * point_x + reference_y * point_y
        cross += reference_x * point_y - reference_y * point_x
    if denominator <= 1e-12:
        scale = 1.0
        rotation_deg = 0.0
    else:
        cosine_term = dot / denominator
        sine_term = cross / denominator
        scale = math.hypot(cosine_term, sine_term)
        rotation_deg = math.degrees(math.atan2(sine_term, cosine_term))
    fitted = [
        (
            centroid[0]
            + scale
            * (
                math.cos(math.radians(rotation_deg))
                * (reference[0] - reference_centroid[0])
                - math.sin(math.radians(rotation_deg))
                * (reference[1] - reference_centroid[1])
            ),
            centroid[1]
            + scale
            * (
                math.sin(math.radians(rotation_deg))
                * (reference[0] - reference_centroid[0])
                + math.cos(math.radians(rotation_deg))
                * (reference[1] - reference_centroid[1])
            ),
        )
        for reference in reference_points
    ]
    residuals = [
        _distance(point, fit) for point, fit in zip(points, fitted)
    ]
    return {
        "centroid_mm": centroid,
        "translation_mm": (
            centroid[0] - reference_centroid[0],
            centroid[1] - reference_centroid[1],
        ),
        "rotation_deg": rotation_deg,
        "scale": scale,
        "similarity_rms_mm": math.sqrt(
            _mean(value * value for value in residuals)
        ),
        "similarity_max_mm": max(residuals, default=0.0),
    }


def audit_cmyk_gcode_registration(
    programs,
    settings,
    expected_pen_offsets_mm=None,
):
    """Compare recovered registration geometry from final G-code text."""
    programs = {
        str(channel): str(text)
        for channel, text in dict(programs).items()
    }
    errors = []
    if expected_pen_offsets_mm is None:
        expected_pen_offsets_mm = getattr(
            settings,
            "registration_pen_offsets_mm",
            None,
        )
    expected_offsets = {
        str(channel): (
            float(value[0]),
            float(value[1]),
        )
        for channel, value in dict(
            expected_pen_offsets_mm or {}
        ).items()
    }
    arms_by_channel, parse_errors = _registration_marks_for_channel(
        programs,
        settings,
    )
    errors.extend(parse_errors)
    marks_by_channel = {}
    for channel, arms in arms_by_channel.items():
        marks, mark_errors = _marks_from_arms(arms)
        marks_by_channel[channel] = marks
        errors.extend(
            "%s: %s" % (channel, message)
            for message in mark_errors
        )
        if len(marks) < MIN_REGISTRATION_MARKS:
            errors.append(
                "%s has %d identified registration marks; at least %d "
                "four-corner-equivalent marks are required"
                % (channel, len(marks), MIN_REGISTRATION_MARKS)
            )
    reference_channel = (
        "c" if "c" in programs else next(iter(programs), None)
    )
    reference_marks = marks_by_channel.get(reference_channel, {})
    reference_ids = set(reference_marks)
    reference_centroid = (
        _mean(
            mark["observed_center_mm"][0]
            for mark in reference_marks.values()
        ),
        _mean(
            mark["observed_center_mm"][1]
            for mark in reference_marks.values()
        ),
    )
    covariance_xx = 0.0
    covariance_xy = 0.0
    covariance_yy = 0.0
    for mark in reference_marks.values():
        dx = mark["observed_center_mm"][0] - reference_centroid[0]
        dy = mark["observed_center_mm"][1] - reference_centroid[1]
        covariance_xx += dx * dx
        covariance_xy += dx * dy
        covariance_yy += dy * dy
    reference_noncollinear = (
        covariance_xx * covariance_yy
        - covariance_xy * covariance_xy
    ) > 1e-9
    if reference_ids and not reference_noncollinear:
        errors.append(
            "%s registration marks are collinear or coincident"
            % reference_channel
        )
    per_ink = {}

    for channel in programs:
        marks = marks_by_channel.get(channel, {})
        if set(marks) != reference_ids:
            errors.append(
                "%s registration mark IDs differ from %s"
                % (channel, reference_channel)
            )
        if channel in expected_offsets:
            actual_offsets = {
                mark["pen_offset_mm"] for mark in marks.values()
            }
            if any(
                _distance(offset, expected_offsets[channel]) > 1e-6
                for offset in actual_offsets
            ):
                errors.append(
                    "%s emitted pen offset does not match the configured "
                    "%s offset"
                    % (channel, channel)
                )
        common_ids = sorted(reference_ids & set(marks))
        pen_errors = []
        marker_identity_errors = []
        for mark_id in common_ids:
            mark = marks[mark_id]
            expected_base = mark["expected_center_mm"]
            reference_base = reference_marks[mark_id][
                "expected_center_mm"
            ]
            if _distance(expected_base, reference_base) > REGISTRATION_TOLERANCE_MM:
                marker_identity_errors.append(
                    "%s %s expected registration center differs from %s by "
                    "%.3f mm"
                    % (
                        channel,
                        mark_id,
                        reference_channel,
                        _distance(expected_base, reference_base),
                    )
                )
            expected = (
                expected_base[0] + mark["pen_offset_mm"][0],
                expected_base[1] + mark["pen_offset_mm"][1],
            )
            error = _distance(mark["observed_center_mm"], expected)
            mark["offset_application_error_mm"] = error
            if error > REGISTRATION_TOLERANCE_MM:
                pen_errors.append(
                    "%s %s pen offset applied %.3f mm off the declared "
                    "single application"
                    % (channel, mark_id, error)
                )
        errors.extend(pen_errors)
        errors.extend(marker_identity_errors)
        normalized = {
            mark_id: (
                marks[mark_id]["observed_center_mm"][0]
                - marks[mark_id]["pen_offset_mm"][0],
                marks[mark_id]["observed_center_mm"][1]
                - marks[mark_id]["pen_offset_mm"][1],
            )
            for mark_id in common_ids
        }
        reference_points = [
            (
                reference_marks[mark_id]["observed_center_mm"][0]
                - reference_marks[mark_id]["pen_offset_mm"][0],
                reference_marks[mark_id]["observed_center_mm"][1]
                - reference_marks[mark_id]["pen_offset_mm"][1],
            )
            for mark_id in common_ids
        ]
        points = [normalized[mark_id] for mark_id in common_ids]
        residuals = [
            _distance(point, reference)
            for point, reference in zip(points, reference_points)
        ]
        similarity = _similarity_metrics(reference_points, points)
        reference_centroid = (
            _mean(point[0] for point in reference_points),
            _mean(point[1] for point in reference_points),
        )
        reference_radius = max(
            (
                _distance(point, reference_centroid)
                for point in reference_points
            ),
            default=0.0,
        )
        if reference_radius > REGISTRATION_TOLERANCE_MM:
            rotation_tolerance = math.degrees(
                math.asin(
                    min(
                        1.0,
                        REGISTRATION_TOLERANCE_MM / reference_radius,
                    )
                )
            )
            scale_tolerance = (
                REGISTRATION_TOLERANCE_MM / reference_radius
            )
        else:
            rotation_tolerance = 0.0
            scale_tolerance = 0.0
        rms = math.sqrt(_mean(value * value for value in residuals))
        maximum = max(residuals, default=0.0)
        translation = similarity["translation_mm"]
        rotation = similarity["rotation_deg"]
        scale = similarity["scale"]
        ink_errors = list(pen_errors) + list(marker_identity_errors)
        if reference_ids and not reference_noncollinear:
            ink_errors.append(
                "registration marks are collinear or coincident"
            )
        if math.hypot(*translation) > REGISTRATION_TOLERANCE_MM:
            ink_errors.append(
                "%s translation %.3f mm exceeds %.3f mm"
                % (
                    channel,
                    math.hypot(*translation),
                    REGISTRATION_TOLERANCE_MM,
                )
            )
        if abs(rotation) > rotation_tolerance:
            ink_errors.append(
                "%s rotation %.4f deg exceeds %.4f deg"
                % (channel, rotation, rotation_tolerance)
            )
        if abs(scale - 1.0) > scale_tolerance:
            ink_errors.append(
                "%s scale %.6f differs by more than %.6f"
                % (channel, scale, scale_tolerance)
            )
        if maximum > REGISTRATION_TOLERANCE_MM:
            ink_errors.append(
                "%s maximum registration residual %.3f mm exceeds %.3f mm"
                % (channel, maximum, REGISTRATION_TOLERANCE_MM)
            )
        if rms > REGISTRATION_RMS_TOLERANCE_MM:
            ink_errors.append(
                "%s registration RMS %.3f mm exceeds %.3f mm"
                % (channel, rms, REGISTRATION_RMS_TOLERANCE_MM)
            )
        errors.extend(ink_errors)
        per_ink[channel] = {
            "passed": not ink_errors,
            "errors": ink_errors,
            "mark_count": len(marks),
            "matched_mark_count": len(common_ids),
            "mark_ids": sorted(marks),
            "centroid_mm": _rounded_point(similarity["centroid_mm"]),
            "translation_mm": _rounded_point(translation),
            "rotation_deg": round(rotation, 6),
            "scale": round(scale, 9),
            "translation_tolerance_mm": REGISTRATION_TOLERANCE_MM,
            "rotation_tolerance_deg": round(rotation_tolerance, 6),
            "scale_tolerance": round(scale_tolerance, 9),
            "rms_residual_mm": round(rms, 6),
            "rms_tolerance_mm": REGISTRATION_RMS_TOLERANCE_MM,
            "max_residual_mm": round(maximum, 6),
            "max_tolerance_mm": REGISTRATION_TOLERANCE_MM,
            "similarity_rms_mm": round(
                similarity["similarity_rms_mm"],
                6,
            ),
            "similarity_max_mm": round(
                similarity["similarity_max_mm"],
                6,
            ),
            "pen_offset_max_error_mm": round(
                max(
                    (
                        marks[mark_id][
                            "offset_application_error_mm"
                        ]
                        for mark_id in common_ids
                    ),
                    default=0.0,
                ),
                6,
            ),
            "residuals_by_mark_mm": {
                mark_id: round(value, 6)
                for mark_id, value in zip(common_ids, residuals)
            },
            "marks": {
                mark_id: {
                    "observed_center_mm": _rounded_point(
                        marks[mark_id]["observed_center_mm"]
                    ),
                    "normalized_center_mm": _rounded_point(
                        normalized[mark_id]
                    ),
                    "expected_center_mm": _rounded_point(
                        marks[mark_id]["expected_center_mm"]
                    ),
                    "pen_offset_mm": _rounded_point(
                        marks[mark_id]["pen_offset_mm"]
                    ),
                    "residual_mm": round(value, 6),
                    "arms": marks[mark_id]["arms"],
                }
                for mark_id, value in zip(common_ids, residuals)
            },
        }
    return {
        "kind": "cmyk-gcode-registration-audit",
        "version": 1,
        "scope": [
            "software_registration",
            "emitted_machine_geometry",
            "registration_marks",
            "a_rotation_reversal",
            "compensation_inversion",
            "pen_offset_single_application",
            "translation_rotation_scale",
        ],
        "tolerance_mm": REGISTRATION_TOLERANCE_MM,
        "rms_tolerance_mm": REGISTRATION_RMS_TOLERANCE_MM,
        "reference_channel": reference_channel,
        "mark_count": len(reference_ids),
        "mark_ids": sorted(reference_ids),
        "passed": not errors,
        "errors": errors,
        "inks": per_ink,
        "physical_overlay": "pending physical four-pen test",
    }


def audit_cmyk_gcode_set(
    programs,
    settings,
    expected_pen_offsets_mm=None,
    expected_row_angles=None,
    expected_frame_center_mm=None,
    expected_profile_fingerprint=None,
    expected_reach_radius_mm=None,
):
    """Validate set identity and pointwise software registration together."""
    programs = {
        str(channel): str(text)
        for channel, text in dict(programs).items()
    }
    identity = {}
    identity_errors = []
    try:
        identity = validate_program_set_identity(
            programs,
            expected_row_angles=expected_row_angles,
            expected_frame_center_mm=(
                expected_frame_center_mm
                if expected_frame_center_mm is not None
                else getattr(settings, "frame_center_mm", None)
            ),
            expected_profile_fingerprint=(
                expected_profile_fingerprint
                if expected_profile_fingerprint is not None
                else load_bed_compensation(
                    getattr(settings, "bed_compensation_path", "")
                ).fingerprint
                if getattr(settings, "bed_compensation_path", "")
                else None
            ),
            expected_reach_radius_mm=(
                expected_reach_radius_mm
                if expected_reach_radius_mm is not None
                else getattr(settings, "machine_reach_radius_mm", None)
            ),
        )
    except (OSError, ValueError) as error:
        identity_errors.append(str(error))
        parsed = {
            channel: gcode_program_identity(text)
            for channel, text in programs.items()
        }
        if parsed:
            reference = next(iter(parsed.values()))
            identity = {
                **reference,
                "row_angles_deg": {
                    channel: value["row_angle_deg"]
                    for channel, value in parsed.items()
                },
            }
    registration = audit_cmyk_gcode_registration(
        programs,
        settings,
        expected_pen_offsets_mm=expected_pen_offsets_mm,
    )
    errors = identity_errors + registration["errors"]
    return {
        "passed": not errors,
        "errors": errors,
        "identity": identity,
        "registration": registration,
    }
