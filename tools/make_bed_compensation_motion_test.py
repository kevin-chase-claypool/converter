"""Generate a one-sheet compensated-versus-uncompensated tracking test.

Every case traces the same bed-space path with the same bed-angle schedule.
The only intentional differences are whether bed compensation is applied,
whether the bed rotates, and the requested feed. Each case draws a reference
cross at A0, performs a rotating pen-up move, draws a forward/reverse path while
the bed rotates, then returns at A0 and draws the same cross again. A clean
result therefore has coincident ink at both crosses and forward/reverse traces.

The program uses ordinary paper and one black Pigma Micron. It is one G-code
file with one Cycle Start and no M0 pauses.
"""

from __future__ import annotations

import argparse
import dataclasses
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


DEFAULT_BED_COMPENSATION = (
    ROOT
    / "samples"
    / "gcode"
    / "bed-error-compensation-2026-10-23-13p5in-extrapolated.json"
)
DEFAULT_OUTPUT = (
    ROOT / "samples" / "gcode" / "bed-compensation-motion-test.gcode"
)

THETA_RATIO = 12.03324
PATH_MIN_X_MM = -45.0
PATH_MAX_X_MM = 45.0
PATH_STEP_MM = 0.6
PATH_WAVES = 3.0
PATH_AMPLITUDE_MM = 1.6
A_SWEEP_DEG = 14.5
CROSS_CENTER_X_MM = -55.0
CROSS_ARM_MM = 2.5
FAST_FEED_MM_MIN = 700.0
SLOW_FEED_MM_MIN = 350.0
TRAVEL_FEED_MM_MIN = 3000.0

CASES = (
    {
        "id": 1,
        "name": "XY only A parked",
        "y_mm": 56.0,
        "rotate": False,
        "compensate": False,
        "feed_mm_min": FAST_FEED_MM_MIN,
    },
    {
        "id": 2,
        "name": "rotating uncompensated fast",
        "y_mm": 28.0,
        "rotate": True,
        "compensate": False,
        "feed_mm_min": FAST_FEED_MM_MIN,
    },
    {
        "id": 3,
        "name": "rotating compensated fast",
        "y_mm": 0.0,
        "rotate": True,
        "compensate": True,
        "feed_mm_min": FAST_FEED_MM_MIN,
    },
    {
        "id": 4,
        "name": "rotating uncompensated slow",
        "y_mm": -28.0,
        "rotate": True,
        "compensate": False,
        "feed_mm_min": SLOW_FEED_MM_MIN,
    },
    {
        "id": 5,
        "name": "rotating compensated slow",
        "y_mm": -56.0,
        "rotate": True,
        "compensate": True,
        "feed_mm_min": SLOW_FEED_MM_MIN,
    },
)


def fmt(value: float) -> str:
    return converter.format_float(float(value))


def load_profile():
    return converter.BedCompensationProfile.from_json(
        DEFAULT_BED_COMPENSATION.read_text(encoding="utf-8")
    )


def machine_point(
    point: tuple[float, float],
    theta_deg: float,
    profile,
    compensate: bool,
) -> tuple[float, float]:
    return converter.compensated_machine_point(
        point,
        theta_deg,
        (0.0, 0.0),
        profile if compensate else None,
    )


def path_y(x_mm: float, lane_y_mm: float) -> float:
    fraction = (x_mm - PATH_MIN_X_MM) / (PATH_MAX_X_MM - PATH_MIN_X_MM)
    return lane_y_mm + PATH_AMPLITUDE_MM * math.sin(
        2.0 * math.pi * PATH_WAVES * fraction
    )


def path_points(case) -> list[tuple[float, float]]:
    count = int(
        round((PATH_MAX_X_MM - PATH_MIN_X_MM) / PATH_STEP_MM)
    )
    return [
        (
            PATH_MIN_X_MM
            + (PATH_MAX_X_MM - PATH_MIN_X_MM) * index / count,
            path_y(
                PATH_MIN_X_MM
                + (PATH_MAX_X_MM - PATH_MIN_X_MM) * index / count,
                case["y_mm"],
            ),
        )
        for index in range(count + 1)
    ]


