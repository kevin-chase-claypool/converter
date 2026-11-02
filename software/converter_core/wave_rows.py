"""Shared bed-angle planning for equidistant rotating-bed Wave rows."""

import bisect
import math

from .cancellation import check_cancelled


# Bound the midpoint shrink between adjacent rows caused by linear X/Y/A
# interpolation. For row pitch h and one emitted angle interval d:
# shrink ~= h * (1 - cos(d / 2)).
WAVE_ROW_INTERPOLATION_TOLERANCE_MM = 0.0005


def wave_row_screen_axes(settings):
    """Return ``(along, across)`` for final paper-space Wave rows."""
    angle_deg = float(
        getattr(settings, "row_lock_screen_angle_deg", 0.0)
    )
    if bool(getattr(settings, "flip_y", True)):
        angle_deg = -angle_deg
    return _screen_axes_from_angle(angle_deg)


def _screen_axes_from_angle(angle_deg):
    angle = math.radians(float(angle_deg))
    return (
        (math.cos(angle), math.sin(angle)),
        (-math.sin(angle), math.cos(angle)),
    )


def _project(point, axis):
    return point[0] * axis[0] + point[1] * axis[1]


def _median(values):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return 0.5 * (ordered[middle - 1] + ordered[middle])


def wave_row_theta_lock_enabled(settings):
    """Whether explicit Wave rows require one shared rotating-bed schedule."""
    if not bool(getattr(settings, "row_locked_compensation", False)):
        return False
    contour_order = str(
        getattr(settings, "contour_order", "optimized")
    ).strip().lower()
    if contour_order not in ("rows_ascending", "rows_descending"):
        return False
    theta_mode = str(
        getattr(settings, "theta_mode", "optimized")
    ).strip().lower()
    return theta_mode != "fixed"


def wave_row_theta_schedule(
    planned_items,
    settings,
    center,
    theta_planner,
    cancel_check=None,
):
    """Build one bed-angle schedule shared by every parallel Wave row.

    A rotating bed is valid for an equidistant Wave layer only if adjacent
    rows have the same orientation wherever they cross the same along-row
    coordinate. The representative row is planned once in the converter's
    screen frame, then every row samples the same ``theta(along)`` function.
    """
    if not wave_row_theta_lock_enabled(settings):
        return None

    along_axis, across_axis = wave_row_screen_axes(settings)
    row_groups = {}
    for item in planned_items:
        path = item["path"]
        row_index = getattr(path, "wave_row_index", None)
        if row_index is not None:
            row_groups.setdefault(int(row_index), []).append(path)
    if len(row_groups) < 2:
        return None

    row_across = {}
    candidates = []
    global_along = []
    for row_index, paths in row_groups.items():
        check_cancelled(cancel_check)
        values = [
            _project(point, across_axis)
            for path in paths
            for point in path
        ]
        if not values:
            continue
        row_across[row_index] = _median(values)
        for path in paths:
            check_cancelled(cancel_check)
            along_values = [_project(point, along_axis) for point in path]
            if along_values:
                global_along.extend(along_values)
                candidates.append(
                    (max(along_values) - min(along_values), path)
                )
    if len(row_across) < 2 or not candidates:
        return None

    pitch_mm = _row_pitch(row_across)
    if pitch_mm <= 1e-9:
        return None

    _span, template = max(candidates, key=lambda item: item[0])
    template_points = sorted(
        (_project(point, along_axis), _project(point, across_axis))
        for point in template
    )
    baseline = _median(value for _along, value in template_points)
    guide_screen = [
        (along, across - baseline)
        for along, across in template_points
    ]
    _extend_guide(
        guide_screen,
        min(global_along),
        max(global_along),
    )
    guide = [
        (
            along * along_axis[0] + across * across_axis[0],
            along * along_axis[1] + across * across_axis[1],
        )
        for along, across in guide_screen
    ]
    guide_thetas, _strategies = theta_planner(
        guide,
        settings,
        None,
        center,
        None,
        cancel_check,
    )
    if len(guide_thetas) != len(guide):
        return None
    positions, thetas = _deduplicate_along(
        guide,
        guide_thetas,
        along_axis,
    )
    if len(positions) < 2:
        return None

    configured_cap = max(
        float(getattr(settings, "theta_max_step_deg", 15.0)),
        0.0,
    )
    row_tolerance = min(
        WAVE_ROW_INTERPOLATION_TOLERANCE_MM,
        0.49 * pitch_mm,
    )
    spacing_cap = math.degrees(
        2.0 * math.acos(1.0 - row_tolerance / pitch_mm)
    )
    max_step_deg = max(0.25, min(configured_cap, spacing_cap))
    return {
        "positions": tuple(positions),
        "thetas": tuple(thetas),
        "pitch_mm": pitch_mm,
        "max_step_deg": max_step_deg,
        "angle_deg": math.degrees(
            math.atan2(along_axis[1], along_axis[0])
        ),
    }


def _row_pitch(row_across):
    index_gaps = []
    ordered_rows = sorted(row_across)
    for first, second in zip(ordered_rows, ordered_rows[1:]):
        row_delta = second - first
        if row_delta > 0:
            pitch = abs(row_across[second] - row_across[first]) / row_delta
            if pitch > 1e-9:
                index_gaps.append(pitch)
    return _median(index_gaps)


def _extend_guide(guide_screen, low_along, high_along):
    if not guide_screen:
        return
    if guide_screen[0][0] > low_along:
        guide_screen.insert(0, (low_along, guide_screen[0][1]))
    if guide_screen[-1][0] < high_along:
        guide_screen.append((high_along, guide_screen[-1][1]))


def _deduplicate_along(guide, thetas, along_axis):
    positions = []
    values = []
    for point, theta in zip(guide, thetas):
        along = _project(point, along_axis)
        if positions and abs(along - positions[-1]) <= 1e-9:
            values[-1] = theta
        else:
            positions.append(along)
            values.append(theta)
    return positions, values


def wave_row_thetas(path, schedule):
    """Sample one shared Wave-row schedule at every path point."""
    along_axis, _across_axis = _screen_axes_from_angle(
        schedule["angle_deg"]
    )
    positions = schedule["positions"]
    values = schedule["thetas"]
    thetas = []
    for point in path:
        along = _project(point, along_axis)
        right = bisect.bisect_right(positions, along)
        if right <= 0:
            theta = values[0]
        elif right >= len(positions):
            theta = values[-1]
        else:
            left = right - 1
            span = positions[right] - positions[left]
            fraction = (
                0.0
                if span <= 1e-12
                else (along - positions[left]) / span
            )
            theta = values[left] + fraction * (values[right] - values[left])
        thetas.append(theta)
    return thetas
