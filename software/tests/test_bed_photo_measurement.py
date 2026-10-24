"""Photo-measurement helpers for the full-field bed calibration."""

import csv
import importlib.util
import io
from pathlib import Path
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

from converter_core.bed_calibration import (
    PASS_SPECS,
    calibration_stations,
    expected_marks,
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
        points = tuple(
            [(x_value, 20) for x_value in range(10, 21)]
            + [(20, y_value) for y_value in range(10, 20)]
        )
        component = self.module.Component(points, (10, 10, 20, 20))
        homography = np.asarray(
            [[4.0, 0.0, 100.0], [0.0, 4.0, 80.0], [0.0, 0.0, 1.0]]
        )
        vertex = self.module._station_vertex(
            component, homography, (0.0, 0.0)
        )
        self.assertTrue(np.allclose(vertex, (20.0, 20.0)))

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


if __name__ == "__main__":
    unittest.main()
