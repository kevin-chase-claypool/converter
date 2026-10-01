"""Re-registering the bed each contour keeps the commanded A small.

The operator sees drift grow with the A value shown in ioSender's DRO. A bed
angle has no absolute multi-turn reference, so subtracting whole revolutions
leaves the drawing identical while keeping |A| near zero - which bounds any
A-axis scale error instead of letting it accumulate over the program.
"""

import dataclasses
import math
import re
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


XYA = re.compile(r"X(-?\d+\.?\d*) Y(-?\d+\.?\d*) A(-?\d+\.?\d*)")


def _winding_design():
    """A two-turn spiral followed by short radial marks.

    Tracing the spiral costs two bed revolutions, so without re-registration
    every contour after it is commanded at about 9000 motor degrees - the
    condition the operator sees as drift. With re-registration those contours
    come back to about zero.
    """
    samples = 240
    spiral = [
        (
            (90.0 + 80.0 * t) * math.cos(2.0 * math.pi * 2.0 * t),
            (90.0 + 80.0 * t) * math.sin(2.0 * math.pi * 2.0 * t),
        )
        for t in (index / samples for index in range(samples + 1))
    ]
    marks = []
    for step in range(1, 7):
        angle = math.radians(45.0 * step)
        marks.append(
            [
                (
                    (120.0 + 50.0 * index / 12) * math.cos(angle),
                    (120.0 + 50.0 * index / 12) * math.sin(angle),
                )
                for index in range(13)
            ]
        )
    return [spiral] + marks


def _first_a_per_contour(text):
    """The first commanded A of each contour, in program order."""
    values = []
    pending = True
    for line in text.splitlines():
        if line.startswith("(contour"):
            pending = True
            continue
        if pending and ("G0 " in line or "G1 " in line):
            match = re.search(r"A(-?\d+\.?\d*)", line)
            if match:
                values.append(float(match.group(1)))
                pending = False
    return values


def _emit(contours, **overrides):
    settings = dataclasses.replace(converter.Settings(), **overrides)
    plan = converter.plan_program(contours, settings)
    text = converter.contours_to_gcode(contours, settings, plan)
    moves = [
        (float(a), float(b), float(c)) for a, b, c in XYA.findall(text)
    ]
    return settings, moves, text


class ThetaWrapTests(unittest.TestCase):
    def test_wrap_keeps_the_commanded_angle_bounded(self):
        settings, _, text = _emit(_winding_design())
        firsts = _first_a_per_contour(text)
        self.assertEqual(len(firsts), 7, "one spiral plus six marks")
        limit = settings.theta_drive_ratio * 180.0  # half a bed turn
        self.assertLess(
            max(abs(value) for value in firsts),
            limit,
            "every contour should start within half a turn of zero",
        )

    def test_without_wrap_the_angle_winds_further(self):
        settings, _, text = _emit(_winding_design(), theta_wrap=False)
        firsts = _first_a_per_contour(text)
        turn = settings.theta_drive_ratio * 360.0
        self.assertGreater(
            max(abs(value) for value in firsts),
            turn,
            "without re-registration the marks after the spiral stay wound up",
        )

    def test_the_drawing_is_unchanged(self):
        settings, wrapped, _ = _emit(_winding_design())
        _, plain, _ = _emit(_winding_design(), theta_wrap=False)
        self.assertEqual(len(wrapped), len(plain))
        for index, (one, other) in enumerate(zip(wrapped, plain)):
            self.assertAlmostEqual(one[0], other[0], places=3, msg="X at %d" % index)
            self.assertAlmostEqual(one[1], other[1], places=3, msg="Y at %d" % index)
            delta = one[2] - other[2]
            revolutions = delta / (settings.theta_drive_ratio * 360.0)
            self.assertAlmostEqual(
                revolutions,
                round(revolutions),
                places=6,
                msg="A difference must be whole bed revolutions at %d" % index,
            )

    def test_the_setting_defaults_on(self):
        self.assertTrue(converter.Settings().theta_wrap)


if __name__ == "__main__":
    unittest.main()
