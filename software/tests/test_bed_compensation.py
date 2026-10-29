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
    CALIBRATION_LAYOUTS,
    COVERAGE_RADIUS_MM,
    DENSE_LAYOUT,
    DENSE_LAYOUT_V1,
    DENSE_LAYOUT_V2,
    PASS_SPECS,
    STANDARD_LAYOUT,
    TEST_RADIUS_MM,
    analyze_measurements,
    calibration_stations,
    compare_measurements,
    expected_marks,
    fiducial_mark_points,
    fiducial_points,
    machine_frame_correction,
    mark_geometry,
    station_label_points,
    station_label_position,
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


def measured_csv_for_synthetic_field(layout=STANDARD_LAYOUT):
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        (
            "layout_id",
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

    for mark in expected_marks(layout):
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
                layout.layout_id,
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

    def test_dense_layout_doubles_spatial_resolution_with_smaller_marks(self):
        stations = calibration_stations(DENSE_LAYOUT)
        self.assertEqual(len(stations), 91)
        self.assertEqual(
            {station.ring_radius_mm for station in stations},
            {0.0, 30.0, 60.0, 90.0, 120.0, 148.5},
        )
        minimum_spacing = min(
            math.hypot(
                first.x_mm - second.x_mm,
                first.y_mm - second.y_mm,
            )
            for index, first in enumerate(stations)
            for second in stations[index + 1 :]
        )
        self.assertGreater(minimum_spacing, 28.0)
        self.assertLess(DENSE_LAYOUT.mark_arm_mm, STANDARD_LAYOUT.mark_arm_mm)
        self.assertLess(
            DENSE_LAYOUT.lane_offset_mm,
            STANDARD_LAYOUT.lane_offset_mm,
        )
        self.assertLessEqual(
            self.module.layout_extent_mm(DENSE_LAYOUT),
            DENSE_LAYOUT.test_radius_mm,
        )
        self.assertAlmostEqual(
            self.module.layout_extent_mm(DENSE_LAYOUT),
            164.0,
            places=6,
        )

    def test_dense_layout_versions_preserve_issued_geometry(self):
        self.assertEqual(DENSE_LAYOUT_V1.layout_id, "dense-91")
        self.assertEqual(DENSE_LAYOUT_V1.lane_offset_mm, 7.0)
        self.assertEqual(DENSE_LAYOUT_V2.layout_id, "dense-91-v2")
        self.assertEqual(DENSE_LAYOUT_V2.lane_offset_mm, 5.0)
        self.assertEqual(DENSE_LAYOUT.layout_id, "dense-91-v3")
        self.assertEqual(DENSE_LAYOUT.lane_offset_mm, 6.0)
        self.assertEqual(
            set(CALIBRATION_LAYOUTS),
            {"standard-37", "dense-91", "dense-91-v2", "dense-91-v3"},
        )

    def test_dense_labels_and_fiducials_clear_station_marks(self):
        def point_segment_distance(point, start, end):
            vx, vy = end[0] - start[0], end[1] - start[1]
            wx, wy = point[0] - start[0], point[1] - start[1]
            length_sq = vx * vx + vy * vy
            if length_sq <= 1e-15:
                return math.hypot(wx, wy)
            t = max(0.0, min(1.0, (wx * vx + wy * vy) / length_sq))
            return math.hypot(
                point[0] - start[0] - t * vx,
                point[1] - start[1] - t * vy,
            )

        def segment_distance(a0, a1, b0, b1):
            vx, vy = a1[0] - a0[0], a1[1] - a0[1]
            ux, uy = b1[0] - b0[0], b1[1] - b0[1]
            denominator = vx * uy - vy * ux
            if abs(denominator) > 1e-12:
                dx, dy = b0[0] - a0[0], b0[1] - a0[1]
                t = (dx * uy - dy * ux) / denominator
                u = (dx * vy - dy * vx) / denominator
                if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
                    return 0.0
            return min(
                point_segment_distance(a0, b0, b1),
                point_segment_distance(a1, b0, b1),
                point_segment_distance(b0, a0, a1),
                point_segment_distance(b1, a0, a1),
            )

        fiducials = []
        for _number, angle, x_mm, y_mm in fiducial_points(DENSE_LAYOUT):
            points = fiducial_mark_points(
                angle,
                x_mm,
                y_mm,
                radial_arm_mm=DENSE_LAYOUT.fiducial_radial_arm_mm,
                tangent_arm_mm=DENSE_LAYOUT.fiducial_tangent_arm_mm,
            )
            fiducials.extend(zip(points, points[1:]))
        minimum = float("inf")
        mark_edges = []
        for station in calibration_stations(DENSE_LAYOUT):
            for calibration_pass in DENSE_LAYOUT.pass_specs:
                _x, _y, points = mark_geometry(
                    station,
                    calibration_pass,
                    DENSE_LAYOUT,
                )
                for station_edge in zip(points, points[1:]):
                    mark_edges.append(station_edge)
                    for fiducial_edge in fiducials:
                        minimum = min(
                            minimum,
                            segment_distance(
                                *station_edge,
                                *fiducial_edge,
                            ),
                        )
        self.assertGreater(minimum, 5.5)

        center = calibration_stations(DENSE_LAYOUT)[0]
        pass_edges = []
        for calibration_pass in DENSE_LAYOUT.pass_specs:
            _x, _y, points = mark_geometry(
                center,
                calibration_pass,
                DENSE_LAYOUT,
            )
            pass_edges.append(
                (
                    calibration_pass.pass_name,
                    tuple(zip(points, points[1:])),
                )
            )
        mark_minimum = float("inf")
        for index, (_first_name, first_edges) in enumerate(pass_edges):
            for _second_name, second_edges in pass_edges[index + 1 :]:
                for first_edge in first_edges:
                    for second_edge in second_edges:
                        mark_minimum = min(
                            mark_minimum,
                            segment_distance(*first_edge, *second_edge),
                        )
        self.assertAlmostEqual(
            mark_minimum,
            1.2426406871,
            places=6,
        )

        label_minimum = float("inf")
        for station in calibration_stations(DENSE_LAYOUT):
            label_x, label_y = station_label_position(
                station,
                DENSE_LAYOUT,
            )
            label_points = station_label_points(
                station.station_id,
                label_x,
                label_y,
                height_mm=DENSE_LAYOUT.label_height_mm,
            )
            label_edges = [
                edge
                for line in label_points
                for edge in zip(line, line[1:])
            ]
            for label_edge in label_edges:
                for mark_edge in mark_edges:
                    label_minimum = min(
                        label_minimum,
                        segment_distance(*label_edge, *mark_edge),
                    )
        self.assertGreater(label_minimum, 2.5)

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

    def test_dense_program_has_91_stations_and_the_same_nine_passes(self):
        program, stations = self.module.build_program(
            converter.Settings(),
            layout=DENSE_LAYOUT,
        )
        self.assertEqual(len(stations), 91)
        self.assertEqual(program.count("M0 ("), 8)
        self.assertIn("91-station balanced dense field", program)
        self.assertIn("PASS 9/9 A000-CONTROL", program)
        self.assertEqual(program.count("G53 G1"), 1)

    def test_automatic_dense_program_uses_timed_pass_changes(self):
        program, stations = self.module.build_program(
            converter.Settings(),
            layout=DENSE_LAYOUT,
            pass_dwell_seconds=5.0,
        )
        self.assertEqual(len(stations), 91)
        self.assertEqual(program.count("M0 ("), 0)
        self.assertEqual(
            program.count(
                "G4 P5 (automatic pass dwell;"
            ),
            8,
        )
        self.assertIn(
            "automatic 5 s pass dwell; one initial Cycle Start",
            program,
        )
        self.assertEqual(program.count("G53 G1"), 1)

    def test_automatic_pass_dwell_must_be_finite_and_non_negative(self):
        for dwell in (-0.1, float("nan"), float("inf")):
            with self.subTest(dwell=dwell):
                with self.assertRaisesRegex(ValueError, "pass dwell"):
                    self.module.build_program(
                        converter.Settings(),
                        layout=DENSE_LAYOUT,
                        pass_dwell_seconds=dwell,
                    )

    def test_committed_dense_sample_matches_the_generator(self):
        program, _stations = self.module.build_program(
            converter.Settings(),
            layout=DENSE_LAYOUT,
        )
        sample = (
            ROOT / "samples" / "gcode" / "bed-error-map-dense-91-v3.gcode"
        )
        self.assertEqual(sample.read_text(encoding="utf-8"), program)
        csv_sample = (
            ROOT / "samples" / "gcode" / "bed-error-map-dense-91-v3.csv"
        )
        self.assertEqual(
            csv_sample.read_text(encoding="utf-8"),
            measurement_template_csv(layout=DENSE_LAYOUT),
        )

    def test_committed_automatic_dense_sample_matches_the_generator(self):
        program, _stations = self.module.build_program(
            converter.Settings(),
            layout=DENSE_LAYOUT,
            pass_dwell_seconds=5.0,
        )
        sample = (
            ROOT
            / "samples"
            / "gcode"
            / "bed-error-map-dense-91-v3-auto.gcode"
        )
        self.assertEqual(sample.read_text(encoding="utf-8"), program)
        csv_sample = (
            ROOT
            / "samples"
            / "gcode"
            / "bed-error-map-dense-91-v3-auto.csv"
        )
        self.assertEqual(
            csv_sample.read_text(encoding="utf-8"),
            measurement_template_csv(layout=DENSE_LAYOUT),
        )

    def test_committed_dense_verification_uses_the_same_numbering(self):
        verification = (
            ROOT
            / "samples"
            / "gcode"
            / "bed-error-verify-dense-91-v3.gcode"
        )
        csv_verification = verification.with_suffix(".csv")
        program = verification.read_text(encoding="utf-8")
        self.assertIn("91-station balanced dense field v3", program)
        self.assertIn("verification pass with bed compensation", program)
        self.assertEqual(program.count("M0 ("), 8)
        self.assertEqual(
            csv_verification.read_text(encoding="utf-8"),
            measurement_template_csv(layout=DENSE_LAYOUT),
        )

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

    def test_dense_template_has_layout_id_and_819_station_marks(self):
        rows = list(
            csv.DictReader(
                io.StringIO(measurement_template_csv(layout=DENSE_LAYOUT))
            )
        )
        self.assertEqual(len(rows), 4 + 91 * len(DENSE_LAYOUT.pass_specs))
        self.assertEqual(len(rows), 823)
        self.assertEqual({row["layout_id"] for row in rows}, {"dense-91-v3"})

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

    def test_dense_synthetic_field_builds_a_91_station_profile(self):
        profile, report, accepted = analyze_measurements(
            measured_csv_for_synthetic_field(DENSE_LAYOUT),
            source="synthetic-dense.csv",
            max_cross_validation_rms_mm=0.08,
            max_cross_validation_error_mm=0.20,
            minimum_improvement_pct=20.0,
        )
        self.assertTrue(accepted)
        self.assertEqual(report["layout"]["id"], "dense-91-v3")
        self.assertEqual(report["layout"]["station_count"], 91)
        self.assertEqual(len(profile.samples_mm[0]), 91)

    def test_measurement_layout_is_detected_and_mismatch_is_rejected(self):
        text = measured_csv_for_synthetic_field(DENSE_LAYOUT)
        self.assertEqual(
            len(parse_measurement_csv(text, require_complete=True)),
            4 + 91 * len(DENSE_LAYOUT.pass_specs),
        )
        with self.assertRaisesRegex(ValueError, "does not match"):
            parse_measurement_csv(
                text,
                require_complete=True,
                layout=STANDARD_LAYOUT,
            )

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
    def test_application_defaults_select_centered_dense_profile(self):
        text_defaults = {
            key: default
            for _group, items in converter.TEXT_FIELD_GROUPS
            for _label, key, default in items
        }
        profile_path = Path(text_defaults["bed_compensation_path"])

        self.assertTrue(profile_path.is_file())
        self.assertEqual(
            converter.load_bed_compensation(str(profile_path)).fingerprint,
            "18bfb4ed1c33",
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
        self.assertAlmostEqual(boundary_max, 0.891352, places=6)
        self.assertLessEqual(boundary_max, 5.0)
        gcode = converter.contours_to_gcode(
            [[(-5.0, 0.0), (5.0, 0.0)]], settings
        )
        self.assertIn("(bed compensation 18bfb4ed1c33,", gcode)
        self.assertIn("angular interpolation bed-frame", gcode)

    def test_13_5_inch_field_clips_before_extrapolated_coverage(self):
        settings = converter.Settings(
            theta_mode="fixed",
            theta_center_hold_diameter_mm=0,
            bed_margin_mm=6.35,
            bed_compensation_path=str(
                ROOT
                / "samples"
                / "gcode"
                / "bed-error-compensation-2026-10-26-13p5in-extrapolated.json"
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
            13.5 * 25.4 / 2.0 + 1e-6,
        )
        self.assertEqual(plan["bed_compensation"].fingerprint, "4bad792e35ad")

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
