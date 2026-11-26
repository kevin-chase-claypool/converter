"""Pre-flight checks for a generated G-code program.

Everything here is measured from the emitted text, not from the settings that
produced it, so the same analysis can answer "was this program generated
before the guards existed?" and "does it obey the current guards?".
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from . import kinematics


MOVE = re.compile(
    r"G([01])\s+X(-?[\d.]+)\s+Y(-?[\d.]+)(?:\s+A(-?[\d.]+))?(?:\s+F([\d.]+))?"
)
LABEL = re.compile(r"\(([a-z_ ]+)\)\s*$")
TOLERANCE_HEADER = re.compile(r"tolerance ([\d.]+) mm")
FRAME_HEADER = re.compile(
    r"^\(frame center (-?[\d.]+),(-?[\d.]+) mm, bed motion .+\)$",
    re.MULTILINE,
)
PROFILE_HEADER = re.compile(
    r"^\(bed compensation ([0-9a-fA-F]+), coverage",
    re.MULTILINE,
)
REACH_HEADER = re.compile(
    r"^\(reach guard (-?[\d.]+) mm, compensation reserve "
    r"(-?[\d.]+) mm, pen radius (-?[\d.]+) mm, "
    r"planning radius (-?[\d.]+) mm\)$",
    re.MULTILINE,
)
ROW_ANGLE_HEADER = re.compile(
    r"at row angle (-?[\d.]+) deg",
    re.MULTILINE,
)


def analyse_gcode(text, settings, tolerance=None):
    """Return motion metrics for one full G-code program."""
    ratio = settings.theta_drive_ratio
    cap = float(
        getattr(settings, "theta_max_step_deg", kinematics.MAX_BED_STEP_DEG)
    )
    rate_cap = settings.theta_controller_limits.max_rate_deg_min / 60.0
    tolerance = (
        float(tolerance)
        if tolerance is not None
        else float(getattr(settings, "tolerance", 0.0))
    )

    drawing = travel = hold = 0
    strategies = {}
    worst_step = (0.0, 0)
    worst_rate = (0.0, 0)
    worst_deviation = (0.0, 0.0, 0, "")
    max_xy_radius = (0.0, 0)
    over_tolerance = 0
    rapids_with_rotation = fed_rotations = unwinds = 0

    previous = None
    for number, line in enumerate(text.splitlines(), 1):
        match = MOVE.match(line)
        if not match:
            continue
        kind, x, y, a, feed = match.groups()
        point = (float(x), float(y), float(a) if a is not None else None)
        radius = math.hypot(point[0], point[1])
        if radius > max_xy_radius[0]:
            max_xy_radius = (radius, number)
        label_match = LABEL.search(line.rstrip())
        label = label_match.group(1) if label_match else ""
        if label:
            strategies[label] = strategies.get(label, 0) + 1
            if label == "hold":
                hold += 1
        # A pen-up move is either a `G0` or a fed re-registration labelled
        # `(travel)`; both carry the bed's whole-revolution unwinds, which are
        # allowed there and irrelevant to ink.
        is_travel = kind == "0" or label == "travel"
        if previous is not None and point[2] is not None and previous[2] is not None:
            delta = abs(point[2] - previous[2])
            if is_travel:
                travel += 1
                if delta > 1e-9:
                    if "(travel)" in line:
                        fed_rotations += 1
                    else:
                        rapids_with_rotation += 1
                if delta > ratio * 300.0:
                    unwinds += 1
            else:
                drawing += 1
                if delta > worst_step[0]:
                    worst_step = (delta, number)
                if delta > 1e-9 and feed:
                    xy = math.hypot(
                        point[0] - previous[0], point[1] - previous[1]
                    )
                    seconds = (math.hypot(xy, delta) / float(feed)) * 60.0
                    if seconds > 0.0 and delta / seconds > worst_rate[0]:
                        worst_rate = (delta / seconds, number)
                if delta > 1e-9:
                    deviation = kinematics._polar_move_deviation(
                        (previous[0], previous[1]),
                        (point[0], point[1]),
                        (0.0, 0.0),
                        previous[2] / ratio,
                        point[2] / ratio,
                    )
                    if deviation > tolerance + 1e-9:
                        over_tolerance += 1
                    if deviation > worst_deviation[0]:
                        worst_deviation = (
                            deviation,
                            0.5
                            * (
                                math.hypot(previous[0], previous[1])
                                + math.hypot(point[0], point[1])
                            ),
                            number,
                            label or kind,
                        )
        previous = point

    pen_radius = max(
        float(getattr(settings, "pen_diameter_mm", 0.0)) / 2.0,
        0.0,
    )
    reach = max(
        float(getattr(settings, "machine_reach_radius_mm", 0.0)),
        0.0,
    )
    reach_match = REACH_HEADER.search(text)
    planning_radius = (
        float(reach_match.group(4))
        if reach_match is not None
        else None
    )
    return {
        "drawing": drawing,
        "travel": travel,
        "hold": hold,
        "strategies": strategies,
        "step": worst_step[0] / ratio,
        "step_line": worst_step[1],
        "rate": worst_rate[0],
        "rate_line": worst_rate[1],
        "deviation": worst_deviation,
        "tolerance": tolerance,
        "over_tolerance": over_tolerance,
        "rapids_with_rotation": rapids_with_rotation,
        "fed_rotations": fed_rotations,
        "unwinds": unwinds,
        "cap": cap,
        "rate_cap": rate_cap,
        "max_xy_radius_mm": max_xy_radius[0],
        "max_xy_radius_line": max_xy_radius[1],
        "max_ink_radius_mm": max_xy_radius[0] + pen_radius,
        "pen_radius_mm": pen_radius,
        "machine_reach_radius_mm": reach,
        "planning_radius_mm": planning_radius,
    }


def analyse_file(path, settings):
    """Read a saved program and return its motion metrics."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    match = TOLERANCE_HEADER.search(text)
    return analyse_gcode(
        text,
        settings,
        tolerance=float(match.group(1)) if match else None,
    )


