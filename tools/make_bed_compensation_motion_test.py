"""Generate a comprehensive one-sheet X/Y/A tracking diagnostic.

Every case uses the same bed-space path at three feed requests and draws an A0
witness before and after a rotating pen-up round trip. Cases compare parked-A
controls, compensated versus uncompensated motion, normal versus reverse A
sweeps, X-dominant versus Y-dominant paths, and inner versus mid-radius motion.

The program is one G-code file with one Cycle Start and no M0 pauses. It fits on
letter/A4 paper and uses one black 0.8 mm Pigma Micron.
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
FEED_LADDER_MM_MIN = (350.0, 700.0, 1200.0)
PATH_STEP_MM = 0.6
A_SWEEP_DEG = 14.5
CROSS_ARM_MM = 2.5
WITNESS_GAP_MM = 7.0
TRAVEL_FEED_MM_MIN = 3000.0
FRAME_CORNERS = (
    (-80.0, 125.0),
    (80.0, 125.0),
    (-80.0, -125.0),
    (80.0, -125.0),
)

CASES = (
    {
        "id": 1,
        "name": "XY-only horizontal control",
        "center": (-35.0, -65.0),
        "orientation_deg": 0.0,
        "length_mm": 40.0,
        "amplitude_mm": 1.2,
        "waves": 3.0,
        "rotate": False,
        "compensate": False,
        "sweep_sign": 1,
    },
    {
        "id": 2,
        "name": "XY-only vertical control",
        "center": (0.0, -105.0),
        "orientation_deg": 90.0,
        "length_mm": 36.0,
        "amplitude_mm": 1.0,
        "waves": 3.0,
        "rotate": False,
        "compensate": False,
        "sweep_sign": 1,
    },
    {
        "id": 3,
        "name": "normal sweep uncompensated",
        "center": (-35.0, 120.0),
        "orientation_deg": 0.0,
        "length_mm": 40.0,
        "amplitude_mm": 1.2,
        "waves": 3.0,
        "rotate": True,
        "compensate": False,
        "sweep_sign": 1,
    },
    {
        "id": 4,
        "name": "normal sweep compensated",
        "center": (35.0, 120.0),
        "orientation_deg": 0.0,
        "length_mm": 40.0,
        "amplitude_mm": 1.2,
        "waves": 3.0,
        "rotate": True,
        "compensate": True,
        "sweep_sign": 1,
    },
    {
        "id": 5,
        "name": "reverse sweep uncompensated",
        "center": (-35.0, 75.0),
        "orientation_deg": 0.0,
        "length_mm": 40.0,
        "amplitude_mm": 1.2,
        "waves": 3.0,
        "rotate": True,
        "compensate": False,
        "sweep_sign": -1,
    },
    {
        "id": 6,
        "name": "reverse sweep compensated",
        "center": (35.0, 75.0),
        "orientation_deg": 0.0,
        "length_mm": 40.0,
        "amplitude_mm": 1.2,
        "waves": 3.0,
        "rotate": True,
        "compensate": True,
        "sweep_sign": -1,
    },
    {
        "id": 7,
        "name": "Y-dominant sweep uncompensated",
        "center": (-35.0, 25.0),
        "orientation_deg": 90.0,
        "length_mm": 36.0,
        "amplitude_mm": 1.0,
        "waves": 3.0,
        "rotate": True,
        "compensate": False,
        "sweep_sign": 1,
    },
    {
        "id": 8,
        "name": "Y-dominant sweep compensated",
        "center": (35.0, 25.0),
        "orientation_deg": 90.0,
        "length_mm": 36.0,
        "amplitude_mm": 1.0,
        "waves": 3.0,
        "rotate": True,
        "compensate": True,
        "sweep_sign": 1,
    },
    {
        "id": 9,
        "name": "inner-radius sweep uncompensated",
        "center": (-28.0, -15.0),
        "orientation_deg": 30.0,
        "length_mm": 28.0,
        "amplitude_mm": 0.8,
        "waves": 3.0,
        "rotate": True,
        "compensate": False,
        "sweep_sign": 1,
    },
    {
        "id": 10,
        "name": "inner-radius sweep compensated",
        "center": (28.0, -15.0),
        "orientation_deg": 30.0,
        "length_mm": 28.0,
        "amplitude_mm": 0.8,
        "waves": 3.0,
        "rotate": True,
        "compensate": True,
        "sweep_sign": 1,
    },
    {
        "id": 11,
        "name": "repeat normal sweep compensated",
        "center": (35.0, -65.0),
        "orientation_deg": 0.0,
        "length_mm": 40.0,
        "amplitude_mm": 1.2,
        "waves": 3.0,
        "rotate": True,
        "compensate": True,
        "sweep_sign": 1,
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


def rotate_local(case, u_mm: float, v_mm: float) -> tuple[float, float]:
    angle = math.radians(float(case["orientation_deg"]))
    cosine = math.cos(angle)
    sine = math.sin(angle)
    center_x, center_y = case["center"]
    return (
        center_x + u_mm * cosine - v_mm * sine,
        center_y + u_mm * sine + v_mm * cosine,
    )


def path_points(case) -> list[tuple[float, float]]:
    length = float(case["length_mm"])
    amplitude = float(case["amplitude_mm"])
    waves = float(case["waves"])
    count = max(1, int(round(length / PATH_STEP_MM)))
    points = []
    for index in range(count + 1):
        fraction = index / count
        u_mm = -length / 2.0 + length * fraction
        v_mm = amplitude * math.sin(2.0 * math.pi * waves * fraction)
        points.append(rotate_local(case, u_mm, v_mm))
    return points


def witness_point(case) -> tuple[float, float]:
    return rotate_local(
        case,
        -float(case["length_mm"]) / 2.0 - WITNESS_GAP_MM,
        0.0,
    )


def theta_for_fraction(case, fraction: float) -> float:
    if not case["rotate"]:
        return 0.0
    return float(case["sweep_sign"]) * A_SWEEP_DEG * (
        2.0 * fraction - 1.0
    )


def case_settings(feed_mm_min: float):
    return dataclasses.replace(
        converter.Settings(),
        feed_rate=float(feed_mm_min),
        theta_tangential_speed_mm_min=float(feed_mm_min),
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


def emit_fixed_travel(
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


def emit_frame(lines: list[str], feed: float) -> None:
    for index, center in enumerate(FRAME_CORNERS, start=1):
        emit_cross(lines, center, feed, f"frame witness {index}")


def trace_pass(
    lines: list[str],
    case,
    points: list[tuple[float, float]],
    feed_mm_min: float,
    profile,
    reverse_path: bool,
) -> None:
    settings = case_settings(feed_mm_min)
    if reverse_path:
        indices = range(len(points) - 2, -1, -1)
        label = "reverse trace"
    else:
        indices = range(len(points) - 1)
        label = "forward trace"
    for index in indices:
        first_index = index + 1 if reverse_path else index
        second_index = index if reverse_path else index + 1
        first = points[first_index]
        second = points[second_index]
        start_fraction = first_index / (len(points) - 1)
        end_fraction = second_index / (len(points) - 1)
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
            label,
        )


def emit_case(lines: list[str], case, profile, first_pen_down: bool) -> None:
    points = path_points(case)
    witness = witness_point(case)
    start_theta = theta_for_fraction(case, 0.0)
    feed_text = "/".join(fmt(feed) for feed in FEED_LADDER_MM_MIN)
    lines.append(
        f"(case {case['id']}: {case['name']}; center "
        f"{fmt(case['center'][0])},{fmt(case['center'][1])} mm; "
        f"orientation {fmt(case['orientation_deg'])} deg; "
        f"feed ladder {feed_text} mm/min)"
    )

    emit_fixed_travel(
        lines,
        witness,
        0.0,
        profile,
        False,
        "travel to case witness",
    )
    emit_pen_down(lines, first_pen_down)
    emit_cross(lines, witness, FEED_LADDER_MM_MIN[1], "initial witness")
    emit_pen_up(lines)

    emit_rotating_travel(
        lines,
        witness,
        0.0,
        points[0],
        start_theta,
        profile,
        bool(case["compensate"]),
        "pen-up transition to path",
    )
    emit_pen_down(lines, False)
    for feed_mm_min in FEED_LADDER_MM_MIN:
        lines.append(f"(feed pass {fmt(feed_mm_min)} mm/min)")
        trace_pass(
            lines,
            case,
            points,
            feed_mm_min,
            profile,
            reverse_path=False,
        )
        trace_pass(
            lines,
            case,
            points,
            feed_mm_min,
            profile,
            reverse_path=True,
        )
    emit_pen_up(lines)

    emit_rotating_travel(
        lines,
        points[0],
        start_theta,
        witness,
        0.0,
        profile,
        bool(case["compensate"]),
        "pen-up return to witness",
    )
    emit_pen_down(lines, False)
    emit_cross(lines, witness, FEED_LADDER_MM_MIN[1], "return witness")
    emit_pen_up(lines)


def build_program(profile) -> str:
    feed_text = "/".join(fmt(feed) for feed in FEED_LADDER_MM_MIN)
    lines = [
        "(comprehensive bed compensation XY/A tracking test)",
        "(letter or A4 paper, black 0.8 mm Pigma Micron)",
        "(one file, one Cycle Start, no M0 pauses)",
        "(run G65 P113 before this file; do not re-register or move the sheet)",
        "(each case redraws the same path at the three feed requests)",
        "(initial and return witness crosses should overlay)",
        "(forward and reverse traces from every feed pass should overlay)",
        f"(feed ladder {feed_text} mm/min)",
        "(top pair 3/4 normal, next pair 5/6 reverse, then 7/8 vertical)",
        "(middle pair 9/10 inner radius; lower-left 1 control, "
        "lower-right 11 repeat; bottom 2 vertical control)",
        "(four corner frame crosses are drawn at A0 before and after all cases)",
        "(keep $113=30000, $123=6000, $376=1, $701=0)",
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

    emit_pen_down(lines, True)
    emit_frame(lines, FEED_LADDER_MM_MIN[1])
    emit_pen_up(lines)
    for case in CASES:
        emit_case(lines, case, profile, False)
    lines.append("(final frame recheck)")
    emit_pen_down(lines, False)
    emit_frame(lines, FEED_LADDER_MM_MIN[1])
    emit_pen_up(lines)

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
