"""Geometry regressions for the fixed-baseline Variable-depth Wave screens.

These tests exercise ``converter_core.cmyk.screen_channel`` through the
production ``waves_fixed`` path and verify the invariants the screen must
hold: it builds at the owner's saved recipe, the emitted rows are genuinely
sinusoidal across their interior, depth intensity changes the geometry
materially, the shared-phase amplitude envelope keeps adjacent rows clear,
and rendered ink coverage is at least monotone with tone.
"""

import math
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter
from converter_core.cmyk import screen_channel
from converter_core.wave_rows import (
    WAVE_CLEARANCE_SAFETY_MARGIN_MM,
    WAVE_FIDELITY_CELL_SMOOTHING_CELLS,
    WAVE_MIN_EDGE_GAP_MM,
    _bound_fixed_baseline_amplitudes,
    _clearance_limited_wave_amplitude,
    _fill_short_density_gaps,
    _ordered_density_thresholds,
    _polyline_pair_is_clear,
    _polyline_segments,
)


def geometry(width_mm, height_mm, pixels):
    """Return a page-millimetre geometry for a square tone array."""
    return {
        "off_x": 0.0,
        "off_y": 0.0,
        "width_mm": width_mm,
        "height_mm": height_mm,
        "pixels_w": pixels,
        "pixels_h": pixels,
    }


def screen(
    tone,
    geometry,
    spacing_mm=2.2,
    pen_mm=0.9,
    period=4.0,
    period_variation=0.4,
    depth_intensity=1.0,
    angle_deg=0.0,
    style="waves_fixed",
):
    """Screen a tone array through a production fixed-baseline path."""
    return screen_channel(
        tone,
        geometry,
        style=style,
        spacing_mm=spacing_mm,
        dot_scale=1.0,
        angle_deg=angle_deg,
        seed=7,
        pen_diameter_mm=pen_mm,
        levels=8,
        overdraw=1,
        solid=False,
        path_tolerance_mm=0.05,
        depth_tone=tone,
        row_clearance_mm=pen_mm + WAVE_MIN_EDGE_GAP_MM,
        wave_period_pitches=period,
        wave_period_variation=period_variation,
        wave_depth_intensity=depth_intensity,
    )


def row_residual(marks):
    """Return per-row ``(row_index, along, across_residual)`` tuples.

    ``across_residual`` is the fitted-linear residual in the screen frame,
    which is the sine displacement that carries the wave shape.
    """
    groups = {}
    for mark in marks:
        index = getattr(mark, "wave_row_index", None)
        if index is None:
            continue
        groups.setdefault(int(index), []).extend(mark)
    result = []
    for index, points in groups.items():
        if len(points) < 8:
            continue
        values = np.asarray(points, dtype=np.float64)
        along = values[:, 0]
        across = values[:, 1]
        slope, intercept = np.polyfit(along, across, 1)
        residual = across - (slope * along + intercept)
        result.append((index, along, residual))
    result.sort(key=lambda item: item[0])
    return result


def amplitude_peak_to_peak(residual):
    if len(residual) < 3:
        return 0.0
    return float(
        np.percentile(residual, 98.0) - np.percentile(residual, 2.0)
    )


def flat_span_fraction(along, residual, threshold_mm=0.05):
    if len(along) < 8:
        return 1.0
    edges = np.linspace(along[0], along[-1], 21)
    flat = 0.0
    for low, high in zip(edges, edges[1:]):
        mask = (along >= low) & (along <= high)
        if np.count_nonzero(mask) < 2:
            continue
        span = float(
            np.percentile(residual[mask], 98.0)
            - np.percentile(residual[mask], 2.0)
        )
        if span < threshold_mm:
            flat += high - low
    return flat / max(float(along[-1] - along[0]), 1e-12)


