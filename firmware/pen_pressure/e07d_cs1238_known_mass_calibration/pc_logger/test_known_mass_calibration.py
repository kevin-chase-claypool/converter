import csv
import tempfile
import unittest
from pathlib import Path

from known_mass_calibration_gui import (
    KnownMassCalibrationApp,
    SAME_FORCE_DIRECTION,
    UPWARD_PEN_REACTION,
    apply_fixture_mass,
    linear_fit,
    project_printing_force_fit,
    raw_for_projected_force,
)


class KnownMassCalibrationTests(unittest.TestCase):
    def test_opposite_pen_reaction_inverts_the_downward_weight_fit(self):
        weight_fit, _ = linear_fit([100.0, 120.0, 140.0], [0.0, 10.0, 20.0])

        projection = project_printing_force_fit(weight_fit, UPWARD_PEN_REACTION)

        self.assertAlmostEqual(projection["grams_per_raw_count"], -0.5)
        self.assertAlmostEqual(projection["offset_g"], 50.0)
        self.assertAlmostEqual(projection["raw_at_40g"], 20.0)
        self.assertAlmostEqual(projection["raw_at_60g"], -20.0)

    def test_same_direction_preserves_the_weight_fit(self):
        weight_fit, _ = linear_fit([100.0, 120.0, 140.0], [0.0, 10.0, 20.0])

        projection = project_printing_force_fit(weight_fit, SAME_FORCE_DIRECTION)

        self.assertAlmostEqual(projection["grams_per_raw_count"], 0.5)
        self.assertAlmostEqual(projection["offset_g"], -50.0)
        self.assertAlmostEqual(projection["raw_at_40g"], 180.0)
        self.assertAlmostEqual(projection["raw_at_60g"], 220.0)

    def test_fixture_mass_is_added_to_physical_labels_without_changing_raw_values(self):
        points = [{"mass_g": 0.0, "raw_mean": 100.0}, {"mass_g": 5.0, "raw_mean": 120.0}]

        corrected = apply_fixture_mass(points, 2.5)

        self.assertEqual([point["mass_g"] for point in corrected], [2.5, 7.5])
        self.assertEqual([point["raw_mean"] for point in corrected], [100.0, 120.0])
        self.assertEqual([point["mass_g"] for point in points], [0.0, 5.0])

    def test_raw_for_projected_force_inverts_projection(self):
        fit, _ = linear_fit([100.0, 120.0, 140.0], [0.0, 10.0, 20.0])
        projection = project_printing_force_fit(fit, UPWARD_PEN_REACTION)

        self.assertAlmostEqual(raw_for_projected_force(projection, 50.0), 0.0)

    def test_projection_graph_is_written_separately_from_weight_graph(self):
        raw = [100.0, 120.0, 140.0]
        grams = [0.0, 10.0, 20.0]
        fit, residuals = linear_fit(raw, grams)
        projection = project_printing_force_fit(fit, UPWARD_PEN_REACTION)
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            points = []
            for number, (raw_value, mass) in enumerate(zip(raw, grams), start=1):
                raw_file = run_dir / f"point_{number:03d}.csv"
                with raw_file.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(("time_us", "cs1238_raw"))
                    writer.writerow((0, int(raw_value)))
                    writer.writerow((1000, int(raw_value)))
                points.append({
                    "mass_g": mass,
                    "pass": "Loading",
                    "raw_mean": raw_value,
                    "raw_file": raw_file.name,
                })
            app = KnownMassCalibrationApp.__new__(KnownMassCalibrationApp)
            app.current_run_dir = run_dir
            app._make_graphs(points, raw, grams, residuals, fit, projection)

            self.assertTrue((run_dir / "calibration_curve.png").is_file())
            self.assertTrue((run_dir / "estimated_pen_force_projection.png").is_file())


if __name__ == "__main__":
    unittest.main()
