"""The kinematic either/or: Xθ/Yθ rotates the bed; XY only parks it.

XY only (`theta_mode = "fixed"`) holds one bed angle for the whole program,
so the gantry draws the artwork unchanged and the bed cannot add rotation
error. It is the operator's precision option after the bed-tilt
investigation; Xθ/Yθ keeps today's rotating-bed solver. The Qt sidebar and
the CMYK tab both present the choice as a two-bullet radio pair.
"""

import dataclasses
import importlib.util
import math
import os
import re
import sys
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


try:
    from PySide6.QtWidgets import QApplication

    from generator_tabs._tab_common import ChoiceBullets

    HAVE_QT = True
except Exception:  # pragma: no cover - the core tests do not need Qt
    HAVE_QT = False


A_WORD = re.compile(r"A(-?\d+\.?\d*)")


def _design():
    """A spiral plus four radial marks, in millimetres."""
    samples = 120
    spiral = [
        (
            (60.0 + 60.0 * t) * math.cos(2.0 * math.pi * t),
            (60.0 + 60.0 * t) * math.sin(2.0 * math.pi * t),
        )
        for t in (index / samples for index in range(samples + 1))
    ]
    marks = []
    for step in range(4):
        angle = math.radians(90.0 * step + 20.0)
        marks.append(
            [
                (
                    (80.0 + 40.0 * index / 10) * math.cos(angle),
                    (80.0 + 40.0 * index / 10) * math.sin(angle),
                )
                for index in range(11)
            ]
        )
    return [spiral] + marks


def _emit(mode, **overrides):
    settings = dataclasses.replace(converter.Settings(), theta_mode=mode, **overrides)
    contours = _design()
    plan = converter.plan_program(contours, settings)
    return settings, plan, converter.contours_to_gcode(contours, settings, plan)


def _a_words(text):
    values = []
    for line in text.splitlines():
        if line.startswith(("G0 ", "G1 ", "G53 ")):
            values.extend(
                float(match.group(1)) for match in A_WORD.finditer(line)
            )
    return values


class XyOnlyKinematicsTests(unittest.TestCase):
    def test_xy_only_emits_one_constant_angle(self):
        _settings, _plan, text = _emit("fixed")
        values = _a_words(text)
        self.assertGreater(len(values), 50, "the program should command A")
        self.assertEqual(
            sorted({round(value, 4) for value in values}),
            [0.0],
            "XY only must never rotate the bed",
        )

    def test_xy_only_holds_the_theta_offset_angle(self):
        settings, _plan, text = _emit("fixed", theta_offset=15.0)
        expected = 15.0 * settings.theta_drive_ratio
        values = sorted({round(value, 4) for value in _a_words(text)})
        self.assertEqual(len(values), 1, "the parked bed has one angle")
        self.assertAlmostEqual(values[0], expected, places=3)

    def test_xy_only_keeps_every_planned_theta_at_the_offset(self):
        _settings, plan, _text = _emit("fixed")
        for _planned, _points, thetas, strategies in plan["planned_jobs"]:
            self.assertEqual(set(thetas), {0.0})
            self.assertEqual(
                {label for label in strategies if label} - {"fixed"}, set()
            )

    def test_xy_only_draws_the_bed_points_unchanged(self):
        _settings, plan, text = _emit("fixed")
        first_point = plan["planned_jobs"][0][1][0]
        travel = re.search(
            r"^G1 X(-?\d+\.?\d*) Y(-?\d+\.?\d*) A(-?\d+\.?\d*) .*\(travel\)$",
            text,
            flags=re.MULTILINE,
        )
        self.assertIsNotNone(travel, "the program should reposition to a start")
        self.assertAlmostEqual(float(travel.group(1)), first_point[0], places=3)
        self.assertAlmostEqual(float(travel.group(2)), first_point[1], places=3)
        self.assertAlmostEqual(float(travel.group(3)), 0.0, places=6)

    def test_rotating_mode_sweeps_many_angles(self):
        _settings, _plan, text = _emit("optimized")
        values = {round(value, 4) for value in _a_words(text)}
        self.assertGreater(len(values), 20, "Xθ/Yθ should sweep the bed")


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class ChoiceBulletsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_choice_bullets_round_trip_values(self):
        widget = ChoiceBullets(converter.THETA_MODE_CHOICES, "optimized")
        self.addCleanup(widget.deleteLater)
        self.assertEqual(
            [button.property("choice_value") for button in widget._buttons],
            ["optimized", "fixed"],
        )
        self.assertEqual(widget.value(), "optimized")
        seen = []
        widget.changed.connect(seen.append)
        widget.set_value("fixed")
        self.assertEqual(widget.value(), "fixed")
        self.assertEqual(seen, ["fixed"])

    def test_choice_bullets_fall_back_to_the_first_choice(self):
        widget = ChoiceBullets(converter.THETA_MODE_CHOICES, "tangent")
        self.addCleanup(widget.deleteLater)
        self.assertEqual(widget.value(), "optimized")


def _load_app_module():
    path = Path(__file__).resolve().parents[1] / "qt_svg_to_gcode.pyw"
    spec = importlib.util.spec_from_file_location("qt_svg_to_gcode_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class SidebarKinematicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()

    def test_the_sidebar_offers_the_two_bullets(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        widget = window.fields["theta_mode"]
        self.assertIsInstance(widget, ChoiceBullets)
        self.assertEqual(
            [button.property("choice_value") for button in widget._buttons],
            ["optimized", "fixed"],
        )
        self.assertEqual(window.settings().theta_mode, "optimized")
        widget.set_value("fixed")
        self.assertEqual(window.settings().theta_mode, "fixed")


if __name__ == "__main__":
    unittest.main()