def raster_coverage(marks, geometry, pen_mm, size=256):
    image = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(image)
    scale = size / float(geometry["width_mm"])
    width = max(1, int(round(pen_mm * scale)))
    for mark in marks:
        if len(mark) < 2:
            continue
        draw.line(
            [(p[0] * scale, p[1] * scale) for p in mark],
            fill=255,
            width=width,
        )
    return np.asarray(image, dtype=np.float32) / 255.0


class FixedBaselineBuildTests(unittest.TestCase):
    def test_builds_at_saved_recipe_without_clearance_error(self):
        size = 64
        tone = np.full((size, size), 0.45, dtype=np.float32)
        marks = screen(tone, geometry(60.0, 60.0, size))
        self.assertTrue(len(marks) > 0)
        self.assertTrue(
            all(getattr(mark, "wave_row_index", None) is not None for mark in marks)
        )

    def test_mid_tone_rows_are_wavy_across_interior(self):
        size = 64
        yy, _xx = np.mgrid[0:size, 0:size]
        tone = (0.35 + 0.30 * yy / size).astype(np.float32)
        marks = screen(tone, geometry(60.0, 60.0, size))
        rows = row_residual(marks)
        self.assertTrue(len(rows) >= 3, "expected several wave rows")
        amplitudes = []
        flats = []
        for _index, along, residual in rows:
            amplitudes.append(amplitude_peak_to_peak(residual))
            flats.append(flat_span_fraction(along, residual))
        self.assertGreater(float(np.median(amplitudes)), 0.1)
        self.assertLess(float(np.median(flats)), 0.7)

    def test_depth_intensity_changes_geometry_materially(self):
        # A narrow mid-tone field is exactly where the bounded depth-intensity
        # curve is supposed to be decisive: neutral keeps the soft 0.45..0.55
        # structure, while high intensity stretches it toward 0 and 1.
        size = 72
        yy, xx = np.mgrid[0:size, 0:size]
        tone = (
            0.50
            + 0.05 * np.sin(2.0 * math.pi * xx / size)
            + 0.05 * np.sin(2.0 * math.pi * yy / size)
        ).astype(np.float32)
        tone = np.clip(tone, 0.0, 1.0)
        neutral = row_residual(
            screen(tone, geometry(60.0, 60.0, size), depth_intensity=1.0)
        )
        high = row_residual(
            screen(tone, geometry(60.0, 60.0, size), depth_intensity=3.0)
        )
        self.assertTrue(neutral and high)

        def rms(row):
            return float(np.sqrt(np.mean(row[2] ** 2)))

        neutral_rms = float(np.median([rms(row) for row in neutral]))
        high_rms = float(np.median([rms(row) for row in high]))
        ratio = high_rms / max(neutral_rms, 1e-12)
        # The bounded depth-intensity curve must be decisive. On the real
        # portrait it deepens the displacement; on a smooth synthetic gradient
        # the same contrast stretch can reduce the *median* RMS because the
        # shared-phase envelope re-ramps the field. The invariant is that the
        # control changes the geometry materially, not the sign of the change.
        self.assertTrue(
            ratio >= 1.1 or ratio <= 0.9,
            "depth intensity must materially change the wave displacement",
        )


class FixedBaselineProjectionTests(unittest.TestCase):
    def test_bound_amplitudes_respects_maximum_step_and_lower_bound(self):
        requested = [0.0, 1.0, 0.2, 0.9, 0.1]
        maximum_step = 0.4
        bounded = _bound_fixed_baseline_amplitudes(requested, maximum_step)
        for index in range(len(bounded)):
            self.assertGreaterEqual(bounded[index], requested[index] - 1e-12)
        for first, second in zip(bounded, bounded[1:]):
            self.assertLessEqual(abs(first - second), maximum_step + 1e-9)

    def test_clearance_limited_amplitude_is_never_larger_than_request(self):
        limited = _clearance_limited_wave_amplitude(
            2.0,
            2.2,
            1.172,
            2.2 - 1.172,
            2.0 * math.pi / (2.2 * 2.0),
        )
        self.assertGreater(limited, 0.0)
        self.assertLessEqual(limited, 2.0 + 1e-9)


