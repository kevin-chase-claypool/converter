"""Bed calibration generation, analysis, and planner compensation."""

import csv
import importlib.util
import io
import math
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter
import converter_core.bed_compensation as bed_compensation_module
import converter_core.gcode as gcode_module
from converter_core.bed_calibration import (
    COVERAGE_RADIUS_MM,
    PASS_SPECS,
    TEST_RADIUS_MM,
    analyze_measurements,
    calibration_stations,
    compare_measurements,
    expected_marks,
    machine_frame_correction,
    measurement_template_csv,
    parse_measurement_csv,
)
from converter_core.bed_compensation import (
    BedCompensationProfile,
    compensated_machine_point,
    compensation_step_count,
)


def profile_for_test():
    samples = ((-10.0, -10.0), (10.0, -10.0), (10.0, 10.0), (-10.0, 10.0))
    return BedCompensationProfile(
        angle_values_deg=(0.0, 90.0, 180.0, 270.0),
        samples_mm=(samples,) * 4,
        corrections_mm=(
            ((1.0, 0.0), (1.0, 0.0), (1.0, 0.0), (1.0, 0.0)),
            ((1.0, 1.0), (1.0, 1.0), (1.0, 1.0), (1.0, 1.0)),
            ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0), (0.0, 1.0)),
            ((-1.0, 0.0), (-1.0, 0.0), (-1.0, 0.0), (-1.0, 0.0)),
        ),
        coverage_radius_mm=20.0,
        source="unit test",
    )


def measured_csv_for_synthetic_field():
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "section",
            "station_id",
            "ring_radius_mm",
            "station_angle_deg",
            "pass_id",
            "pass_name",
            "mark_kind",
            "angle_deg",
            "base_x_mm",
            "base_y_mm",
            "nominal_x_mm",
            "nominal_y_mm",
            "measured_x_mm",
            "measured_y_mm",
        )
    )

    def spatial(x_mm, y_mm):
        return (
            0.004 * x_mm + 0.006 * y_mm,
            -0.005 * x_mm - 0.007 * y_mm,
        )

    def angular(angle_deg, x_mm, y_mm):
        return (
            0.10 * math.cos(math.radians(angle_deg)) + 0.002 * x_mm,
            0.08 * math.sin(math.radians(angle_deg)) - 0.0015 * y_mm,
        )

    for mark in expected_marks():
        if mark.section == "fiducial":
            error = (0.0, 0.0)
        elif mark.mark_kind == "reference":
            error = spatial(mark.nominal_x_mm, mark.nominal_y_mm)
        elif mark.mark_kind == "control":
            target_error = spatial(mark.nominal_x_mm, mark.nominal_y_mm)
            error = (target_error[0] + 0.015, target_error[1] - 0.010)
        else:
            target_error = spatial(mark.nominal_x_mm, mark.nominal_y_mm)
            angle_error = angular(
                mark.angle_deg, mark.nominal_x_mm, mark.nominal_y_mm
            )
            error = (
                target_error[0] + angle_error[0],
                target_error[1] + angle_error[1],
            )
        writer.writerow(
            (
                mark.section,
                mark.station_id,
                mark.ring_radius_mm,
                mark.station_angle_deg,
                mark.pass_id,
                mark.pass_name,
                mark.mark_kind,
                mark.angle_deg,
                mark.base_x_mm,
                mark.base_y_mm,
                mark.nominal_x_mm,
                mark.nominal_y_mm,
                mark.nominal_x_mm + error[0],
                mark.nominal_y_mm + error[1],
            )
        )
    return output.getvalue()


def transform_measured_csv(text, *, scale, rotation_deg, dx, dy):
    reader = csv.DictReader(io.StringIO(text))
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    angle = math.radians(rotation_deg)
    cosine, sine = math.cos(angle) * scale, math.sin(angle) * scale
    for row in reader:
        measured_x = float(row["measured_x_mm"])
        measured_y = float(row["measured_y_mm"])
        row["measured_x_mm"] = cosine * measured_x - sine * measured_y + dx
        row["measured_y_mm"] = sine * measured_x + cosine * measured_y + dy
        writer.writerow(row)
    return output.getvalue()


