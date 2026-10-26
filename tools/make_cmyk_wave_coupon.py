"""Generate a full-sheet black-pen CMYK wave diagnostic.

The single program prints sixteen 54 x 28 mm patches: all four CMYK screen
angles in two rows, comparing phase-locked depth with equidistant rows, then
repeats the matrix with production Xtheta/Ytheta planning. The upper half is
planned with A parked as an isolated geometry control. Everything uses the
production 3.36 mm paper pitch, 0.8 mm pen, F700, and 0.05 mm tolerance.

The matrices fit within a 234 x 142 mm field on one already-mounted 14-inch
sheet. One Cycle Start completes the entire diagnostic without intervention.

``--letter`` writes a separate 8.5 x 11 paper verification matrix: all four
CMYK angles at 2.80, 3.36, and 4.20 mm phase-locked pitch, plus one equidistant
3.36 mm control row. The letter test keeps A parked so it isolates waveform
geometry from bed-motion effects.
"""

from __future__ import annotations

import argparse
import dataclasses
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


DEFAULT_OUTPUT = ROOT / "samples" / "gcode" / "cmyk-wave-coupon.gcode"
DEFAULT_PITCH_OUTPUT = (
    ROOT / "samples" / "gcode" / "cmyk-wave-pitch-coupon.gcode"
)
DEFAULT_LETTER_OUTPUT = (
    ROOT / "samples" / "gcode" / "cmyk-wave-letter-test.gcode"
)
DEFAULT_BED = (
    ROOT
    / "samples"
    / "gcode"
    / "bed-error-compensation-2026-10-23-13p5in-extrapolated.json"
)
PAPER_PITCH_MM = 3.36
PEN_WIDTH_MM = 0.8
PATH_TOLERANCE_MM = 0.05
FEED_MM_MIN = 700.0
PATCH_WIDTH_MM = 54.0
PATCH_HEIGHT_MM = 28.0
PATCH_LEFT_MM = (-117.0, -57.0, 3.0, 63.0)
PATCH_TOP_MM = {
    "fixed": (-72.0, -38.0),
    "optimized": (10.0, 44.0),
}
COUPON_ANGLES = (
    ("C", converter.SCREEN_ANGLES_DEG["c"]),
    ("M", converter.SCREEN_ANGLES_DEG["m"]),
    ("Y", converter.SCREEN_ANGLES_DEG["y"]),
    ("K", converter.SCREEN_ANGLES_DEG["k"]),
)
PITCH_COUPON_MM = (2.80, 3.36, 4.20)
PITCH_PATCH_LEFT_MM = (-97.5, -47.5, 2.5, 52.5)
PITCH_PATCH_TOP_MM = (-72.0, -22.0, 28.0)
PITCH_PATCH_WIDTH_MM = 45.0
PITCH_PATCH_HEIGHT_MM = 44.0
LETTER_PATCH_WIDTH_MM = 50.0
LETTER_PATCH_HEIGHT_MM = 50.0
LETTER_PATCH_LEFT_MM = (-100.0, -50.0, 0.0, 50.0)
LETTER_PATCH_TOP_MM = (-100.0, -50.0, 0.0, 50.0)
LETTER_ROWS = (
    ("waves_zero", 2.80),
    ("waves_zero", 3.36),
    ("waves_zero", 4.20),
    ("waves_even", 3.36),
)


def coupon_settings(theta_mode="fixed"):
    return dataclasses.replace(
        converter.Settings(),
        tolerance=PATH_TOLERANCE_MM,
        pen_diameter_mm=PEN_WIDTH_MM,
        hatch_spacing_mm=0.0,
        fit_mode="manual",
        scale=1.0,
        frame_center_mm=(0.0, 0.0),
        artwork_offset_x_mm=0.0,
        artwork_offset_y_mm=0.0,
        feed_rate=FEED_MM_MIN,
        travel_rate=3000.0,
        theta_mode=str(theta_mode),
        theta_center_hold_diameter_mm=60.0,
        bed_compensation_path=str(DEFAULT_BED),
    )