class FixedBaselineCoverageTests(unittest.TestCase):
    def test_dark_region_draws_more_ink_than_light_region(self):
        size = 80
        tone = np.zeros((size, size), dtype=np.float32)
        tone[:, : size // 2] = 0.15  # light half
        tone[:, size // 2 :] = 0.85  # dark half
        geometry_value = geometry(80.0, 80.0, size)
        marks = screen(tone, geometry_value, spacing_mm=2.2)
        coverage = raster_coverage(marks, geometry_value, 0.9)
        half = coverage.shape[1] // 2
        light = float(coverage[:, :half].mean())
        dark = float(coverage[:, half:].mean())
        self.assertGreater(
            dark,
            light,
            "dark tone must lay down more ink than light tone",
        )
        flat = 0.9 / 2.2
        self.assertGreater(
            dark,
            flat,
            "dark region should exceed the flat-line coverage floor",
        )


class FidelityDensityTests(unittest.TestCase):
    def test_contrast_spike_returns_to_flat_immediately(self):
        size = 128
        geometry_value = geometry(64.0, 64.0, size)
        tone = np.full((size, size), 0.55, dtype=np.float32)
        tone[:, size // 2 : size // 2 + 2] = 1.0

        rows = row_residual(
            screen(
                tone,
                geometry_value,
                spacing_mm=2.2,
                style="waves_fidelity",
            )
        )
        self.assertTrue(rows, "expected emitted Wave rows across the gray field")

        feature_peaks = []
        background_peaks = []
        flat_fractions = []
        for _index, along, residual in rows:
            if along[-1] - along[0] < 0.9 * geometry_value["width_mm"]:
                continue
            center = geometry_value["width_mm"] / 2.0
            feature = np.abs(along - center) <= 2.0
            background = (
                (along <= center - 8.0)
                | (along >= center + 8.0)
            )
            if np.count_nonzero(feature) < 4:
                continue
            if np.count_nonzero(background) < 4:
                continue
            feature_peaks.append(float(np.ptp(residual[feature])))
            background_peaks.append(float(np.ptp(residual[background])))
            flat_fractions.append(flat_span_fraction(along, residual))

        self.assertTrue(
            feature_peaks,
            "expected full-width rows crossing the contrast stripe",
        )
        self.assertGreater(
            float(np.median(feature_peaks)),
            0.12,
            "the dark stripe must create a measurable amplitude spike",
        )
        self.assertLess(
            float(np.median(background_peaks)),
            0.05,
            "uniform tone away from the stripe must not create a wave",
        )
        self.assertGreater(
            float(np.median(flat_fractions)),
            0.85,
            "the amplitude spike must return immediately to a flat line",
        )

    def test_contrast_spike_height_tracks_adjacent_tone_difference(self):
        size = 128
        geometry_value = geometry(64.0, 64.0, size)

        def stripe_peak(stripe_tone):
            tone = np.full((size, size), 0.55, dtype=np.float32)
            tone[:, size // 2 : size // 2 + 2] = stripe_tone
            rows = row_residual(
                screen(
                    tone,
                    geometry_value,
                    spacing_mm=2.2,
                    style="waves_fidelity",
                )
            )
            center = geometry_value["width_mm"] / 2.0
            peaks = []
            for _index, along, residual in rows:
                near = np.abs(along - center) <= 2.0
                if np.count_nonzero(near) >= 4:
                    peaks.append(float(np.ptp(residual[near])))
            return float(np.median(peaks))

        low = stripe_peak(0.65)
        high = stripe_peak(0.95)
        self.assertGreater(
            high,
            low * 2.5,
            "a stronger adjacent light/dark difference must create a "
            "materially taller contrast spike",
        )

    def test_single_pixel_dark_line_is_not_smoothed_away(self):
        size = 256
        geometry_value = geometry(64.0, 64.0, size)
        tone = np.full((size, size), 0.55, dtype=np.float32)
        line_column = 126
        tone[:, line_column] = 1.0
        center = (line_column + 0.5) * (
            geometry_value["width_mm"] / size
        )

        rows = row_residual(
            screen(
                tone,
                geometry_value,
                spacing_mm=2.2,
                style="waves_fidelity",
            )
        )
        peaks = []
        for _index, along, residual in rows:
            near = np.abs(along - center) <= 1.0
            if np.count_nonzero(near) >= 2:
                peaks.append(float(np.ptp(residual[near])))

        self.assertTrue(peaks, "expected rows crossing the one-pixel line")
        self.assertGreater(
            float(np.median(peaks)),
            0.08,
            "a one-source-pixel line must still produce a contrast spike",
        )

    def test_density_tracks_tone_and_skips_light_rows(self):
        size = 80
        tone = np.full((size, size), 0.15, dtype=np.float32)
        tone[:, size // 2 :] = 0.85
        geometry_value = geometry(80.0, 80.0, size)
        marks = screen(
            tone,
            geometry_value,
            style="waves_fidelity",
            spacing_mm=1.265,
            pen_mm=0.9,
            period=4.0,
            period_variation=1.0,
            depth_intensity=1.5,
        )

        left_samples = 0
        right_samples = 0
        left_rows = set()
        right_rows = set()
        for row in marks:
            row_index = int(row.wave_row_index)
            for x_value, _y_value in row:
                if x_value < 40.0:
                    left_samples += 1
                    left_rows.add(row_index)
                elif x_value > 40.0:
                    right_samples += 1
                    right_rows.add(row_index)

        self.assertGreater(right_samples, left_samples * 3)
        self.assertEqual(left_rows, right_rows)
        self.assertGreater(len([mark for mark in marks if mark]), 0)

    def test_ordered_thresholds_vary_by_coarse_cell_and_row(self):
        first = _ordered_density_thresholds(7, 3, 96)
        repeated = _ordered_density_thresholds(7, 3, 96)
        second_row = _ordered_density_thresholds(7, 4, 96)
        self.assertEqual(first, repeated)
        self.assertNotEqual(first, second_row)
        self.assertGreater(len(set(first)), 20)
        self.assertGreaterEqual(min(first + second_row), 0.0)
        self.assertLessEqual(max(first + second_row), 1.0)
        self.assertGreater(WAVE_FIDELITY_CELL_SMOOTHING_CELLS, 0)

    def test_short_density_gaps_close_only_inside_inked_runs(self):
        visible = [True, False, True, False, False, True]
        inked = _fill_short_density_gaps(
            visible,
            [0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
        )
        self.assertEqual(inked, [True, True, True, False, False, True])
        blank_gap = _fill_short_density_gaps(
            visible,
            [0.7, 0.01, 0.7, 0.01, 0.01, 0.7],
        )
        self.assertEqual(blank_gap, visible)

    def test_fidelity_cells_do_not_emit_per_sample_dashes(self):
        size = 96
        yy, xx = np.mgrid[0:size, 0:size]
        tone = (
            0.24
            + 0.06 * np.sin(2.0 * math.pi * xx / 9.0)
            + 0.03 * np.sin(2.0 * math.pi * yy / 7.0)
        ).astype(np.float32)
        marks = screen(
            tone,
            geometry(80.0, 80.0, size),
            spacing_mm=1.265,
            pen_mm=0.9,
            period=4.0,
            period_variation=1.0,
            depth_intensity=1.5,
            angle_deg=15.0,
            style="waves_fidelity",
        )
        self.assertGreater(len(marks), 20)
        spans = [
            math.hypot(mark[-1][0] - mark[0][0], mark[-1][1] - mark[0][1])
            for mark in marks
            if len(mark) >= 2
        ]
        self.assertGreaterEqual(min(spans), 0.8 - 1e-6)
        marks_per_row = {}
        for mark in marks:
            row_index = int(mark.wave_row_index)
            marks_per_row[row_index] = marks_per_row.get(row_index, 0) + 1
        self.assertLessEqual(
            max(marks_per_row.values()),
            24,
            "coarse density cells must not degrade into per-sample dashes",
        )

    def test_rows_remain_on_candidate_pitch_and_do_not_collide(self):
        size = 72
        yy, _xx = np.mgrid[0:size, 0:size]
        tone = (0.15 + 0.75 * yy / max(size - 1, 1)).astype(np.float32)
        pitch = 1.265
        pen = 0.9
        marks = screen(
            tone,
            geometry(70.0, 70.0, size),
            spacing_mm=pitch,
            pen_mm=pen,
            period=4.0,
            period_variation=1.0,
            depth_intensity=1.5,
            angle_deg=15.0,
            style="waves_fidelity",
        )
        rows = {}
        for mark in marks:
            rows.setdefault(int(mark.wave_row_index), []).append(mark)
        indexes = sorted(rows)
        self.assertGreater(len(indexes), 20)

        first_index = indexes[0]
        theta = math.radians(15.0)
        cosine = math.cos(theta)
        sine = math.sin(theta)

        def screen_baseline(mark):
            x_value, y_value = mark.wave_baseline_mm
            return -x_value * sine + y_value * cosine

        first_baseline = np.median(
            [screen_baseline(mark) for mark in rows[first_index]]
        )
        last_index = indexes[-1]
        last_baseline = np.median(
            [screen_baseline(mark) for mark in rows[last_index]]
        )
        fitted_pitch = (last_baseline - first_baseline) / (
            last_index - first_index
        )
        self.assertAlmostEqual(abs(fitted_pitch), pitch, places=6)
        for row_index in indexes:
            for mark in rows[row_index]:
                expected = first_baseline + (
                    row_index - first_index
                ) * fitted_pitch
                self.assertAlmostEqual(
                    screen_baseline(mark),
                    expected,
                    places=6,
                )
        for first, second in zip(indexes, indexes[1:]):
            for left in rows[first]:
                for right in rows[second]:
                    self.assertTrue(
                        _polyline_pair_is_clear(
                            _polyline_segments(left),
                            _polyline_segments(right),
                            pen + WAVE_MIN_EDGE_GAP_MM,
                        )
                    )

    def test_uniform_tone_keeps_shared_phase_and_crossing_count(self):
        size = 72
        tone = np.full((size, size), 0.62, dtype=np.float32)
        marks = screen(
            tone,
            geometry(70.0, 70.0, size),
            spacing_mm=1.265,
            pen_mm=0.9,
            period=4.0,
            period_variation=0.6,
            depth_intensity=1.2,
            angle_deg=0.0,
            style="waves_fidelity",
        )
        rows = row_residual(marks)
        self.assertGreaterEqual(len(rows), 6)
        crossing_counts = []
        for _index, _along, residual in rows:
            centered = residual - float(np.mean(residual))
            signs = np.sign(centered[np.abs(centered) > 0.01])
            crossing_counts.append(
                int(np.count_nonzero(signs[1:] != signs[:-1]))
            )
        self.assertLessEqual(
            max(crossing_counts) - min(crossing_counts),
            2,
            "fidelity rows must retain one shared phase carrier",
        )

    def test_each_ink_angle_keeps_the_pitch_lattice_and_clearance(self):
        size = 64
        yy, _xx = np.mgrid[0:size, 0:size]
        tone = (0.12 + 0.82 * yy / max(size - 1, 1)).astype(np.float32)
        pitch = 1.265
        pen = 0.9
        for angle_deg in (15.0, 75.0, 0.0, 45.0):
            with self.subTest(angle_deg=angle_deg):
                marks = screen(
                    tone,
                    geometry(64.0, 64.0, size),
                    spacing_mm=pitch,
                    pen_mm=pen,
                    period=4.0,
                    period_variation=1.0,
                    depth_intensity=1.5,
                    angle_deg=angle_deg,
                    style="waves_fidelity",
                )
                rows = {}
                for mark in marks:
                    rows.setdefault(int(mark.wave_row_index), []).append(mark)
                indexes = sorted(rows)
                self.assertGreater(len(indexes), 20)
                theta = math.radians(angle_deg)
                cosine = math.cos(theta)
                sine = math.sin(theta)

                def screen_baseline(mark):
                    x_value, y_value = mark.wave_baseline_mm
                    return -x_value * sine + y_value * cosine

                first = float(
                    np.median(
                        [
                            screen_baseline(mark)
                            for mark in rows[indexes[0]]
                        ]
                    )
                )
                last = float(
                    np.median(
                        [
                            screen_baseline(mark)
                            for mark in rows[indexes[-1]]
                        ]
                    )
                )
                fitted_pitch = (last - first) / (
                    indexes[-1] - indexes[0]
                )
                self.assertAlmostEqual(
                    abs(fitted_pitch),
                    pitch,
                    places=6,
                )
                for row_index in indexes:
                    expected = first + (
                        row_index - indexes[0]
                    ) * fitted_pitch
                    for mark in rows[row_index]:
                        self.assertAlmostEqual(
                            screen_baseline(mark),
                            expected,
                            places=6,
                        )
                ordered = [rows[index][0] for index in indexes]
                for first_mark, second_mark in zip(
                    ordered,
                    ordered[1:],
                ):
                    self.assertTrue(
                        _polyline_pair_is_clear(
                            _polyline_segments(first_mark),
                            _polyline_segments(second_mark),
                            pen + WAVE_MIN_EDGE_GAP_MM,
                        )
                    )

    def test_depth_intensity_is_monotone_at_live_tight_pitch(self):
        size = 80
        yy, _xx = np.mgrid[0:size, 0:size]
        tone = (0.25 + 0.65 * yy / max(size - 1, 1)).astype(np.float32)
        geometry_value = geometry(70.0, 70.0, size)
        neutral = row_residual(
            screen(
                tone,
                geometry_value,
                spacing_mm=1.265,
                pen_mm=0.9,
                period=4.0,
                period_variation=1.0,
                depth_intensity=1.0,
                angle_deg=15.0,
                style="waves_fidelity",
            )
        )
        high = row_residual(
            screen(
                tone,
                geometry_value,
                spacing_mm=1.265,
                pen_mm=0.9,
                period=4.0,
                period_variation=1.0,
                depth_intensity=1.5,
                angle_deg=15.0,
                style="waves_fidelity",
            )
        )

        def median_rms(rows):
            return float(
                np.median(
                    [
                        np.sqrt(np.mean(residual ** 2))
                        for _index, _along, residual in rows
                    ]
                )
            )

        self.assertGreaterEqual(
            median_rms(high),
            median_rms(neutral) - 1e-9,
            "raising Depth intensity must not flatten fidelity waves",
        )

    def test_zero_depth_intensity_collapses_the_carrier(self):
        size = 48
        tone = np.full((size, size), 0.65, dtype=np.float32)
        rows = screen(
            tone,
            geometry(48.0, 48.0, size),
            spacing_mm=1.9,
            pen_mm=0.9,
            period=4.0,
            period_variation=1.0,
            depth_intensity=0.0,
            angle_deg=0.0,
            style="waves_fidelity",
        )
        self.assertTrue(rows)
        for row in rows:
            baseline_y = row.wave_baseline_mm[1]
            self.assertLess(
                max(abs(y - baseline_y) for _x, y in row),
                1e-6,
            )