def nominal_measurement_csv(text):
    reader = csv.DictReader(io.StringIO(text))
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in reader:
        row["measured_x_mm"] = row["nominal_x_mm"]
        row["measured_y_mm"] = row["nominal_y_mm"]
        writer.writerow(row)
    return output.getvalue()


class BedCompensationProfileTests(unittest.TestCase):
    def test_angle_interpolation_and_wrap(self):
        profile = profile_for_test()
        between = profile.correction(45.0, 0.0, 0.0)
        self.assertAlmostEqual(between[0], 1.0606601717798212)
        self.assertAlmostEqual(between[1], 0.35355339059327373)
        wrapped = profile.correction(315.0, 0.0, 0.0)
        self.assertAlmostEqual(wrapped[0], 0.0)
        self.assertAlmostEqual(wrapped[1], -0.7071067811865476)

    def test_angle_interpolation_rotates_a_constant_bed_error(self):
        samples = ((-10.0, 0.0), (0.0, 10.0), (10.0, 0.0))
        corrections = []
        for angle in (0.0, 90.0, 180.0, 270.0):
            corrections.append(
                machine_frame_correction(angle, (1.0, 0.0))
            )
        profile = BedCompensationProfile(
            angle_values_deg=(0.0, 90.0, 180.0, 270.0),
            samples_mm=(samples,) * 4,
            corrections_mm=tuple((correction,) * 3 for correction in corrections),
            coverage_radius_mm=20.0,
        )
        correction = profile.correction(45.0, 0.0, 0.0)
        self.assertAlmostEqual(correction[0], -math.sqrt(0.5))
        self.assertAlmostEqual(correction[1], -math.sqrt(0.5))
        machine = compensated_machine_point(
            (1.0, 0.0),
            45.0,
            (0.0, 0.0),
            profile,
        )
        self.assertAlmostEqual(machine[0], 0.0)
        self.assertAlmostEqual(machine[1], 0.0)

    def test_spatial_interpolation(self):
        profile = BedCompensationProfile(
            angle_values_deg=(0.0,),
            samples_mm=(((-10.0, -10.0), (10.0, -10.0), (10.0, 10.0)),),
            corrections_mm=(((0.0, 0.0), (2.0, 0.0), (2.0, 2.0)),),
            coverage_radius_mm=20.0,
        )
        self.assertEqual(profile.correction(0.0, 10.0, -10.0), (2.0, 0.0))
        interpolated = profile.correction(0.0, 0.0, 0.0)
        self.assertGreater(interpolated[0], 0.0)
        self.assertLess(interpolated[0], 2.0)

    def test_json_round_trip(self):
        profile = profile_for_test()
        restored = BedCompensationProfile.from_json(profile.to_json())
        self.assertEqual(restored, profile)
        self.assertEqual(restored.fingerprint, profile.fingerprint)

    def test_excessive_correction_is_rejected(self):
        with self.assertRaises(ValueError):
            BedCompensationProfile(
                angle_values_deg=(0.0,),
                samples_mm=(((-10.0, 0.0), (0.0, 10.0), (10.0, 0.0)),),
                corrections_mm=(((6.0, 0.0), (0.0, 0.0), (0.0, 0.0)),),
                coverage_radius_mm=20.0,
            )

    def test_coverage_is_enforced(self):
        with self.assertRaises(ValueError):
            profile_for_test().correction(0.0, 21.0, 0.0)

    def test_compensated_point_rotates_then_adds_profile(self):
        point = compensated_machine_point(
            (10.0, 0.0), 90.0, (0.0, 0.0), profile_for_test()
        )
        self.assertAlmostEqual(point[0], 1.0)
        self.assertAlmostEqual(point[1], 11.0)

    def test_varying_profile_adds_subdivision(self):
        steps = compensation_step_count(
            (-10.0, 0.0),
            (10.0, 0.0),
            0.0,
            90.0,
            (0.0, 0.0),
            profile_for_test(),
            0.01,
        )
        self.assertGreater(steps, 1)

    def test_adaptive_probe_fast_exits_on_a_flat_correction(self):
        samples = ((-10.0, -10.0), (10.0, -10.0), (10.0, 10.0), (-10.0, 10.0))
        profile = BedCompensationProfile(
            angle_values_deg=(0.0,),
            samples_mm=(samples,),
            corrections_mm=(((0.25, -0.10),) * len(samples),),
            coverage_radius_mm=20.0,
        )
        with mock.patch.object(
            bed_compensation_module,
            "compensated_machine_point",
            wraps=bed_compensation_module.compensated_machine_point,
        ) as probe:
            steps = compensation_step_count(
                (-5.0, 0.0),
                (5.0, 0.0),
                0.0,
                0.0,
                (0.0, 0.0),
                profile,
                0.10,
            )
        self.assertEqual(steps, 1)
        self.assertLessEqual(probe.call_count, 5)

    def test_adaptive_probe_falls_back_to_full_curvature_check(self):
        arguments = (
            (-10.0, 0.0),
            (10.0, 0.0),
            0.0,
            90.0,
            (0.0, 0.0),
            profile_for_test(),
            0.01,
        )
        adaptive = compensation_step_count(*arguments)
        fixed = compensation_step_count(*arguments, adaptive=False)
        self.assertGreater(adaptive, 1)
        self.assertEqual(adaptive, fixed)

    def test_adaptive_probe_matches_full_probe_for_varying_fields(self):
        rng = random.Random(20261023)
        profile = profile_for_test()
        for _index in range(200):
            start = (rng.uniform(-9.0, 9.0), rng.uniform(-9.0, 9.0))
            end = (rng.uniform(-9.0, 9.0), rng.uniform(-9.0, 9.0))
            start_theta = rng.uniform(0.0, 360.0)
            end_theta = rng.uniform(0.0, 360.0)
            arguments = (
                start,
                end,
                start_theta,
                end_theta,
                (0.0, 0.0),
                profile,
                0.01,
            )
            self.assertEqual(
                compensation_step_count(*arguments),
                compensation_step_count(*arguments, adaptive=False),
            )


class BedCalibrationGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "tools" / "make_bed_error_calibration.py"
        spec = importlib.util.spec_from_file_location(
            "make_bed_error_calibration", path
        )
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_layout_covers_round_sheet_and_stays_inside_13_inches(self):
        stations = calibration_stations()
        self.assertEqual(len(stations), 37)
        self.assertEqual(
            {station.ring_radius_mm for station in stations},
            {0.0, 50.0, 95.0, 150.0},
        )
        self.assertLessEqual(self.module.layout_extent_mm(), TEST_RADIUS_MM)
        self.assertGreater(self.module.layout_extent_mm(), 160.0)

    def test_one_pen_nine_pass_program_and_eight_pauses(self):
        program, stations = self.module.build_program(converter.Settings())
        self.assertEqual(len(stations), 37)
        self.assertEqual(program.count("M0 ("), 8)
        for marker in (
            "PASS 1/9 A000-REFERENCE",
            "PASS 2/9 A045",
            "PASS 3/9 A090",
            "PASS 4/9 A135",
            "PASS 5/9 A180",
            "PASS 6/9 A225",
            "PASS 7/9 A270",
            "PASS 8/9 A315",
            "PASS 9/9 A000-CONTROL",
        ):
            self.assertIn(marker, program)
        self.assertIn("one 0.20 mm pen for all 9 passes", program)
        self.assertNotIn("install blue", program.lower())
        self.assertEqual(program.count("G53 G1"), 1)

    def test_verification_mode_uses_the_loaded_profile(self):
        samples = tuple(
            (station.x_mm, station.y_mm) for station in calibration_stations()
        )
        profile = BedCompensationProfile(
            angle_values_deg=(0.0,),
            samples_mm=(samples,),
            corrections_mm=(((0.5, 0.25),) * len(samples),),
            coverage_radius_mm=TEST_RADIUS_MM,
            source="verification test",
        )
        raw, _stations = self.module.build_program(converter.Settings())
        compensated, _stations = self.module.build_program(
            converter.Settings(), compensation=profile
        )
        self.assertIn(
            "verification pass with bed compensation %s" % profile.fingerprint,
            compensated,
        )
        self.assertNotEqual(raw, compensated)

    def test_measurement_template_has_every_mark_and_blank_measurements(self):
        rows = list(csv.DictReader(io.StringIO(measurement_template_csv())))
        self.assertEqual(len(rows), 4 + 37 * len(PASS_SPECS))
        self.assertTrue(all(not row["measured_x_mm"] for row in rows))
        self.assertTrue(all(not row["measured_y_mm"] for row in rows))

    def test_incomplete_measurements_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            parse_measurement_csv(
                measurement_template_csv(), require_complete=True
            )


