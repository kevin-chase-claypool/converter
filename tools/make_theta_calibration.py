"""Write a G-code pattern that measures the bed's real degrees-per-motor-degree.

The converter turns bed angles into motor degrees with
``settings.theta_drive_ratio``. If that number is wrong the whole drawing is
stretched around the bed, and the error grows with every revolution - which
looks exactly like "drift".

This pattern makes the error visible and measurable with a ruler:

* one long radial mark at bed angle 0,
* eight shorter ticks at 45 degree intervals (one full commanded turn),
* the same long mark again at 0 after exactly **one** commanded revolution,
* the same mark, longer still, after exactly **two** commanded revolutions.

If the ratio is right, all three marks lie on top of each other and print as a
single line. If the bed under- or over-rotates, the second and third marks fan
away from the first, and the gap doubles from the first turn to the second -
which is how you tell a ratio error from backlash.

Measure the gap ``s`` (mm) between the first and second mark at radius ``R``
(mm, from the centre of the bed to the middle of the marks):

    error_degrees = degrees(atan(s / R))
    true_ratio    = assumed_ratio * 360 / (360 + error_degrees)

Usage::

    python tools\\make_theta_calibration.py
    python tools\\make_theta_calibration.py --out samples\\gcode\\theta-calibration.gcode
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter  # noqa: E402


def radial(angle_deg, inner, outer, samples=24):
    """A radial stroke in bed coordinates at *angle_deg*."""
    radians = math.radians(angle_deg)
    points = []
    for index in range(samples + 1):
        radius = inner + (outer - inner) * index / samples
        points.append((radius * math.cos(radians), radius * math.sin(radians)))
    return points


def build_pattern(inner_short=110.0, inner_long=60.0, outer=170.0):
    """Contours for the calibration pattern, in bed coordinates.

    The bed angle follows the direction of travel, so a circle costs exactly
    one bed revolution and a two-turn spiral costs two. If the ratio is wrong
    the bed under- or over-rotates through those turns and the spiral cannot
    close: the gap at the seam is the error, doubled on the second lap, which
    is what tells a ratio error apart from backlash.
    """
    contours = [radial(0.0, inner_long, outer)]
    for step in range(1, 8):
        contours.append(radial(45.0 * step, inner_short, outer))
    contours.append(circle(150.0))
    contours.append(spiral(120.0, 170.0, turns=2.0))
    return contours


def circle(radius, samples=240):
    """A full circle in bed coordinates: one bed revolution per lap."""
    return [
        (
            radius * math.cos(2.0 * math.pi * index / samples),
            radius * math.sin(2.0 * math.pi * index / samples),
        )
        for index in range(samples + 1)
    ]


def spiral(inner, outer, turns=2.0, samples=480):
    """A multi-turn spiral: one bed revolution per turn of the path."""
    points = []
    for index in range(samples + 1):
        t = index / samples
        angle = 2.0 * math.pi * turns * t
        radius = inner + (outer - inner) * t
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "gcode" / "theta-calibration.gcode"),
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=None,
        help="assumed ratio; defaults to the converter's current setting",
    )
    args = parser.parse_args()

    settings = converter.Settings()
    if args.ratio is not None:
        settings = __import__("dataclasses").replace(
            settings, theta_drive_ratio=float(args.ratio)
        )
    contours = build_pattern()
    plan = converter.plan_program(contours, settings)
    gcode = converter.contours_to_gcode(contours, settings, plan)

    header = (
        "(theta calibration pattern)\n"
        "(ratio used: %.5f motor deg per bed deg)\n"
        "(marks at bed angle 0: start, after +360 commanded deg, after +720)\n"
        "(if the three marks do not land on each other, the ratio is wrong)\n"
    ) % settings.theta_drive_ratio
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(header + gcode, encoding="utf-8")

    a_values = [
        float(token[1:])
        for line in gcode.splitlines()
        for token in line.split()
        if token.startswith("A")
    ]
    turns = (max(a_values) - min(a_values)) / (settings.theta_drive_ratio * 360.0)
    print(
        "wrote %s\n  ratio %.5f, A spans %.1f motor deg over %.2f bed revolutions"
        % (out, settings.theta_drive_ratio, max(a_values) - min(a_values), turns)
    )


if __name__ == "__main__":
    main()