def coupon_patch(
    style,
    left_mm,
    top_mm,
    width_mm=PATCH_WIDTH_MM,
    height_mm=PATCH_HEIGHT_MM,
    angle_deg=75.0,
    spacing_mm=PAPER_PITCH_MM,
):
    """Return one patch using the real screening and planning functions."""
    yy, xx = np.mgrid[0:128, 0:256]
    tone = np.full((128, 256), 0.82, dtype=np.float32)
    row_step_px = max(
        1.0,
        float(spacing_mm) * 128.0 / max(float(height_mm), 1e-9),
    )
    # Broad two-dimensional luminance variation exposes tone-driven amplitude
    # differences both along and across the wave rows at every screen angle.
    depth = np.clip(
        0.08
        + 0.34 * xx / 255.0
        + 0.42 * yy / 127.0
        + 0.12
        * np.sin(2.0 * np.pi * yy / (12.0 * row_step_px)),
        0.0,
        1.0,
    ).astype(np.float32)
    return converter.screen_channel(
        tone,
        {
            "off_x": float(left_mm),
            "off_y": float(top_mm),
            "width_mm": float(width_mm),
            "height_mm": float(height_mm),
            "pixels_w": 256,
            "pixels_h": 128,
        },
        style=style,
        spacing_mm=float(spacing_mm),
        dot_scale=1.0,
        angle_deg=float(angle_deg),
        pen_diameter_mm=PEN_WIDTH_MM,
        path_tolerance_mm=PATH_TOLERANCE_MM,
        depth_tone=depth,
    )


def _coupon_matrix(theta_mode):
    theta_mode = str(theta_mode).strip().lower()
    if theta_mode not in PATCH_TOP_MM:
        raise ValueError("theta_mode must be 'fixed' or 'optimized'.")
    marks = []
    for top, style in zip(
        PATCH_TOP_MM[theta_mode],
        ("waves_zero", "waves_even"),
    ):
        for left, (_ink, angle_deg) in zip(
            PATCH_LEFT_MM,
            COUPON_ANGLES,
        ):
            marks.extend(
                coupon_patch(
                    style,
                    left,
                    top,
                    angle_deg=angle_deg,
                )
            )
    return marks


def build_pitch_coupon():
    """Build one rotating-bed coupon spanning all supported test pitches."""
    settings = coupon_settings("optimized")
    marks = []
    for pitch_mm, top_mm in zip(PITCH_COUPON_MM, PITCH_PATCH_TOP_MM):
        for left_mm, (_ink, angle_deg) in zip(
            PITCH_PATCH_LEFT_MM,
            COUPON_ANGLES,
        ):
            marks.extend(
                coupon_patch(
                    "waves_zero",
                    left_mm,
                    top_mm,
                    width_mm=PITCH_PATCH_WIDTH_MM,
                    height_mm=PITCH_PATCH_HEIGHT_MM,
                    angle_deg=angle_deg,
                    spacing_mm=pitch_mm,
                )
            )
    plan = converter.plan_program(marks, settings)
    gcode = converter.contours_to_gcode(
        marks,
        settings,
        program_plan=plan,
    )
    banner = (
        "(CMYK wave pitch diagnostic - single file; 12 patches)\n"
        "(columns left-to-right: C15 M75 Y0 K45)\n"
        "(rows top-to-bottom: 2.800 / 3.360 / 4.200 mm pitch)\n"
        "(Xtheta-Ytheta motion, 0.800 mm pen, F700, "
        "bed compensation enabled)\n"
        "(field 195 x 144 mm; ordinary paper is sufficient)\n"
    )
    return banner + gcode, settings, marks


