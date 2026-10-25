"""Generate a small black-pen comparison of the two CMYK wave modes.

The left 28 x 20 mm patch is the original variable-depth Wave screen. The
right patch is Wave screen - equidistant rows. Both use the current production
effective pitch of 3.36 mm, feed 700 mm/min, and Path tolerance 0.05 mm.

The bed is parked for this geometry coupon so it can be printed on ordinary
paper near bed center without consuming a CMYK layer.
"""

from __future__ import annotations

import argparse
import dataclasses
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


DEFAULT_OUTPUT = ROOT / "samples" / "gcode" / "cmyk-wave-coupon.gcode"
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


def coupon_settings():
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
        theta_mode="fixed",
        theta_center_hold_diameter_mm=60.0,
        bed_compensation_path=str(DEFAULT_BED),
    )


def coupon_patch(style, left_mm, top_mm, width_mm=28.0, height_mm=20.0):
    """Return one patch using the real screening and planning functions."""
    yy, xx = np.mgrid[0:96, 0:128]
    tone = np.full((96, 128), 0.82, dtype=np.float32)
    # Broad two-dimensional luminance variation makes the original mode's
    # changing row amplitudes visible without adding row-frequency noise.
    depth = np.clip(
        0.12
        + 0.58 * xx / 127.0
        + 0.22 * yy / 95.0
        + 0.06 * np.sin(2.0 * np.pi * yy / 7.0),
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
            "pixels_w": 128,
            "pixels_h": 96,
        },
        style=style,
        spacing_mm=PAPER_PITCH_MM,
        dot_scale=1.0,
        angle_deg=75.0,
        pen_diameter_mm=PEN_WIDTH_MM,
        path_tolerance_mm=PATH_TOLERANCE_MM,
        depth_tone=depth,
    )


def build_coupon():
    settings = coupon_settings()
    marks = coupon_patch("waves", -34.0, -10.0)
    marks.extend(coupon_patch("waves_even", 6.0, -10.0))
    settings = converter.validate_settings(settings)
    gcode = converter.contours_to_gcode(marks, settings)
    banner = (
        "(CMYK wave coupon - black pen; ordinary paper is sufficient)\n"
        "(left 28x20 mm: original Wave screen, variable row depth)\n"
        "(right 28x20 mm: Wave screen - equidistant rows)\n"
        "(effective pitch 3.360 mm, pen 0.800 mm, F700, A parked)\n"
    )
    return banner + gcode, settings, marks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    gcode, settings, marks = build_coupon()
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(gcode, encoding="utf-8", newline="\n")
    print(output)
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
