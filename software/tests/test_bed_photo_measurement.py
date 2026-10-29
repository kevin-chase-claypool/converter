"""Photo-measurement helpers for the full-field bed calibration."""

import csv
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

from converter_core.bed_calibration import (
    DENSE_LAYOUT,
    PASS_SPECS,
    STANDARD_LAYOUT,
    calibration_stations,
    expected_marks,
    fiducial_mark_points,
    fiducial_points,
)


class BedPhotoMeasurementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "tools" / "measure_bed_error_photo.py"
        spec = importlib.util.spec_from_file_location(
            "measure_bed_error_photo", path
        )
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    def test_homography_round_trip(self):
        nominal = np.asarray(
            [(10.0, 10.0), (-10.0, 10.0), (-10.0, -10.0), (10.0, -10.0)]
        )
        image = np.asarray(
            [(510.0, 490.0), (490.0, 510.0), (510.0, 510.0), (530.0, 490.0)]
        )
        transform = self.module._fit_homography(nominal, image)
        inverse = np.linalg.inv(transform)
        for bed_point, image_point in zip(nominal, image):
            mapped = self.module._forward(transform, bed_point)
            restored = self.module._inverse(inverse, mapped)
            self.assertTrue(np.allclose(mapped, image_point))
            self.assertTrue(np.allclose(restored, bed_point))

    def test_dense_station_component_bounds_follow_the_marker_scale(self):
        self.assertEqual(
            self.module._default_station_dimensions(STANDARD_LAYOUT),
            (16, 30),
        )
        self.assertEqual(
            self.module._default_station_dimensions(DENSE_LAYOUT),
            (14, 60),
        )
        self.assertEqual(
            self.module._default_station_point_bounds(STANDARD_LAYOUT),
            (60, 200),
        )
        self.assertEqual(
            self.module._default_station_point_bounds(DENSE_LAYOUT),
            (40, 500),
        )

    def test_fiducial_corner_uses_the_shared_vertex(self):
        points = tuple(
            [(x_value, 20) for x_value in range(10, 21)]
            + [(20, y_value) for y_value in range(10, 20)]
        )
        component = self.module.Component(points, (10, 10, 20, 20))
        corner = self.module._component_corner(
            component,
            prediction=(20, 20),
        )
        self.assertTrue(np.allclose(corner, (20, 20)))

    def test_fiducial_corner_prefers_the_arm_junction_over_nearest_tip(self):
        points = tuple(
            [(x_value, 20) for x_value in range(10, 21)]
            + [(20, y_value) for y_value in range(10, 20)]
        )
        component = self.module.Component(points, (10, 10, 20, 20))
        corner = self.module._component_corner(
            component,
            prediction=(20, 11),
        )
        self.assertTrue(np.allclose(corner, (20, 20)))

    def test_fiducial_filter_rejects_paper_edges_and_station_marks(self):
        def component(point_count, bbox):
            return self.module.Component(
                tuple((bbox[0], bbox[1]) for _ in range(point_count)),
                bbox,
            )

        fiducial = component(250, (0, 0, 65, 65))
        paper_edge = component(5000, (0, 0, 400, 400))
        station_mark = component(200, (0, 0, 25, 25))
        filtered = self.module._fiducial_sized_components(
            (paper_edge, station_mark, fiducial)
        )
        self.assertEqual(filtered, (fiducial,))

    def test_fiducial_filter_accepts_smaller_overhead_capture(self):
        points = ((100, 200),) * 103
        fiducial = self.module.Component(
            points,
            (100, 200, 126, 236),
        )
        self.assertEqual(
            self.module._fiducial_sized_components((fiducial,)),
            (fiducial,),
        )

    def test_fiducial_shape_score_prefers_the_long_radial_arm(self):
        expected = np.asarray((19.6, 34.3, 39.5))
        fiducial = self.module.Component(
            ((100, 100), (120, 100), (100, 135)),
            (100, 100, 120, 135),
        )
        station_mark = self.module.Component(
            ((100, 100), (122, 100), (100, 123)),
            (100, 100, 122, 123),
        )
        self.assertLess(
            self.module._fiducial_shape_error(fiducial, expected, 4.9),
            self.module._fiducial_shape_error(station_mark, expected, 4.9),
        )

    def test_station_dimension_floor_can_exclude_large_labels(self):
        def component(maximum_dimension):
            return self.module.Component(
                ((0, 0), (1, 1)),
                (0, 0, maximum_dimension - 1, maximum_dimension - 1),
            )

        label = component(16)
        station = component(17)
        self.assertEqual(
            self.module._station_sized_components(
                (label, station),
                minimum_dimension=17,
            ),
            (station,),
        )

    def test_fiducial_selection_uses_largest_component_per_quadrant(self):
        def component(point, point_count):
            return self.module.Component(
                tuple(point for _ in range(point_count)),
                (point[0], point[1], point[0] + 60, point[1] + 60),
            )

        center = (500.0, 500.0)
        small_candidates = (
            component((600, 400), 120),
            component((400, 400), 130),
            component((600, 600), 140),
            component((400, 600), 150),
        )
        selected = (
            component((600, 400), 220),
            component((400, 400), 230),
            component((400, 600), 240),
            component((600, 600), 250),
        )
        self.assertEqual(
            self.module._quadrant_fiducials(
                small_candidates + selected,
                center,
            ),
            selected,
        )

    def test_seed_homography_scales_to_new_photo_size(self):
        diagnostic = {
            "homography": [
                [4.0, 0.0, 100.0],
                [0.0, 4.0, 80.0],
                [0.0, 0.0, 1.0],
            ],
            "image_size_px": [100, 100],
        }
        transform = self.module._scaled_seed_homography(
            diagnostic, (200, 100)
        )
        mapped = self.module._forward(transform, (10.0, 10.0))
        self.assertTrue(np.allclose(mapped, (280.0, 120.0)))

    def test_station_vertex_uses_shared_corner_centrelines(self):
        sheet_points = tuple(
            [(x_value, 0) for x_value in range(-5, 1)]
            + [(0, y_value) for y_value in range(1, 6)]
        )
        homography = np.asarray(
            [[4.0, 0.0, 100.0], [0.0, -4.0, 100.0], [0.0, 0.0, 1.0]]
        )
        image_points = tuple(
            (
                int(round(4.0 * x_value + 100.0)),
                int(round(-4.0 * y_value + 100.0)),
            )
            for x_value, y_value in sheet_points
        )
        xs = [point[0] for point in image_points]
        ys = [point[1] for point in image_points]
        component = self.module.Component(
            image_points,
            (min(xs), min(ys), max(xs), max(ys)),
        )
        vertex = self.module._station_vertex(
            component, homography, (0.0, 0.0)
        )
        self.assertTrue(np.allclose(vertex, (100.0, 100.0)))

    def test_measurement_csv_contains_every_complete_mark(self):
        expected = expected_marks()
        measured = {
            (mark.station_id, mark.pass_id): (
                mark.nominal_x_mm,
                mark.nominal_y_mm,
            )
            for mark in expected
        }
        rows = list(
            csv.DictReader(
                io.StringIO(self.module.measurement_csv(expected, measured))
            )
        )
        self.assertEqual(len(rows), 4 + len(calibration_stations()) * len(PASS_SPECS))
        self.assertTrue(all(row["measured_x_mm"] for row in rows))
        self.assertTrue(all(row["measured_y_mm"] for row in rows))

    def test_dense_measurement_csv_records_layout_and_all_819_marks(self):
        expected = expected_marks(DENSE_LAYOUT)
        measured = {
            (mark.station_id, mark.pass_id): (
                mark.nominal_x_mm,
                mark.nominal_y_mm,
            )
            for mark in expected
        }
        rows = list(
            csv.DictReader(
                io.StringIO(
                    self.module.measurement_csv(
                        expected,
                        measured,
                        DENSE_LAYOUT,
                    )
                )
            )
        )
        self.assertEqual(
            len(rows),
            4 + 91 * len(DENSE_LAYOUT.pass_specs),
        )
        self.assertEqual({row["layout_id"] for row in rows}, {"dense-91-v3"})

    def test_dense_oriented_homography_uses_the_smaller_mark_centroid(self):
        expected = expected_marks(DENSE_LAYOUT)
        fiducials = tuple(
            mark for mark in expected if mark.section == "fiducial"
        )
        stations = tuple(
            mark for mark in expected if mark.section == "station"
        )
        homography = np.asarray(
            [[4.0, 0.0, 900.0], [0.0, -4.0, 900.0], [0.0, 0.0, 1.0]]
        )
        image_fiducials = np.asarray(
            [
                self.module._forward(
                    homography,
                    (mark.nominal_x_mm, mark.nominal_y_mm),
                )
                for mark in fiducials
            ]
        )
        centroids = np.asarray(
            [
                self.module._forward(
                    homography,
                    (
                        mark.nominal_x_mm - DENSE_LAYOUT.mark_arm_mm / 2.0,
                        mark.nominal_y_mm + DENSE_LAYOUT.mark_arm_mm / 2.0,
                    ),
                )
                for mark in stations
            ]
        )
        fitted, _points, order, score = self.module._fit_oriented_homography(
            fiducials,
            image_fiducials,
            stations,
            centroids,
            DENSE_LAYOUT,
        )
        self.assertEqual(order, (0, 1, 2, 3))
        self.assertLess(score[0], 1e-6)
        self.assertTrue(np.allclose(fitted, homography))

    def test_dense_seeded_sheet_resolves_arm_junctions_repeatably(self):
        scale = 5.0
        image_size = 1750
        image_center = (image_size - 1) / 2.0
        homography = np.asarray(
            [
                [scale, 0.0, image_center],
                [0.0, -scale, image_center],
                [0.0, 0.0, 1.0],
            ]
        )
        image = self.module.Image.new(
            "L",
            (image_size, image_size),
            255,
        )
        draw = self.module.ImageDraw.Draw(image)

        def image_point(x_mm, y_mm):
            return tuple(self.module._forward(homography, (x_mm, y_mm)))

        for _number, angle, x_mm, y_mm in fiducial_points(DENSE_LAYOUT):
            points = fiducial_mark_points(
                angle,
                x_mm,
                y_mm,
                DENSE_LAYOUT.fiducial_radial_arm_mm,
                DENSE_LAYOUT.fiducial_tangent_arm_mm,
            )
            for endpoint in points[1:]:
                draw.line(
                    (image_point(*points[0]), image_point(*endpoint)),
                    fill=0,
                    width=3,
                )
        for mark in expected_marks(DENSE_LAYOUT):
            if mark.section != "station":
                continue
            draw.line(
                (
                    image_point(
                        mark.nominal_x_mm - DENSE_LAYOUT.mark_arm_mm,
                        mark.nominal_y_mm,
                    ),
                    image_point(mark.nominal_x_mm, mark.nominal_y_mm),
                ),
                fill=0,
                width=3,
            )
            draw.line(
                (
                    image_point(mark.nominal_x_mm, mark.nominal_y_mm),
                    image_point(
                        mark.nominal_x_mm,
                        mark.nominal_y_mm + DENSE_LAYOUT.mark_arm_mm,
                    ),
                ),
                fill=0,
                width=3,
            )

        biased_seed = homography.copy()
        biased_seed[0, 2] += 30.0
        with tempfile.TemporaryDirectory() as temporary:
            image_path = Path(temporary) / "synthetic-dense-v3.png"
            image.save(image_path)
            expected, measured, diagnostic = self.module.measure_photo(
                image_path,
                layout=DENSE_LAYOUT,
                threshold=55,
                fiducial_threshold=35,
                blur_radius=3.0,
                minimum_station_dimension=14,
                maximum_station_dimension=60,
                seed_diagnostic={
                    "homography": biased_seed.tolist(),
                    "image_size_px": [image_size, image_size],
                },
            )
            expected_repeat, measured_repeat, repeat_diagnostic = (
                self.module.measure_photo(
                    image_path,
                    layout=DENSE_LAYOUT,
                    threshold=65,
                    fiducial_threshold=35,
                    blur_radius=3.0,
                    minimum_station_dimension=14,
                    maximum_station_dimension=60,
                    seed_diagnostic=diagnostic,
                )
            )

        self.assertEqual(set(measured), {
            (mark.station_id, mark.pass_id) for mark in expected
        })
        self.assertEqual(
            {(mark.station_id, mark.pass_id) for mark in expected_repeat},
            set(measured),
        )
        expected_fiducial_points = np.asarray(
            [
                self.module._forward(
                    homography,
                    (mark.nominal_x_mm, mark.nominal_y_mm),
                )
                for mark in expected
                if mark.section == "fiducial"
            ]
        )
        self.assertTrue(
            np.allclose(
                diagnostic["fiducial_points_px"],
                expected_fiducial_points,
                atol=2.0,
            ),
            "selected %s, expected %s"
            % (
                diagnostic["fiducial_points_px"],
                expected_fiducial_points,
            ),
        )
        self.assertEqual(
            diagnostic["component_counts"]["template_refined_station_L"],
            91 * len(DENSE_LAYOUT.pass_specs),
        )
        self.assertEqual(
            repeat_diagnostic["component_counts"]["template_refined_station_L"],
            diagnostic["component_counts"]["template_refined_station_L"],
        )
        repeat_delta = max(
            np.linalg.norm(
                np.asarray(measured[key]) - np.asarray(measured_repeat[key])
            )
            for key in measured
        )
        self.assertLess(repeat_delta, 0.01)


if __name__ == "__main__":
    unittest.main()