def theta_for_fraction(case, fraction: float) -> float:
    if not case["rotate"]:
        return 0.0
    return -A_SWEEP_DEG + 2.0 * A_SWEEP_DEG * fraction


def case_settings(case):
    feed = float(case["feed_mm_min"])
    return dataclasses.replace(
        converter.Settings(),
        feed_rate=feed,
        theta_tangential_speed_mm_min=feed,
    )


def emit_g1(
    lines: list[str],
    point: tuple[float, float],
    theta_deg: float,
    feed: float,
    profile,
    compensate: bool,
    label: str,
) -> None:
    x_mm, y_mm = machine_point(
        point, theta_deg, profile, compensate
    )
    lines.append(
        f"G1 X{fmt(x_mm)} Y{fmt(y_mm)} "
        f"A{fmt(theta_deg * THETA_RATIO)} F{fmt(feed)} ({label})"
    )


def emit_travel(
    lines: list[str],
    point: tuple[float, float],
    theta_deg: float,
    profile,
    compensate: bool,
    description: str,
) -> None:
    lines.append(f"({description})")
    emit_g1(
        lines,
        point,
        theta_deg,
        TRAVEL_FEED_MM_MIN,
        profile,
        compensate,
        "travel",
    )


def emit_rotating_travel(
    lines: list[str],
    start_point: tuple[float, float],
    start_theta_deg: float,
    end_point: tuple[float, float],
    end_theta_deg: float,
    profile,
    compensate: bool,
    description: str,
) -> None:
    start_machine = machine_point(
        start_point, start_theta_deg, profile, compensate
    )
    end_machine = machine_point(
        end_point, end_theta_deg, profile, compensate
    )
    feed_plan = converter.plan_travel_move(
        converter.Settings(),
        converter.distance(start_machine, end_machine),
        abs(end_theta_deg - start_theta_deg) * THETA_RATIO,
    )
    lines.append(f"({description})")
    emit_g1(
        lines,
        end_point,
        end_theta_deg,
        feed_plan["feed_rate"],
        profile,
        compensate,
        "travel",
    )


def emit_cross(
    lines: list[str],
    center: tuple[float, float],
    feed: float,
    label: str,
) -> None:
    x_mm, y_mm = center
    points = (
        (x_mm + CROSS_ARM_MM, y_mm),
        (x_mm - CROSS_ARM_MM, y_mm),
        center,
        (x_mm, y_mm + CROSS_ARM_MM),
        (x_mm, y_mm - CROSS_ARM_MM),
        center,
    )
    for point in points:
        x, y = point
        lines.append(
            f"G1 X{fmt(x)} Y{fmt(y)} A0 F{fmt(feed)} ({label})"
        )


def emit_pen_down(lines: list[str], first_pen_down: bool) -> None:
    lines.append("M3")
    lines.append(
        "G65 P115 Q1 B12 A1 W2"
        if first_pen_down
        else "G65 P115 Q1 A1 W2"
    )


def emit_pen_up(lines: list[str]) -> None:
    lines.append("M5")
    lines.append("G65 P115 Q1 A1 W2")