def build_letter_test():
    """Build the phase-locked wave verification for one 8.5 x 11 sheet."""
    settings = coupon_settings("fixed")
    marks = []
    for top_mm, (style, pitch_mm) in zip(
        LETTER_PATCH_TOP_MM,
        LETTER_ROWS,
    ):
        for left_mm, (_ink, angle_deg) in zip(
            LETTER_PATCH_LEFT_MM,
            COUPON_ANGLES,
        ):
            marks.extend(
                coupon_patch(
                    style,
                    left_mm,
                    top_mm,
                    width_mm=LETTER_PATCH_WIDTH_MM,
                    height_mm=LETTER_PATCH_HEIGHT_MM,
                    angle_deg=angle_deg,
                    spacing_mm=pitch_mm,
                )
            )
    plan = converter.plan_program(marks, settings)
    gcode = converter.contours_to_gcode(
        marks,
        settings,
        program_plan=plan,
    )
    banner = (
        "(CMYK phase-locked wave test - 8.5 x 11 paper; 16 patches)\n"
        "(columns left-to-right: C15 M75 Y0 K45)\n"
        "(rows top-to-bottom: phase-locked 2.800 / 3.360 / 4.200 mm; "
        "equidistant 3.360 mm control)\n"
        "(A parked, 0.800 mm black pen, F700, bed compensation enabled)\n"
        "(field 200 x 200 mm centered on the sheet)\n"
    )
    return banner + gcode, settings, marks


def _reindexed_jobs(plan, offset):
    jobs = []
    for planned, points, thetas, strategies in plan["planned_jobs"]:
        renumbered = dict(planned)
        renumbered["index"] = int(renumbered["index"]) + offset
        jobs.append((renumbered, points, thetas, strategies))
    return jobs


def build_coupon():
    fixed_settings = coupon_settings("fixed")
    parked_marks = _coupon_matrix("fixed")
    parked_plan = converter.plan_program(parked_marks, fixed_settings)

    settings = coupon_settings("optimized")
    motion_marks = _coupon_matrix("optimized")
    motion_plan = converter.plan_program(motion_marks, settings)
    parked_count = len(parked_plan["planned_jobs"])
    combined_plan = dict(parked_plan)
    combined_plan["planned_jobs"] = (
        parked_plan["planned_jobs"]
        + _reindexed_jobs(motion_plan, parked_count)
    )
    combined_plan["contours"] = (
        parked_plan["contours"] + motion_plan["contours"]
    )

    marks = parked_marks + motion_marks
    settings = converter.validate_settings(settings)
    gcode = converter.contours_to_gcode(
        marks,
        settings,
        program_plan=combined_plan,
    )
    gcode = re.sub(
        r"\(frame center .* bed motion .*\)",
        "(frame center 0.000,0.000 mm, bed motion: upper A parked + "
        "lower Xtheta/Ytheta)",
        gcode,
        count=1,
    )
    banner = (
        "(CMYK full-sheet wave diagnostic - single file; 16 patches)\n"
        "(columns left-to-right: C15 M75 Y0 K45)\n"
        "(upper 8 patches: A parked; lower 8 patches: Xtheta-Ytheta)\n"
        "(first row of each set: phase-locked depth; second: equidistant)\n"
        "(field 234 x 142 mm centered on the mounted sheet)\n"
        "(effective pitch 3.360 mm, pen 0.800 mm, F700, "
        "bed compensation enabled)\n"
    )
    return banner + gcode, settings, marks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--multi-pitch",
        action="store_true",
        help="generate the 12-patch 2.80/3.36/4.20 mm pitch coupon",
    )
    mode.add_argument(
        "--letter",
        action="store_true",
        help="generate the 16-patch 8.5 x 11 phase-locked wave test",
    )
    args = parser.parse_args()

    if args.letter:
        gcode, settings, marks = build_letter_test()
        output_path = Path(args.out or DEFAULT_LETTER_OUTPUT)
    elif args.multi_pitch:
        gcode, settings, marks = build_pitch_coupon()
        output_path = Path(args.out or DEFAULT_PITCH_OUTPUT)
    else:
        gcode, settings, marks = build_coupon()
        output_path = Path(args.out or DEFAULT_OUTPUT)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(gcode, encoding="utf-8", newline="\n")
    print(output_path)
    print(
        "marks=%d drawing_points=%d columns=%s"
        % (
            len(marks),
            sum(len(mark) for mark in marks),
            (
                settings.theta_axis,
                settings.theta_mode,
                settings.feed_rate,
            ),
        )
    )


if __name__ == "__main__":
    main()