def gcode_program_identity(text):
    """Return the safety-relevant frame and compensation identity."""
    frame_match = FRAME_HEADER.search(text)
    profile_match = PROFILE_HEADER.search(text)
    reach_match = REACH_HEADER.search(text)
    row_angle_match = ROW_ANGLE_HEADER.search(text)
    return {
        "has_g54": bool(re.search(r"^G54\s*$", text, re.MULTILINE)),
        "frame_center_mm": (
            (
                float(frame_match.group(1)),
                float(frame_match.group(2)),
            )
            if frame_match is not None
            else None
        ),
        "profile_fingerprint": (
            profile_match.group(1).lower()
            if profile_match is not None
            else None
        ),
        "machine_reach_radius_mm": (
            float(reach_match.group(1))
            if reach_match is not None
            else None
        ),
        "compensation_reserve_mm": (
            float(reach_match.group(2))
            if reach_match is not None
            else None
        ),
        "pen_radius_mm": (
            float(reach_match.group(3))
            if reach_match is not None
            else None
        ),
        "planning_radius_mm": (
            float(reach_match.group(4))
            if reach_match is not None
            else None
        ),
        "row_angle_deg": (
            float(row_angle_match.group(1))
            if row_angle_match is not None
            else None
        ),
    }


def validate_program_set_identity(
    programs,
    expected_row_angles=None,
    expected_frame_center_mm=None,
    expected_profile_fingerprint=None,
    expected_reach_radius_mm=None,
):
    """Require every program in a multi-file set to share one safety frame.

    ``programs`` maps channel keys to complete G-code text. All entries must
    declare G54, the same frame center, reach guard, and compensation profile.
    A Wave row-lock set must also declare the expected row angle per channel.
    """
    programs = {
        str(channel): str(text)
        for channel, text in dict(programs).items()
    }
    if not programs:
        raise ValueError("program set identity check received no programs")
    identities = {
        channel: gcode_program_identity(text)
        for channel, text in programs.items()
    }
    reference_channel = next(iter(identities))
    reference = identities[reference_channel]
    required = (
        "frame_center_mm",
        "machine_reach_radius_mm",
        "planning_radius_mm",
    )
    for field in required:
        if reference[field] is None:
            raise ValueError(
                "%s has no %s safety identity"
                % (reference_channel, field.replace("_", " "))
            )
    if expected_frame_center_mm is not None:
        expected_frame = tuple(
            float(value) for value in expected_frame_center_mm
        )
        if math.hypot(
            reference["frame_center_mm"][0] - expected_frame[0],
            reference["frame_center_mm"][1] - expected_frame[1],
        ) > 1e-6:
            raise ValueError(
                "%s frame center %s differs from configured %s"
                % (
                    reference_channel,
                    reference["frame_center_mm"],
                    expected_frame,
                )
            )
    if expected_profile_fingerprint is not None:
        expected_profile = str(expected_profile_fingerprint).lower()
        if reference["profile_fingerprint"] != expected_profile:
            raise ValueError(
                "%s profile fingerprint %s differs from configured %s"
                % (
                    reference_channel,
                    reference["profile_fingerprint"],
                    expected_profile,
                )
            )
    if expected_reach_radius_mm is not None:
        expected_reach = float(expected_reach_radius_mm)
        if abs(
            reference["machine_reach_radius_mm"] - expected_reach
        ) > 1e-6:
            raise ValueError(
                "%s machine reach %.6f differs from configured %.6f"
                % (
                    reference_channel,
                    reference["machine_reach_radius_mm"],
                    expected_reach,
                )
            )
    for channel, identity in identities.items():
        if not identity["has_g54"]:
            raise ValueError("%s does not declare G54" % channel)
        for field in required:
            if identity[field] is None:
                raise ValueError(
                    "%s has no %s safety identity"
                    % (channel, field.replace("_", " "))
                )
        if math.hypot(
            identity["frame_center_mm"][0]
            - reference["frame_center_mm"][0],
            identity["frame_center_mm"][1]
            - reference["frame_center_mm"][1],
        ) > 1e-6:
            raise ValueError(
                "%s frame center %s differs from %s %s"
                % (
                    channel,
                    identity["frame_center_mm"],
                    reference_channel,
                    reference["frame_center_mm"],
                )
            )
        if identity["profile_fingerprint"] != reference[
            "profile_fingerprint"
        ]:
            raise ValueError(
                "%s profile fingerprint %s differs from %s %s"
                % (
                    channel,
                    identity["profile_fingerprint"],
                    reference_channel,
                    reference["profile_fingerprint"],
                )
            )
        for field in (
            "machine_reach_radius_mm",
            "compensation_reserve_mm",
            "pen_radius_mm",
            "planning_radius_mm",
        ):
            if abs(identity[field] - reference[field]) > 1e-6:
                raise ValueError(
                    "%s %s %.6f differs from %s %.6f"
                    % (
                        channel,
                        field.replace("_", " "),
                        identity[field],
                        reference_channel,
                        reference[field],
                    )
                )
    if expected_row_angles is not None:
        for channel, expected_angle in dict(
            expected_row_angles
        ).items():
            channel = str(channel)
            actual_angle = identities.get(channel, {}).get("row_angle_deg")
            if actual_angle is None:
                raise ValueError(
                    "%s has no row angle identity" % channel
                )
            if abs(actual_angle - (float(expected_angle) % 180.0)) > 1e-6:
                raise ValueError(
                    "%s row angle %.3f differs from expected %.3f"
                    % (channel, actual_angle, float(expected_angle) % 180.0)
                )
    return {
        "frame_center_mm": reference["frame_center_mm"],
        "profile_fingerprint": reference["profile_fingerprint"],
        "machine_reach_radius_mm": reference[
            "machine_reach_radius_mm"
        ],
        "compensation_reserve_mm": reference[
            "compensation_reserve_mm"
        ],
        "pen_radius_mm": reference["pen_radius_mm"],
        "planning_radius_mm": reference["planning_radius_mm"],
        "row_angles_deg": {
            channel: identity["row_angle_deg"]
            for channel, identity in identities.items()
        },
    }


def preflight_problems(result):
    """Return the hard guard violations from an analysis result."""
    problems = []
    if result["step"] > result["cap"] + 1e-6:
        problems.append(
            "a drawing move rotates %.1f deg, over the %.0f deg cap"
            % (result["step"], result["cap"])
        )
    if result["rate"] > result["rate_cap"] * 1.01:
        problems.append(
            "a move asks for %.0f motor deg/s, over the %.0f limit"
            % (result["rate"], result["rate_cap"])
        )
    if result["rapids_with_rotation"]:
        problems.append(
            "%d pen-up moves carry rotation as bare G0 rapids"
            % result["rapids_with_rotation"]
        )
    reach = float(result.get("machine_reach_radius_mm", 0.0))
    max_ink_radius = float(result.get("max_ink_radius_mm", 0.0))
    if reach > 0.0 and max_ink_radius > reach + 0.001:
        problems.append(
            "a move's ink envelope reaches %.3f mm from the bed center, "
            "over the %.3f mm machine reach (path centerline %.3f mm)"
            % (
                max_ink_radius,
                reach,
                float(result.get("max_xy_radius_mm", 0.0)),
            )
        )
    return problems
