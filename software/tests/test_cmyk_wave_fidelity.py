"""Red/green tests for the objective CMYK Wave fidelity oracle."""

import importlib.util
import io
import json
import math
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


def load_oracle():
    path = ROOT / "tools" / "cmyk_wave_fidelity.py"
    spec = importlib.util.spec_from_file_location(
        "cmyk_wave_fidelity",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ORACLE = load_oracle()
DEFAULT_RECIPE_FACTORY = ORACLE.default_recipe


def safe_synthetic_recipe():
    recipe = DEFAULT_RECIPE_FACTORY()
    recipe.update(
        {
            "pitch": 4.0,
            "wave_period": 2.0,
            "wave_period_variation": 0.0,
            "wave_depth_intensity": 1.5,
        }
    )
    return recipe


def wave_paths(amplitude=0.6, cycles=4.0, span=80.0, rows=4):
    x = np.linspace(0.0, span, 321)
    paths = []
    for row in range(rows):
        y = (
            row * 4.0
            + amplitude
            * np.sin(2.0 * math.pi * cycles * (x - x[0]) / span)
        )
        paths.append(
            converter.WaveTrail(
                list(zip(x.tolist(), y.tolist())),
                wave_row_index=row,
            )
        )
    return paths


class DetailMetricTests(unittest.TestCase):
    def test_matching_detail_passes_and_flat_output_goes_red(self):
        yy, xx = np.mgrid[0:96, 0:96]
        source = np.stack(
            (
                0.15 + 0.70 * xx / 95.0,
                0.12 + 0.72 * yy / 95.0,
                0.20 + 0.55 * ((xx + yy) % 17) / 16.0,
            ),
            axis=-1,
        ).astype(np.float32)
        perfect = ORACLE.structure_metrics(source, source)
        flat = ORACLE.structure_metrics(
            source,
            np.zeros_like(source),
        )
        self.assertGreaterEqual(
            perfect["structure_correlation"],
            ORACLE.THRESHOLDS["detail_structure_correlation_min"],
        )
        self.assertGreaterEqual(
            perfect["edge_correlation"],
            ORACLE.THRESHOLDS["detail_edge_correlation_min"],
        )
        self.assertLess(
            perfect["luminance_mae"],
            ORACLE.THRESHOLDS["detail_luminance_mae_max"],
        )
        self.assertLess(
            flat["structure_correlation"],
            ORACLE.THRESHOLDS["detail_structure_correlation_min"],
        )
        self.assertLess(
            flat["edge_correlation"],
            ORACLE.THRESHOLDS["detail_edge_correlation_min"],
        )
        self.assertGreater(
            flat["luminance_mae"],
            ORACLE.THRESHOLDS["detail_luminance_mae_max"],
        )
        self.assertEqual(
            set(flat["scale_correlations"]),
            {"radius_1px", "radius_4px"},
        )


class ColorMetricTests(unittest.TestCase):
    def test_rgb_and_lab_errors_can_all_go_red(self):
        source = np.full((32, 32, 3), (0.78, 0.42, 0.24), dtype=np.float32)
        perfect = ORACLE.color_metrics(source, source)
        swapped = ORACLE.color_metrics(
            source,
            np.full((32, 32, 3), (0.24, 0.42, 0.78), dtype=np.float32),
        )
        dark = ORACLE.color_metrics(
            source,
            np.full((32, 32, 3), (0.08, 0.08, 0.08), dtype=np.float32),
        )
        gray = ORACLE.color_metrics(
            source,
            np.full((32, 32, 3), 0.40, dtype=np.float32),
        )
        self.assertLess(perfect["delta_e76_mean"], 1e-9)
        self.assertGreater(
            swapped["rgb_mae"],
            ORACLE.THRESHOLDS["color_rgb_mae_max"],
        )
        self.assertGreater(
            swapped["hue_error_deg"],
            ORACLE.THRESHOLDS["color_hue_error_deg_max"],
        )
        self.assertGreater(
            gray["chroma_mae"],
            ORACLE.THRESHOLDS["color_chroma_mae_max"],
        )
        self.assertGreater(
            swapped["delta_e76_mean"],
            ORACLE.THRESHOLDS["color_delta_e76_mean_max"],
        )
        self.assertGreater(
            dark["lightness_mae"],
            ORACLE.THRESHOLDS["color_lightness_mae_max"],
        )


class InkAndWaveMetricTests(unittest.TestCase):
    def test_per_ink_coverage_bias_goes_red(self):
        size = 64
        source = np.ones((size, size, 3), dtype=np.float32)
        rendered = np.ones_like(source)
        target = {
            channel: np.full((size, size), 0.20, dtype=np.float32)
            for channel in ORACLE.CHANNELS
        }
        coverage = {
            channel: np.full((size, size), 0.75, dtype=np.float32)
            for channel in ORACLE.CHANNELS
        }
        mapping = ORACLE.PageMapping(
            page_w=200.0,
            page_h=200.0,
            x_mm=0.0,
            y_mm=0.0,
            width_mm=200.0,
            height_mm=200.0,
        )
        regions = ORACLE.region_metrics(
            source,
            rendered,
            coverage,
            target,
            mapping,
            size,
        )
        bias = regions["family_portrait"]["ink"]["c"]["coverage_bias"]
        self.assertGreater(
            abs(bias),
            ORACLE.THRESHOLDS["ink_mean_absolute_bias_max"],
        )

    def test_sine_rows_pass_each_wave_geometry_metric(self):
        result = ORACLE.measure_wave_paths(
            wave_paths(),
            0.0,
            2.2,
        )
        self.assertGreaterEqual(
            result["median_span_mm"],
            ORACLE.THRESHOLDS["wave_span_min_mm"],
        )
        self.assertGreaterEqual(
            result["median_amplitude_peak_to_peak_mm"],
            ORACLE.THRESHOLDS["wave_amplitude_min_mm"],
        )
        self.assertGreaterEqual(
            result["median_cycles"],
            ORACLE.THRESHOLDS["wave_cycles_min"],
        )
        self.assertLessEqual(
            result["median_flat_span_fraction"],
            ORACLE.THRESHOLDS["wave_flat_span_fraction_max"],
        )
        self.assertGreaterEqual(
            result["median_interior_amplitude_ratio"],
            ORACLE.THRESHOLDS["wave_interior_amplitude_ratio_min"],
        )

    def test_span_and_amplitude_metrics_go_red(self):
        short = ORACLE.measure_wave_paths(
            wave_paths(span=0.5, cycles=2.0),
            0.0,
            2.2,
        )
        flat = ORACLE.measure_wave_paths(
            wave_paths(amplitude=0.0),
            0.0,
            2.2,
        )
        self.assertLess(
            short["median_span_mm"],
            ORACLE.THRESHOLDS["wave_span_min_mm"],
        )
        self.assertLess(
            flat["median_amplitude_peak_to_peak_mm"],
            ORACLE.THRESHOLDS["wave_amplitude_min_mm"],
        )
        self.assertGreaterEqual(
            flat["median_flat_span_fraction"],
            ORACLE.THRESHOLDS["wave_flat_span_fraction_max"],
        )

    def test_cycles_metric_catches_a_non_oscillating_row(self):
        xs = np.linspace(0.0, 80.0, 321)
        hump = 0.7 * np.sin(np.pi * xs / 80.0)
        paths = [
            converter.WaveTrail(
                list(zip(xs.tolist(), hump.tolist())),
                wave_row_index=0,
            )
        ]
        result = ORACLE.measure_wave_paths(paths, 0.0, 2.2)
        self.assertGreaterEqual(
            result["median_amplitude_peak_to_peak_mm"],
            ORACLE.THRESHOLDS["wave_amplitude_min_mm"],
        )
        self.assertLess(
            result["median_cycles"],
            ORACLE.THRESHOLDS["wave_cycles_min"],
        )

    def test_interior_variation_rejects_boundary_only_hooks(self):
        xs = np.linspace(0.0, 80.0, 321)
        edge = 0.015 * 80.0
        residual = np.exp(
            -((xs - edge) / 0.7) ** 2
        ) + np.exp(-((xs - (80.0 - edge)) / 0.7) ** 2)
        paths = [
            converter.WaveTrail(
                list(zip(xs.tolist(), (residual * 0.8).tolist())),
                wave_row_index=0,
            )
        ]
        result = ORACLE.measure_wave_paths(paths, 0.0, 2.2)
        self.assertGreaterEqual(
            result["median_amplitude_peak_to_peak_mm"],
            ORACLE.THRESHOLDS["wave_amplitude_min_mm"],
        )
        self.assertLess(
            result["median_interior_amplitude_ratio"],
            ORACLE.THRESHOLDS["wave_interior_amplitude_ratio_min"],
        )


class CoverageFidelityTests(unittest.TestCase):
    def _ramp_target(self, size=64):
        yy, xx = np.mgrid[0:size, 0:size]
        ramp = (
            (xx.astype(np.float64) + yy.astype(np.float64))
            / (2.0 * (size - 1))
        )
        target = {channel: ramp for channel in ORACLE.CHANNELS}
        return target

    def test_coverage_metrics_distinguish_tone_tracking_from_flat(self):
        target = self._ramp_target()
        tracking = {
            channel: target[channel].copy()
            for channel in ORACLE.CHANNELS
        }
        flat = {
            channel: np.zeros((64, 64), dtype=np.float64)
            for channel in ORACLE.CHANNELS
        }
        tracking_metrics = ORACLE.coverage_fidelity_metrics(
            tracking,
            target,
        )
        flat_metrics = ORACLE.coverage_fidelity_metrics(flat, target)
        self.assertLess(
            tracking_metrics["c"]["coverage_mae"],
            ORACLE.THRESHOLDS["ink_coverage_mae_max"],
        )
        self.assertGreater(
            tracking_metrics["c"]["coverage_correlation"],
            ORACLE.THRESHOLDS["ink_coverage_correlation_min"],
        )
        self.assertGreater(
            flat_metrics["c"]["coverage_mae"],
            ORACLE.THRESHOLDS["ink_coverage_mae_max"],
        )
        self.assertLess(
            flat_metrics["c"]["coverage_correlation"],
            ORACLE.THRESHOLDS["ink_coverage_correlation_min"],
        )
        blank = {
            channel: np.zeros((64, 64), dtype=np.float64)
            for channel in ORACLE.CHANNELS
        }
        blank_metrics = ORACLE.coverage_fidelity_metrics(blank, target)
        self.assertGreater(
            blank_metrics["c"]["coverage_mae"],
            ORACLE.THRESHOLDS["ink_coverage_mae_max"],
        )

    def test_coverage_checks_go_red_on_a_flat_screen(self):
        target = self._ramp_target()
        blank = {
            channel: np.zeros((64, 64), dtype=np.float64)
            for channel in ORACLE.CHANNELS
        }
        metrics = ORACLE.coverage_fidelity_metrics(blank, target)
        checks = {
            check["name"]: check
            for check in ORACLE._coverage_fidelity_checks(metrics)
        }
        self.assertFalse(checks["ink.cyan.coverage_mae_max"]["passed"])
        self.assertFalse(
            checks["ink.cyan.coverage_correlation_min"]["passed"]
        )


class DepthAndGcodeTests(unittest.TestCase):
    def _global_wave(self, amplitude):
        return {
            channel: ORACLE.measure_wave_paths(
                wave_paths(amplitude=amplitude),
                0.0,
                2.2,
            )
            for channel in ORACLE.CHANNELS
        }

    def _fidelity_regions(self):
        record = {
            "detail": {
                "structure_correlation": 1.0,
                "edge_correlation": 1.0,
                "luminance_mae": 0.0,
            },
            "color": {
                "rgb_mae": 0.0,
                "lightness_mae": 0.0,
                "chroma_mae": 0.0,
                "hue_error_deg": 0.0,
                "delta_e76_mean": 0.0,
            },
            "ink": {
                channel: {"coverage_bias": 0.0}
                for channel in ORACLE.CHANNELS
            },
        }
        return {name: dict(record) for name in ORACLE.REGIONS}

    def _region_wave(self):
        inks = self._global_wave(0.60)
        return {
            name: {
                "inks": {
                    channel: dict(record)
                    for channel, record in inks.items()
                }
            }
            for name in ORACLE.REGIONS
        }

    def _passing_build_arguments(self):
        fidelity = self._fidelity_regions()
        global_wave = self._global_wave(0.60)
        wave = {
            "inks": global_wave,
            "regions": self._region_wave(),
        }
        gcode = {
            "metrics": {
                channel: dict(record)
                for channel, record in global_wave.items()
            },
            "programs": {
                channel: {"has_fixed_baseline_header": True}
                for channel in ORACLE.CHANNELS
            },
            "regions": self._region_wave(),
        }
        depth = {
            "material_geometry_change": True,
            "median_rms_delta_mm": 1.0,
        }
        return fidelity, wave, depth, gcode

    def test_identical_depth_geometry_goes_red_and_high_contrast_passes(self):
        neutral = self._global_wave(0.20)
        identical = ORACLE.depth_geometry_comparison(neutral, neutral)
        materially_different = ORACLE.depth_geometry_comparison(
            neutral,
            self._global_wave(0.60),
        )
        self.assertFalse(identical["material_geometry_change"])
        self.assertLess(
            identical["median_rms_delta_mm"],
            ORACLE.THRESHOLDS["depth_geometry_delta_min_mm"],
        )
        self.assertTrue(
            materially_different["material_geometry_change"]
        )
        self.assertGreaterEqual(
            materially_different["median_rms_ratio"],
            ORACLE.THRESHOLDS["depth_geometry_ratio_min"],
        )

    def test_gcode_rows_are_decoded_from_emitted_points(self):
        gcode = "\n".join(
            (
                "(contour 1)",
                "(wave row 3 baseline 12.0000 mm)",
                "G1 X-10.000 Y0.000 A0.000 F3000 (travel)",
                "M3",
                "G1 X-5.000 Y1.000 A0.000 F700 (fixed)",
                "G1 X5.000 Y-1.000 A0.000 F700 (fixed)",
                "G1 X10.000 Y0.000 A0.000 F700 (fixed)",
                "M5",
            )
        )
        rows = ORACLE.decode_gcode_wave_rows(
            gcode,
            ratio=1.0,
            centre=(0.0, 0.0),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].wave_row_index, 3)
        xs = [point[0] for point in rows[0]]
        self.assertAlmostEqual(min(xs), -10.0)
        self.assertAlmostEqual(max(xs), 10.0)

    def test_gcode_gate_goes_red_when_a_row_is_missing(self):
        empty = {
            channel: {
                "rows": 0,
                "median_span_mm": 0.0,
                "median_amplitude_peak_to_peak_mm": 0.0,
                "median_cycles": 0.0,
                "median_flat_span_fraction": 1.0,
                "median_interior_amplitude_ratio": 0.0,
            }
            for channel in ORACLE.CHANNELS
        }
        depth = {"material_geometry_change": True, "median_rms_delta_mm": 1.0}
        wave = {
            "inks": self._global_wave(0.60),
            "regions": {},
        }
        regions = {
            "family_portrait": {
                "detail": {
                    "structure_correlation": 1.0,
                    "edge_correlation": 1.0,
                    "luminance_mae": 0.0,
                },
                "color": {
                    "rgb_mae": 0.0,
                    "lightness_mae": 0.0,
                    "chroma_mae": 0.0,
                    "hue_error_deg": 0.0,
                    "delta_e76_mean": 0.0,
                },
                "ink": {
                    channel: {"coverage_bias": 0.0}
                    for channel in ORACLE.CHANNELS
                },
            }
        }
        checks = ORACLE.build_checks(
            regions,
            wave,
            depth,
            {"metrics": empty},
        )
        rows_check = next(
            check
            for check in checks
            if check["name"] == "gcode.cyan.rows_min"
        )
        self.assertFalse(rows_check["passed"])

    def test_one_straight_crop_reddens_every_region_geometry_gate(self):
        fidelity, wave, depth, gcode = self._passing_build_arguments()
        for scope in (wave["regions"], gcode["regions"]):
            record = scope["child_face"]["inks"]["c"]
            record.update(
                {
                    "median_span_mm": 1.0,
                    "median_amplitude_peak_to_peak_mm": 0.0,
                    "median_cycles": 0.0,
                    "median_flat_span_fraction": 1.0,
                    "median_interior_amplitude_ratio": 0.0,
                }
            )
            scope["child_face"]["inks"]["c"] = record
        checks = {
            check["name"]: check
            for check in ORACLE.build_checks(
                fidelity,
                wave,
                depth,
                gcode,
            )
        }
        for prefix in ("wave", "gcode"):
            for metric in (
                "median_span_mm",
                "median_amplitude_peak_to_peak_mm",
                "median_cycles",
                "median_flat_span_fraction",
                "median_interior_amplitude_ratio",
            ):
                self.assertFalse(
                    checks[f"{prefix}.{metric}_worst"]["passed"]
                )
        self.assertTrue(checks["wave.regions_with_rows"]["passed"])
        self.assertTrue(checks["gcode.regions_with_rows"]["passed"])

    def test_fixed_baseline_header_is_a_release_gate(self):
        fidelity, wave, depth, gcode = self._passing_build_arguments()
        gcode["programs"]["k"]["has_fixed_baseline_header"] = False
        checks = {
            check["name"]: check
            for check in ORACLE.build_checks(
                fidelity,
                wave,
                depth,
                gcode,
            )
        }
        self.assertFalse(checks["gcode.black.fixed_baseline_header"]["passed"])

    def test_unavailable_gcode_witness_is_red_without_crashing(self):
        fidelity, wave, depth, _gcode = self._passing_build_arguments()
        checks = {
            check["name"]: check
            for check in ORACLE.build_checks(
                fidelity,
                wave,
                depth,
                {
                    "available": False,
                    "error_type": "ValueError",
                    "error": "clearance rejected",
                },
            )
        }
        self.assertFalse(checks["gcode.available"]["passed"])


