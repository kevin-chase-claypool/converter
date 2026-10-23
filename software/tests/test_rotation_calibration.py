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
    measurement_template_csv,
    parse_measurement,
    parse_measurements_csv,
    remove_control_bias,
    remove_pair_baseline,
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

    def test_pair_baseline_is_removed_from_raw_gaps(self):
        corrected = remove_pair_baseline(
            [parse_measurement("90,20.6,19.4")],
            20.0,
        )
        self.assertAlmostEqual(corrected[0].offset_x_mm, 0.6)
        self.assertAlmostEqual(corrected[0].offset_y_mm, -0.6)
        with self.assertRaises(ValueError):
            remove_pair_baseline([], -1.0)

    def test_control_bias_is_averaged_and_removed(self):
        corrected, bias = remove_control_bias(
            (
                RotationCenterMeasurement(0.0, 0.10, -0.20),
                RotationCenterMeasurement(0.0, 0.30, 0.00),
                RotationCenterMeasurement(90.0, 0.70, -0.40),
            )
        )
        self.assertAlmostEqual(bias[0], 0.20)
        self.assertAlmostEqual(bias[1], -0.10)
        self.assertEqual(len(corrected), 1)
        self.assertAlmostEqual(corrected[0].offset_x_mm, 0.50)
        self.assertAlmostEqual(corrected[0].offset_y_mm, -0.30)

    def test_measurement_csv_ignores_blank_rows(self):
        measurements = parse_measurements_csv(
            "station,angle_deg,gap_x_mm,gap_y_mm\n"
            "0-1,0,,\n"
            "90-1,90,20.6,19.4\n"
        )
        self.assertEqual(measurements, (RotationCenterMeasurement(90, 20.6, 19.4),))
        with self.assertRaises(ValueError):
            parse_measurements_csv(
                "station,angle_deg,gap_x_mm,gap_y_mm\n90-1,90,20.6,\n"
            )


class RotationCenterProgramTests(unittest.TestCase):
    def test_program_contains_balanced_spaced_stations(self):
        program, stations = build_rotation_center_test_program(converter.Settings())
        self.assertEqual(
            [name for name, _, _, _ in stations],
            [
                "0-1", "0-2", "0-3",
                "90-1", "90-2", "90-3",
                "180-1", "180-2", "180-3",
                "270-1", "270-2", "270-3",
            ],
        )
        self.assertIn("(0-1 station:", program)
        self.assertIn("(90-2 station:", program)
        self.assertIn("(180-3 station:", program)
        self.assertIn("(270-1 station:", program)
        self.assertIn("LONGER cross is A=0", program)
        self.assertIn("SHORTER cross is the replay", program)
        self.assertIn("(label 0-1 at", program)
        self.assertIn("(label 90-2 at", program)
        self.assertIn("(label +X at", program)
        self.assertIn("small L bracket marks the A=0 reference", program)
        self.assertIn("centre direction key", program)
        self.assertEqual(program.count("("), program.count(")"))

    def test_default_pairs_keep_wet_lines_apart(self):
        program, _stations = build_rotation_center_test_program(
            converter.Settings()
        )
        self.assertIn("SHORTER cross is the replay, +20,+20 mm", program)
        self.assertIn("fitter subtracts the 20 mm nominal gap", program)
        self.assertIn("reference arm 18 mm", program)

    def test_default_layout_fits_14_inch_round_sheet(self):
        program, stations = build_rotation_center_test_program(converter.Settings())
        self.assertEqual(len(stations), 12)
        self.assertAlmostEqual(stations[0][2], -90.0, places=8)
        self.assertAlmostEqual(stations[0][3], -70.0, places=8)
        self.assertIn("330.2 mm test on 355.6 mm round stock", program)
        self.assertIn("largest ink radius", program)

    def test_three_replicates_keep_each_angle_balanced(self):
        _program, stations = build_rotation_center_test_program(converter.Settings())
        counts = {}
        for _name, angle, _x, _y in stations:
            counts[angle] = counts.get(angle, 0) + 1
        self.assertEqual(set(counts), {0.0, 90.0, 180.0, 270.0})
        self.assertEqual(set(counts.values()), {3})

    def test_measurement_template_matches_generated_stations(self):
        _program, stations = build_rotation_center_test_program(converter.Settings())
        template = measurement_template_csv(stations)
        rows = template.strip().splitlines()
        self.assertEqual(rows[0], "station,angle_deg,gap_x_mm,gap_y_mm")
        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[1], "0-1,0,,")
        self.assertEqual(rows[-1], "270-3,270,,")

    def test_oversized_station_layout_is_rejected(self):
        with self.assertRaises(ValueError):
            build_rotation_center_test_program(
                converter.Settings(),
                station_offset_mm=160.0,
                sheet_diameter_mm=355.6,
                test_diameter_mm=330.2,
            )

    def test_invalid_short_arm_is_rejected(self):
        with self.assertRaises(ValueError):
            build_rotation_center_test_program(
                converter.Settings(), arm_mm=8.0
            )

    def test_every_replay_uses_its_indexed_bed_angle(self):
        settings = converter.Settings()
        program, _stations = build_rotation_center_test_program(settings)
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