class BedCalibrationAnalysisTests(unittest.TestCase):
    def test_synthetic_field_builds_an_accepted_profile(self):
        profile, report, accepted = analyze_measurements(
            measured_csv_for_synthetic_field(),
            source="synthetic.csv",
            max_cross_validation_rms_mm=0.08,
            max_cross_validation_error_mm=0.20,
            minimum_improvement_pct=20.0,
        )
        self.assertTrue(accepted)
        self.assertEqual(
            profile.angle_values_deg,
            (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0),
        )
        self.assertEqual(
            report["layout"]["angle_values_deg"],
            list(profile.angle_values_deg),
        )
        self.assertIn("45", report["angles"])
        self.assertIn("315", report["angles"])
        self.assertEqual(profile.coverage_radius_mm, COVERAGE_RADIUS_MM)
        self.assertLess(report["a0_control_residual"]["max_mm"], 0.03)
        self.assertLess(report["leave_one_out"]["rms_mm"], 0.08)
        self.assertGreater(report["leave_one_out"]["improvement_pct"], 50.0)

    def test_profile_can_declare_extrapolated_coverage(self):
        profile, report, accepted = analyze_measurements(
            measured_csv_for_synthetic_field(),
            source="synthetic.csv",
            max_cross_validation_rms_mm=0.08,
            max_cross_validation_error_mm=0.20,
            minimum_improvement_pct=20.0,
            coverage_radius_mm=converter.DEFAULT_BED_COMPENSATION_RADIUS_MM,
        )
        self.assertTrue(accepted)
        self.assertEqual(
            profile.coverage_radius_mm,
            converter.DEFAULT_BED_COMPENSATION_RADIUS_MM,
        )
        self.assertEqual(
            report["layout"]["coverage_radius_mm"],
            converter.DEFAULT_BED_COMPENSATION_RADIUS_MM,
        )
        boundary = profile.correction(
            0.0, converter.DEFAULT_BED_COMPENSATION_RADIUS_MM, 0.0
        )
        self.assertLessEqual(math.hypot(*boundary), 5.0)

    def test_coverage_cannot_extend_beyond_the_calibration_stock(self):
        with self.assertRaisesRegex(ValueError, "calibration stock radius"):
            analyze_measurements(
                measured_csv_for_synthetic_field(),
                coverage_radius_mm=180.0,
            )

    def test_bed_mesh_correlation_is_reported(self):
        mesh = io.StringIO()
        writer = csv.writer(mesh, lineterminator="\n")
        mesh.write("# toolhead contact-seek bed mesh\n")
        writer.writerow(("type", "x", "y", "gap_mm"))
        for station in calibration_stations():
            writer.writerow(
                (
                    "grid",
                    station.x_mm,
                    station.y_mm,
                    0.004 * station.x_mm - 0.003 * station.y_mm,
                )
            )
        _profile, report, _accepted = analyze_measurements(
            measured_csv_for_synthetic_field(),
            bed_mesh_csv=mesh.getvalue(),
            source="synthetic.csv",
            max_cross_validation_rms_mm=0.08,
            max_cross_validation_error_mm=0.20,
            minimum_improvement_pct=20.0,
        )
        self.assertEqual(
            report["bed_mesh_correlation"]["sample_count"],
            len(calibration_stations()),
        )
        self.assertIn("summary", report["bed_mesh_correlation"])
        self.assertEqual(len(report["bed_mesh_correlation"]["sha256"]), 64)

    def test_fiducials_remove_common_sheet_pose_before_fitting(self):
        transformed = transform_measured_csv(
            measured_csv_for_synthetic_field(),
            scale=1.018,
            rotation_deg=2.5,
            dx=12.0,
            dy=-7.0,
        )
        _profile, report, accepted = analyze_measurements(
            transformed,
            source="transformed.csv",
            max_cross_validation_rms_mm=0.08,
            max_cross_validation_error_mm=0.20,
            minimum_improvement_pct=20.0,
        )
        self.assertTrue(accepted)
        self.assertAlmostEqual(report["alignment"]["scale"], 1.018, places=12)
        self.assertAlmostEqual(report["alignment"]["rotation_deg"], 2.5, places=12)

    def test_bed_correction_is_rotated_into_machine_frame(self):
        correction = machine_frame_correction(90.0, (1.0, 0.0))
        self.assertAlmostEqual(correction[0], 0.0)
        self.assertAlmostEqual(correction[1], -1.0)

    def test_verification_comparison_rewards_a_clean_second_sheet(self):
        baseline = measured_csv_for_synthetic_field()
        comparison = compare_measurements(
            baseline,
            nominal_measurement_csv(baseline),
            baseline_source="before.csv",
            verification_source="after.csv",
            max_rms_mm=0.35,
            max_error_mm=0.90,
            minimum_improvement_pct=30.0,
        )
        self.assertTrue(comparison["acceptance"]["accepted"])
        self.assertEqual(comparison["after"]["rms_mm"], 0.0)
        self.assertEqual(comparison["rms_improvement_pct"], 100.0)


