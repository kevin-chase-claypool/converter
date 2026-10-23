"""Rotation-centre cross test and P100 correction fit."""

import math
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter
from converter_core.rotation_calibration import (
    RotationCenterMeasurement,
    build_rotation_center_test_program,
    center_error,
    corrected_axis_center,
    current_axis_center_correction,
    fit_rotation_center,
    parse_measurement,
)


class RotationCenterTests(unittest.TestCase):
    def test_error_doubles_at_half_turn(self):
        self.assertEqual(center_error(0.0, 0.4, -0.7), (0.0, 0.0))
        measured_x, measured_y = center_error(180.0, 0.4, -0.7)
        self.assertAlmostEqual(measured_x, 0.8, places=12)
        self.assertAlmostEqual(measured_y, -1.4, places=12)

    def test_fit_recovers_center_from_three_quadrants(self):
        expected = (0.35, -0.6)
        measurements = [
            RotationCenterMeasurement(90.0, 0.95, -0.25),
            RotationCenterMeasurement(180.0, 0.70, -1.20),
            RotationCenterMeasurement(270.0, -0.25, -0.95),
        ]
        fit = fit_rotation_center(measurements)
        self.assertAlmostEqual(fit.center_x_mm, expected[0], places=12)
        self.assertAlmostEqual(fit.center_y_mm, expected[1], places=12)
        self.assertAlmostEqual(fit.rms_error_mm, 0.0, places=12)
        self.assertAlmostEqual(fit.max_error_mm, 0.0, places=12)

    def test_half_turn_two_axis_measurement_is_sufficient(self):
        measurements = [parse_measurement("180,1.2,-0.8")]
        fit = fit_rotation_center(measurements)
        self.assertAlmostEqual(fit.center_x_mm, 0.6, places=12)
        self.assertAlmostEqual(fit.center_y_mm, -0.4, places=12)

    def test_degenerate_angle_set_is_rejected(self):
        measurements = [
            RotationCenterMeasurement(0.0, 1.0, 1.0),
            RotationCenterMeasurement(0.0, 1.0, 1.0),
        ]
        with self.assertRaises(ValueError):
            fit_rotation_center(measurements)

    def test_non_centre_translation_is_reported_as_residual(self):
        measurements = [
            RotationCenterMeasurement(angle, 0.5, 0.5)
            for angle in (90.0, 180.0, 270.0)
        ]
        fit = fit_rotation_center(measurements)
        self.assertGreater(fit.max_error_mm, 0.2)

    def test_correction_adds_residual_to_current_p100_constants(self):
        fit = fit_rotation_center(
            [parse_measurement("180,-1.2,0.8")]
        )
        self.assertEqual(
            tuple(round(value, 8) for value in corrected_axis_center(2.45, 0.3, fit)),
            (1.85, 0.7),
        )

    def test_current_macro_values_are_parsed(self):
        text = (
            "#<axis_center_correction_x> = 2.45\n"
            "#<axis_center_correction_y> = 0.3\n"
        )
        self.assertEqual(current_axis_center_correction(text), (2.45, 0.3))


class RotationCenterProgramTests(unittest.TestCase):
    def test_program_contains_reference_controls_and_quadrant_replays(self):
        program, passes = build_rotation_center_test_program(
            converter.Settings(),
            arm_mm=32.0,
            arm_step_mm=3.0,
            angles=(90.0, 180.0, 270.0),
            control_passes=1,
            closing=True,
        )
        self.assertEqual(
            [name for name, _, _ in passes],
            ["reference", "control 1", "replay 90", "replay 180", "replay 270", "closing"],
        )
        self.assertIn("(reference cross:", program)
        self.assertIn("(replay 180 cross:", program)
        self.assertIn("(control 1 cross:", program)
        self.assertIn("arrowheads point machine +X and +Y", program)
        self.assertEqual(program.count("("), program.count(")"))

    def test_program_arm_lengths_are_ordered_and_clear(self):
        _program, passes = build_rotation_center_test_program(
            converter.Settings(),
            arm_mm=30.0,
            arm_step_mm=2.0,
        )
        halves = [half for _, _, half in passes]
        self.assertEqual(halves, sorted(halves, reverse=True))
        self.assertGreaterEqual(min(halves), 10.0)

    def test_default_layout_fits_14_inch_round_sheet(self):
        program, passes = build_rotation_center_test_program(converter.Settings())
        self.assertEqual(passes[0][2], 165.1)
        self.assertIn("330.2 mm test on 355.6 mm round stock", program)
        self.assertIn("largest ink radius 165.1 mm", program)

    def test_oversized_cross_for_sheet_is_rejected(self):
        with self.assertRaises(ValueError):
            build_rotation_center_test_program(
                converter.Settings(),
                arm_mm=170.0,
                sheet_diameter_mm=355.6,
                test_diameter_mm=330.2,
                edge_margin_mm=10.0,
            )

    def test_invalid_short_arm_is_rejected(self):
        with self.assertRaises(ValueError):
            build_rotation_center_test_program(
                converter.Settings(), arm_mm=30.0, arm_step_mm=5.0
            )

    def test_every_replay_uses_its_indexed_bed_angle(self):
        settings = converter.Settings()
        program, _passes = build_rotation_center_test_program(
            settings,
            arm_mm=30.0,
            arm_step_mm=2.0,
            angles=(90.0, 180.0, 270.0),
            control_passes=0,
            closing=False,
        )
        a_values = {
            round(float(value), 4)
            for value in (
                line.split("A", 1)[1].split()[0]
                for line in program.splitlines()
                if line.startswith(("G0 X", "G1 X")) and " A" in line
            )
        }
        for angle in (0.0, 90.0, 180.0, 270.0):
            self.assertIn(round(angle * settings.theta_drive_ratio, 4), a_values)

    def test_fit_rejects_empty_measurements(self):
        with self.assertRaises(ValueError):
            fit_rotation_center([])

    def test_center_error_is_unit_vector_rotation(self):
        x, y = center_error(90.0, 1.0, 0.0)
        self.assertAlmostEqual(x, 1.0, places=12)
        self.assertAlmostEqual(y, 1.0, places=12)
        self.assertAlmostEqual(math.hypot(x, y), math.sqrt(2.0), places=12)


if __name__ == "__main__":
    unittest.main()