class PipelineSmokeTests(unittest.TestCase):
    def test_live_failure_profile_is_the_primary_baseline(self):
        recipe = ORACLE.default_recipe()
        self.assertEqual(recipe["pitch"], 1.15)
        self.assertEqual(recipe["scale"], 1.10)
        self.assertAlmostEqual(
            recipe["pitch"] * recipe["scale"],
            1.265,
        )
        self.assertEqual(recipe["wave_depth_intensity"], 1.50)
        self.assertEqual(recipe["wave_period_variation"], 1.00)
        self.assertEqual(
            recipe["weights"],
            {"c": 0.90, "m": 0.85, "y": 1.15, "k": 1.00},
        )
        self.assertEqual(recipe["gcr"], 0.25)
        self.assertEqual(recipe["gamma"], 1.35)
        self.assertEqual(recipe["brightness"], 160.0)
        self.assertEqual(recipe["contrast"], 1.15)
        self.assertEqual(recipe["saturation"], 1.10)
        self.assertEqual(recipe["resolution"], 10000)
        self.assertEqual(
            recipe["row_clearance_mode"],
            "pen-plus-edge",
        )

    def test_screen_worker_honors_the_selected_production_style(self):
        recipe = safe_synthetic_recipe()
        recipe["style"] = "waves_fidelity"
        tones = {
            channel: np.ones((8, 8), dtype=np.float32)
            for channel in ORACLE.CHANNELS
        }
        tones["depth"] = np.full((8, 8), 0.25, dtype=np.float32)
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 32.0,
            "height_mm": 32.0,
            "pixels_w": 8,
            "pixels_h": 8,
        }
        with mock.patch.object(
            ORACLE.converter,
            "screen_channel",
            return_value=[],
        ) as screen:
            channel, marks, error = ORACLE._screen_one_channel(
                (tones, geometry, recipe, "c", 0, 1.5)
            )
        self.assertEqual(channel, "c")
        self.assertEqual(marks, [])
        self.assertIsNone(error)
        self.assertEqual(
            screen.call_args.kwargs["style"],
            "waves_fidelity",
        )
        self.assertTrue(
            np.array_equal(
                screen.call_args.kwargs["depth_tone"],
                tones["depth"],
            )
        )

    def test_real_screen_path_is_deterministic_and_machine_readable(self):
        with tempfile.TemporaryDirectory(prefix="wave-fidelity-test-") as folder:
            image_path = Path(folder) / "gradient.png"
            yy, xx = np.mgrid[0:80, 0:80]
            image = np.stack(
                (
                    0.15 + 0.70 * xx / 79.0,
                    0.25 + 0.55 * yy / 79.0,
                    0.20 + 0.30 * (xx + yy) / 158.0,
                ),
                axis=-1,
            )
            Image.fromarray(
                (np.clip(image, 0.0, 1.0) * 255.0).astype(np.uint8)
            ).save(image_path)
            with mock.patch.object(
                ORACLE,
                "default_recipe",
                side_effect=safe_synthetic_recipe,
            ):
                first, _ = ORACLE.evaluate(
                    image_path,
                    render_pixels=96,
                    run_gcode=False,
                )
                second, _ = ORACLE.evaluate(
                    image_path,
                    render_pixels=96,
                    run_gcode=False,
                )
        first.pop("artifacts", None)
        second.pop("artifacts", None)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "FAIL")
        self.assertIn("failed_checks", first)
        self.assertIn("crop_regions", first)
        self.assertIn("depth_comparison", first)

    def test_console_output_is_json_and_exit_code_is_red_on_failure(self):
        with tempfile.TemporaryDirectory(prefix="wave-fidelity-cli-") as folder:
            image_path = Path(folder) / "flat.png"
            Image.new("RGB", (64, 64), "gray").save(image_path)
            output = io.StringIO()
            with (
                mock.patch.object(
                    ORACLE,
                    "default_recipe",
                    side_effect=safe_synthetic_recipe,
                ),
                redirect_stdout(output),
            ):
                status = ORACLE.main(
                    [
                        "--image",
                        str(image_path),
                        "--render-pixels",
                        "64",
                        "--jobs",
                        "1",
                        "--no-gcode",
                        "--no-artifacts",
                    ]
                )
        self.assertEqual(status, 1)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["status"], "FAIL")
        self.assertTrue(payload["failed_checks"])

    def test_screen_error_is_captured_and_reported_as_fail(self):
        with tempfile.TemporaryDirectory(prefix="wave-fidelity-err-") as folder:
            image_path = Path(folder) / "flat.png"
            Image.new("RGB", (64, 64), "gray").save(image_path)
            with (
                mock.patch.object(
                    ORACLE,
                    "default_recipe",
                    side_effect=safe_synthetic_recipe,
                ),
                mock.patch.object(
                    ORACLE.converter,
                    "screen_channel",
                    side_effect=ValueError("boom"),
                ),
            ):
                report, _ = ORACLE.evaluate(
                    image_path,
                    render_pixels=64,
                    run_gcode=False,
                )
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["screen_errors"]["high_depth_intensity"])
        self.assertIn(
            "boom",
            report["screen_errors"]["high_depth_intensity"]["c"],
        )


if __name__ == "__main__":
    unittest.main()
