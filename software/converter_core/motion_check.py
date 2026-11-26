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
    over_tolerance = 0
    rapids_with_rotation = fed_rotations = unwinds = 0

    previous = None
    for number, line in enumerate(text.splitlines(), 1):
        match = MOVE.match(line)
        if not match:
            continue
        kind, x, y, a, feed = match.groups()
        point = (float(x), float(y), float(a) if a is not None else None)
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
    return problems