class BedCompensationPlannerIntegrationTests(unittest.TestCase):
    def test_application_defaults_select_the_extrapolated_profile(self):
        text_defaults = {
            key: default
            for _group, items in converter.TEXT_FIELD_GROUPS
            for _label, key, default in items
        }
        profile_path = Path(text_defaults["bed_compensation_path"])

        self.assertTrue(profile_path.is_file())
        self.assertEqual(
            converter.load_bed_compensation(str(profile_path)).fingerprint,
            "4c8270de8a74",
        )
        self.assertEqual(
            converter.default_settings().bed_compensation_path,
            str(profile_path),
        )

        settings = converter.settings_from_values(text_defaults, {})
        self.assertFalse(settings.exact_compensated_preview)
        profile = converter.load_bed_compensation(
            settings.bed_compensation_path
        )
        self.assertAlmostEqual(
            profile.coverage_radius_mm,
            converter.DEFAULT_BED_COMPENSATION_RADIUS_MM,
            places=6,
        )
        self.assertAlmostEqual(
            settings.bed_diameter_mm / 2.0 - settings.bed_margin_mm,
            profile.coverage_radius_mm,
            places=6,
        )
        boundary_max = max(
            math.hypot(
                *profile.correction(
                    angle,
                    profile.coverage_radius_mm
                    * math.cos(math.radians(angle)),
                    profile.coverage_radius_mm
                    * math.sin(math.radians(angle)),
                )
            )
            for angle in range(360)
        )
        self.assertAlmostEqual(boundary_max, 1.053640, places=6)
        self.assertLessEqual(boundary_max, 5.0)
        gcode = converter.contours_to_gcode(
            [[(-5.0, 0.0), (5.0, 0.0)]], settings
        )
        self.assertIn("(bed compensation 4c8270de8a74,", gcode)
        self.assertIn("angular interpolation bed-frame", gcode)

    def test_13_5_inch_field_clips_before_extrapolated_coverage(self):
        settings = converter.Settings(
            theta_mode="fixed",
            theta_center_hold_diameter_mm=0,
            bed_compensation_path=str(
                ROOT
                / "samples"
                / "gcode"
                / "bed-error-compensation-2026-10-23-13p5in-extrapolated.json"
            ),
            machine_reach_radius_mm=180.0,
            frame_center_mm=(0.0, 0.0),
        )
        plan = converter.plan_program(
            [[(160.0, 0.0), (180.0, 0.0)]], settings
        )
        radii = [
            (x * x + y * y) ** 0.5
            for contour in plan["contours"]
            for x, y in contour
        ]
        self.assertTrue(radii)
        self.assertGreater(max(radii), 170.0)
        self.assertLessEqual(
            max(radii),
            converter.DEFAULT_BED_COMPENSATION_RADIUS_MM + 1e-6,
        )
        self.assertEqual(plan["bed_compensation"].fingerprint, "4c8270de8a74")

    def test_fast_preview_uses_nominal_moves_without_compensation_probes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bed.json"
            path.write_text(profile_for_test().to_json(), encoding="utf-8")
            settings = converter.Settings(
                theta_mode="fixed",
                theta_center_hold_diameter_mm=0,
                bed_compensation_path=str(path),
            )
            contours = [[(-5.0, 0.0), (5.0, 0.0)]]
            plan = converter.plan_program(contours, settings)
            with mock.patch.object(
                gcode_module,
                "compensation_step_count",
                wraps=gcode_module.compensation_step_count,
            ) as probe:
                fast_moves = converter.build_preview_moves(
                    contours,
                    settings,
                    program_plan=plan,
                    apply_compensation=False,
                )
            probe.assert_not_called()
            gcode = converter.contours_to_gcode(
                contours, settings, program_plan=plan
            )

        exact_moves = converter.build_preview_moves(
            contours,
            settings,
            program_plan=plan,
        )
        self.assertIn("(bed compensation ", gcode)
        self.assertNotEqual(
            [move.get("gcode") for move in fast_moves],
            [move.get("gcode") for move in exact_moves],
        )

    def test_explicit_empty_profile_disables_compensation(self):
        settings = converter.Settings(
            theta_mode="fixed",
            theta_center_hold_diameter_mm=0,
            bed_compensation_path="",
        )
        gcode = converter.contours_to_gcode(
            [[(-5.0, 0.0), (5.0, 0.0)]], settings
        )
        self.assertNotIn("bed compensation", gcode)

    def test_gcode_and_preview_use_the_same_compensated_machine_points(self):
        settings = converter.Settings(
            theta_mode="fixed", theta_center_hold_diameter_mm=0
        )
        base_gcode = converter.contours_to_gcode(
            [[(-5.0, 0.0), (5.0, 0.0)]], settings
        )
        self.assertNotIn("bed compensation", base_gcode)

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bed.json"
            path.write_text(profile_for_test().to_json(), encoding="utf-8")
            compensated_settings = converter.Settings(
                theta_mode="fixed",
                theta_center_hold_diameter_mm=0,
                bed_compensation_path=str(path),
            )
            contours = [[(-5.0, 0.0), (5.0, 0.0)]]
            program_plan = converter.plan_program(
                contours, compensated_settings
            )
            gcode = converter.contours_to_gcode(
                contours, compensated_settings, program_plan
            )
            moves = converter.build_preview_moves(
                contours, compensated_settings, program_plan=program_plan
            )
        self.assertIn("(bed compensation ", gcode)
        gcode_moves = [
            line for line in gcode.splitlines() if line.startswith("G1 X")
        ]
        preview_moves = [
            move["gcode"]
            for move in moves
            if str(move.get("gcode", "")).startswith("G1 X")
        ]
        self.assertEqual(gcode_moves, preview_moves)

    def test_profile_beyond_its_coverage_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bed.json"
            path.write_text(profile_for_test().to_json(), encoding="utf-8")
            settings = converter.Settings(
                theta_mode="fixed",
                bed_compensation_path=str(path),
                artwork_offset_y_mm=60.0,
            )
            with self.assertRaisesRegex(ValueError, "compensation coverage"):
                converter.plan_program(
                    [[(0.0, 40.0), (0.0, 41.0)]], settings
                )


if __name__ == "__main__":
    unittest.main()
