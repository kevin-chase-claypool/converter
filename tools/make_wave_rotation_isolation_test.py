"""Generate a one-sheet CMYK wave test that isolates bed rotation.

Both output files use the same four-row wave geometry. The sheet remains
taped for both runs:

* base pass: parked A0 control, +5/+10 degree rotation cases, a +14.5 degree
  baseline, the same rotation at reduced feed, and a reverse rotation;
* reduced-A-acceleration pass: its own parked control plus a +14.5 degree
  case to run after changing ``$123`` from 6000 to 600.

The paper stays mounted, and ``G65 P113`` is needed only before the base
pass. The base pass parks safely at the end; run the second file without
re-registering or moving the sheet.
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


DEFAULT_BED = (
    ROOT
    / "samples"
    / "gcode"
    / "bed-error-compensation-2026-10-23-13p5in-extrapolated.json"
)
RATIO = 12.03324
ROWS = 4
ROW_PITCH_MM = 3.0
HALF_WIDTH_MM = 9.0
AMPLITUDE_MM = 1.0
WAVELENGTH_MM = 6.0
SAMPLE_STEP_MM = 0.5

CASES = (
    {
        "id": 1,
        "name": "parked A0 control",
        "center": (-35.0, 30.0),
        "delta_deg": 0.0,
        "feed": 700.0,
        "pass": "base",
    },
    {
        "id": 2,
        "name": "small rotation",
        "center": (0.0, 30.0),
        "delta_deg": 5.0,
        "feed": 700.0,
        "pass": "base",
    },
    {
        "id": 3,
        "name": "medium rotation",
        "center": (35.0, 30.0),
        "delta_deg": 10.0,
        "feed": 700.0,
        "pass": "base",
    },
    {
        "id": 4,
        "name": "large rotation baseline",
        "center": (-35.0, 0.0),
        "delta_deg": 14.5,
        "feed": 700.0,
        "pass": "base",
    },
    {
        "id": 5,
        "name": "large rotation reduced feed",
        "center": (0.0, 0.0),
        "delta_deg": 14.5,
        "feed": 350.0,
        "pass": "base",
    },
    {
        "id": 6,
        "name": "large reverse rotation baseline",
        "center": (35.0, 0.0),
        "delta_deg": -14.5,
        "feed": 700.0,
        "pass": "base",
    },
    {
        "id": 7,
        "name": "second-pass parked control",
        "center": (-35.0, -30.0),
        "delta_deg": 0.0,
        "feed": 700.0,
        "pass": "low-a-accel",
    },
    {
        "id": 8,
        "name": "large rotation reduced A acceleration",
        "center": (0.0, -30.0),
        "delta_deg": 14.5,
        "feed": 700.0,
        "pass": "low-a-accel",
    },
)


def fmt(value):
    return converter.format_float(float(value))


def profile():
    return converter.BedCompensationProfile.from_json(
        DEFAULT_BED.read_text(encoding="utf-8")
    )


def machine_point(bed_compensation, point, theta_deg):
    return converter.compensated_machine_point(
        point, theta_deg, (0.0, 0.0), bed_compensation
    )


def emit_travel(lines, bed_compensation, point):
    x_mm, y_mm = machine_point(bed_compensation, point, 0.0)
    lines.append(
        f"G1 X{fmt(x_mm)} Y{fmt(y_mm)} A0 F3000 (travel)"
    )


def emit_patch(lines, bed_compensation, case):
    center_x, center_y = case["center"]
    delta_deg = float(case["delta_deg"])
    settings = dataclasses.replace(
        converter.Settings(),
        feed_rate=float(case["feed"]),
        theta_tangential_speed_mm_min=float(case["feed"]),
    )
    lines.append(
        f"(case {case['id']}: {case['name']}; "
        f"center {fmt(center_x)},{fmt(center_y)}; "
        f"A delta {fmt(delta_deg)} deg; requested F{fmt(case['feed'])})"
    )
    sample_count = (
        int(round((2.0 * HALF_WIDTH_MM) / SAMPLE_STEP_MM)) + 1
    )
    for row_index in range(ROWS):
        row_baseline = (
            center_y + (row_index - (ROWS - 1) / 2.0) * ROW_PITCH_MM
        )
        start_x = center_x - HALF_WIDTH_MM
        start_phase = (
            2.0 * math.pi * (start_x - center_x) / WAVELENGTH_MM
        )
        start_bed = (
            start_x,
            row_baseline + AMPLITUDE_MM * math.sin(start_phase),
        )
        end_x = center_x + HALF_WIDTH_MM
        end_phase = (
            2.0 * math.pi * (end_x - center_x) / WAVELENGTH_MM
        )
        end_bed = (
            end_x,
            row_baseline + AMPLITUDE_MM * math.sin(end_phase),
        )
        start_machine = machine_point(bed_compensation, start_bed, 0.0)
        end_machine = machine_point(
            bed_compensation, end_bed, delta_deg
        )
        feed_plan = converter.plan_radius_aware_draw_feed(
            start_bed,
            end_bed,
            (0.0, 0.0),
            converter.distance(start_machine, end_machine),
            delta_deg * RATIO,
            settings,
        )
        feed = feed_plan["feed_rate"]
        emit_travel(lines, bed_compensation, start_bed)
        points = []
        for sample_index in range(sample_count):
            fraction = sample_index / (sample_count - 1)
            x_mm = (
                center_x
                - HALF_WIDTH_MM
                + fraction * 2.0 * HALF_WIDTH_MM
            )
            phase = 2.0 * math.pi * (x_mm - center_x) / WAVELENGTH_MM
            y_mm = row_baseline + AMPLITUDE_MM * math.sin(phase)
            theta_deg = delta_deg * fraction
            points.append(
                (
                    machine_point(
                        bed_compensation, (x_mm, y_mm), theta_deg
                    ),
                    theta_deg,
                )
            )
        lines.append("M3")
        lines.append("G65 P115 Q1 B12 A1 W2")
        lines.append(f"G1 F{fmt(feed)}")
        for (x_mm, y_mm), theta_deg in points[1:]:
            lines.append(
                f"G1 X{fmt(x_mm)} Y{fmt(y_mm)} "
                f"A{fmt(theta_deg * RATIO)} F{fmt(feed)}"
            )
        lines.append("M5")
        lines.append("G65 P115 Q1 A1 W2")


def preamble(title, extra_comments=()):
    lines = [
        f"({title})",
        "(one sheet: do not remove, move, or re-tape the paper between runs)",
        "(run G65 P113 once before the base file; do not re-register for pass two)",
        "(case layout: top-left 1, top-centre 2, top-right 3)",
        "(middle-left 4, middle-centre 5, middle-right 6)",
        "(bottom-left 7 and bottom-centre 8 in the reduced-A-acceleration pass)",
        *extra_comments,
        "G21",
        "G90",
        "G94",
        "G17",
        "G54",
        "G0 F3000",
        "M5",
        "G65 P115 Q0 A1 W2",
    ]
    return lines


def ending(lines):
    lines.extend(
        [
            "M65 P0",
            "G65 P115 Q0 A3 W1",
            "M64 P0",
            "G53 G1 X-10 Y-436 F3000 (park home)",
            "M2",
        ]
    )


def build_programs(bed_compensation):
    base = preamble(
        "CMYK wave rotation isolation - base six-patch pass",
        (
            "(inspect and photograph before changing any controller setting)",
            "(then keep the sheet mounted for the reduced-A-acceleration pass)",
        ),
    )
    low = preamble(
        "CMYK wave rotation isolation - reduced A acceleration pass",
        (
            "(before Cycle Start: set $123=600 in the ioSender console)",
            "(confirm $$ reports $123=600; do not re-register or move the paper)",
            "(this file draws cases 7 and 8; restore $123=6000 afterward)",
        ),
    )
    for case in CASES:
        emit_patch(
            base if case["pass"] == "base" else low,
            bed_compensation,
            case,
        )
    ending(base)
    ending(low)
    return "\n".join(base) + "\n", "\n".join(low) + "\n"


def check_comments(program):
    for number, line in enumerate(program.splitlines(), 1):
        if line.count("(") != line.count(")"):
            raise ValueError(f"line {number} has unbalanced comment: {line!r}")
        if "(" in line and not line.rstrip().endswith(")"):
            raise ValueError(f"line {number} has code after a comment: {line!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        default=str(ROOT / "samples" / "gcode"),
    )
    args = parser.parse_args()

    bed_compensation = profile()
    base_text, low_text = build_programs(bed_compensation)
    check_comments(base_text)
    check_comments(low_text)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = (
        out_dir / "wave-rotation-isolation-base.gcode",
        out_dir / "wave-rotation-isolation-low-a-accel.gcode",
    )
    for path, text in zip(paths, (base_text, low_text)):
        path.write_text(text, encoding="utf-8", newline="\n")
        print(path)


if __name__ == "__main__":
    main()