def emit_case(lines: list[str], case, profile, first_pen_down: bool) -> None:
    center = (CROSS_CENTER_X_MM, float(case["y_mm"]))
    settings = case_settings(case)
    requested_feed = float(case["feed_mm_min"])
    points = path_points(case)
    lines.append(
        f"(case {case['id']}: {case['name']}; bed y {fmt(case['y_mm'])} mm; "
        f"A {fmt(-A_SWEEP_DEG)} to {fmt(A_SWEEP_DEG)} to "
        f"{fmt(-A_SWEEP_DEG)} deg; requested F{fmt(requested_feed)})"
    )

    emit_travel(
        lines,
        center,
        0.0,
        profile,
        False,
        "travel to case witness",
    )
    emit_pen_down(lines, first_pen_down)
    emit_cross(lines, center, requested_feed, "initial witness")
    emit_pen_up(lines)

    start_theta = theta_for_fraction(case, 0.0)
    emit_rotating_travel(
        lines,
        center,
        0.0,
        points[0],
        start_theta,
        profile,
        bool(case["compensate"]),
        "rotating pen-up to path",
    )
    emit_pen_down(lines, False)

    for index, (first, second) in enumerate(zip(points, points[1:])):
        start_fraction = index / (len(points) - 1)
        end_fraction = (
            (index + 1) / (len(points) - 1)
        )
        start_theta = theta_for_fraction(case, start_fraction)
        end_theta = theta_for_fraction(case, end_fraction)
        start_machine = machine_point(
            first,
            start_theta,
            profile,
            bool(case["compensate"]),
        )
        end_machine = machine_point(
            second,
            end_theta,
            profile,
            bool(case["compensate"]),
        )
        feed_plan = converter.plan_radius_aware_draw_feed(
            first,
            second,
            (0.0, 0.0),
            converter.distance(start_machine, end_machine),
            (end_theta - start_theta) * THETA_RATIO,
            settings,
        )
        emit_g1(
            lines,
            second,
            end_theta,
            feed_plan["feed_rate"],
            profile,
            bool(case["compensate"]),
            "forward trace",
        )

    for index in range(len(points) - 2, -1, -1):
        first = points[index + 1]
        second = points[index]
        start_theta = theta_for_fraction(
            case, (index + 1) / (len(points) - 1)
        )
        end_theta = theta_for_fraction(case, index / (len(points) - 1))
        start_machine = machine_point(
            first,
            start_theta,
            profile,
            bool(case["compensate"]),
        )
        end_machine = machine_point(
            second,
            end_theta,
            profile,
            bool(case["compensate"]),
        )
        feed_plan = converter.plan_radius_aware_draw_feed(
            first,
            second,
            (0.0, 0.0),
            converter.distance(start_machine, end_machine),
            (end_theta - start_theta) * THETA_RATIO,
            settings,
        )
        emit_g1(
            lines,
            second,
            end_theta,
            feed_plan["feed_rate"],
            profile,
            bool(case["compensate"]),
            "reverse trace",
        )

    emit_pen_up(lines)
    emit_rotating_travel(
        lines,
        points[0],
        start_theta,
        center,
        0.0,
        profile,
        False,
        "rotating pen-up return to witness",
    )
    emit_pen_down(lines, False)
    emit_cross(lines, center, requested_feed, "return witness")
    emit_pen_up(lines)


def build_program(profile) -> str:
    lines = [
        "(bed compensation XY/A tracking test)",
        "(ordinary paper, black Pigma Micron, one file and one Cycle Start)",
        "(layout top to bottom: 1 XY parked, 2 rotating no comp fast, "
        "3 rotating comp fast, 4 rotating no comp slow, 5 rotating comp slow)",
        "(run G65 P113 before this file; do not re-register or move the sheet)",
        "(each initial/return witness and forward/reverse trace should coincide)",
        "(keep $123=6000 and $701=0 for this baseline comparison)",
        "(tolerance 0.150 mm)",
        f"(A limits assumed {fmt(30000.0)} motor deg/min, "
        f"{fmt(6000.0)} motor deg/s^2)",
        f"(bed compensation {profile.fingerprint}, coverage "
        f"{fmt(profile.coverage_radius_mm)} mm, max "
        f"{fmt(profile.max_correction_mm)} mm)",
        "G21",
        "G90",
        "G94",
        "G17",
        "G54",
        "G0 F3000",
        "M5",
        "G65 P115 Q0 A1 W2",
    ]
    first_pen_down = True
    for case in CASES:
        emit_case(lines, case, profile, first_pen_down)
        first_pen_down = False
    lines.extend(
        [
            "M65 P0",
            "G65 P115 Q0 A3 W1",
            "M64 P0",
            "G53 G1 X-10 Y-436 F3000 (park home)",
            "M2",
        ]
    )
    return "\n".join(lines) + "\n"


def check_comments(program: str) -> None:
    for number, line in enumerate(program.splitlines(), 1):
        if line.count("(") != line.count(")"):
            raise ValueError(
                f"line {number} has unbalanced comment: {line!r}"
            )
        if "(" in line and not line.rstrip().endswith(")"):
            raise ValueError(
                f"line {number} has code after a comment: {line!r}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUTPUT),
        help="G-code destination",
    )
    args = parser.parse_args()

    profile = load_profile()
    program = build_program(profile)
    check_comments(program)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(program, encoding="utf-8", newline="\n")
    print(output)


if __name__ == "__main__":
    main()
