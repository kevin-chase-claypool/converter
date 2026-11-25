"""CMYK Wave-row geometry, depth, and clearance."""

import math
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


class CmykWaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np

        cls.np = np

    def geometry(self, width=100.0, height=100.0):
        return {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": width,
            "height_mm": height,
            "pixels_w": 32,
            "pixels_h": 32,
        }

    def test_wave_rows_keep_bounded_spacing_across_row_tone_changes(self):
        spacing = 4.0
        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        page_mm = 64
        pixels_per_mm = 4
        pixel_count = page_mm * pixels_per_mm
        yy, xx = self.np.mgrid[0:pixel_count, 0:pixel_count]
        yy_mm = yy / pixels_per_mm
        xx_mm = xx / pixels_per_mm
        for angle_deg in converter.SCREEN_ANGLES_DEG.values():
            with self.subTest(angle_deg=angle_deg):
                radians = math.radians(angle_deg)
                local_normal = (
                    xx_mm * math.sin(radians) + yy_mm * math.cos(radians)
                )
                tone = (
                    0.7
                    + 0.3
                    * self.np.sin(
                        2.0 * self.np.pi * local_normal / (2.0 * spacing)
                    )
                ).astype("float32")
                waves = converter.screen_channel(
                    tone,
                    {
                        "off_x": 0.0,
                        "off_y": 0.0,
                        "width_mm": float(page_mm),
                        "height_mm": float(page_mm),
                        "pixels_w": pixel_count,
                        "pixels_h": pixel_count,
                    },
                    style="waves",
                    allow_variable_wave_spacing=True,
                    spacing_mm=spacing,
                    angle_deg=angle_deg,
                )
                local_rows = []
                for points in waves:
                    local_rows.append(
                        [
                            (
                                x * math.cos(radians) + y * math.sin(radians),
                                -x * math.sin(radians) + y * math.cos(radians),
                            )
                            for x, y in points
                        ]
                    )

                x_min = min(
                    point[0] for points in local_rows for point in points
                )
                sample_xs = [
                    x_min + spacing / 2.0 + index * 2.0 * spacing
                    for index in range(8)
                ]
                sample_x = max(
                    sample_xs,
                    key=lambda candidate: sum(
                        min(point[0] for point in row)
                        <= candidate
                        <= max(point[0] for point in row)
                        for row in local_rows
                    ),
                )
                # One quarter wavelength is where tone-driven amplitude has
                # its strongest effect on the visible gap between rows.
                ys = sorted(
                    value
                    for points in local_rows
                    if (value := value_at_x(points, sample_x)) is not None
                )
                # End rows have a one-sided tone window; guard the field.
                ys = ys[2:-2]
                gaps = [
                    second - first
                    for first, second in zip(ys, ys[1:])
                    if 0.1 <= second - first <= 2.0 * spacing
                ]
                self.assertGreaterEqual(len(gaps), 10)
                self.assertGreater(min(gaps), 0.85 * spacing)
                self.assertLess(max(gaps), 1.15 * spacing)
                self.assertLess(max(gaps) - min(gaps), 0.3 * spacing)

    def test_wave_rows_vary_depth_but_stay_bounded_on_a_vertical_gradient(self):
        spacing = 4.0
        yy, _xx = self.np.mgrid[0:64, 0:64]
        tone = (0.2 + 0.6 * yy / 63.0).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        amplitudes = []
        for points in waves:
            baseline = value_at_x(points, 0.0)
            crest = value_at_x(points, spacing / 2.0)
            if baseline is not None and crest is not None:
                amplitudes.append((baseline, crest - baseline))
        amplitudes.sort()
        self.assertGreaterEqual(len(amplitudes), 10)
        wave_amplitudes = [amplitude for _baseline, amplitude in amplitudes]
        self.assertGreater(
            max(wave_amplitudes) - min(wave_amplitudes),
            spacing * 0.12,
            "vertical tone must create visible depth",
        )
        self.assertLess(
            max(wave_amplitudes) - min(wave_amplitudes),
            spacing * 0.35,
            "depth variation must stay within the bounded row envelope",
        )

    def test_wave_rows_restore_vertical_tone_depth_without_crossing(self):
        spacing = 4.0
        yy, _xx = self.np.mgrid[0:64, 0:64]
        tone = (0.1 + 0.8 * yy / 63.0).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        amplitudes = []
        crest_y = []
        for points in waves:
            baseline = value_at_x(points, 0.0)
            crest = value_at_x(points, spacing / 2.0)
            if baseline is not None and crest is not None:
                amplitudes.append(abs(crest - baseline))
                crest_y.append(crest)

        self.assertGreaterEqual(len(amplitudes), 12)
        self.assertGreater(
            max(amplitudes) - min(amplitudes),
            spacing * 0.2,
            "vertical image tone must still create visible wave depth",
        )
        gaps = sorted(
            second - first for first, second in zip(crest_y, crest_y[1:])
        )
        self.assertGreater(min(gaps), 0.75 * spacing)
        self.assertLess(max(gaps), 1.25 * spacing)

    def test_wave_depth_can_follow_a_separate_luminance_field(self):
        spacing = 4.0
        yy, _xx = self.np.mgrid[0:64, 0:64]
        ink_mask = self.np.ones((64, 64), dtype="float32")
        depth_tone = (0.1 + 0.8 * yy / 63.0).astype("float32")
        waves = converter.screen_channel(
            ink_mask,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
            depth_tone=depth_tone,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        amplitudes = []
        for points in waves:
            baseline = value_at_x(points, 0.0)
            crest = value_at_x(points, spacing / 2.0)
            if baseline is not None and crest is not None:
                amplitudes.append(abs(crest - baseline))
        self.assertGreaterEqual(len(amplitudes), 12)
        self.assertGreater(
            max(amplitudes) - min(amplitudes),
            spacing * 0.2,
            "wave depth should follow scene luminance even where one ink "
            "channel is uniformly saturated",
        )

    def test_depth_wave_keeps_near_full_pitch_amplitude_at_full_tone(self):
        spacing = 4.0
        tone = self.np.ones((128, 128), dtype="float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 128,
                "pixels_h": 128,
            },
            style="waves_zero",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
            pen_diameter_mm=0.8,
            depth_tone=tone,
        )
        ranges = [
            max(y for _x, y in points) - min(y for _x, y in points)
            for points in waves
            if len(points) > 100
        ]
        self.assertGreater(min(ranges), spacing * 0.95)

    def test_depth_wave_shares_phase_while_amplitude_follows_tone(self):
        spacing = 4.0
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 64.0,
            "height_mm": 64.0,
            "pixels_w": 64,
            "pixels_h": 64,
        }
        tone = self.np.ones((64, 64), dtype="float32")
        yy, _xx = self.np.mgrid[0:64, 0:64]
        depth = (0.25 + 0.7 * yy / 63.0).astype("float32")
        rows = converter.screen_channel(
            tone,
            geometry,
            style="waves_zero",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
            pen_diameter_mm=0.8,
            depth_tone=depth,
        )
        rows = [points for points in rows if len(points) > 100]
        peaks = []
        ranges = []
        for points in rows:
            ys = [y for _x, y in points]
            ranges.append(max(ys) - min(ys))
            first_half = [point for point in points if point[0] <= spacing]
            peaks.append(max(first_half, key=lambda point: point[1])[0])
        self.assertLess(max(peaks) - min(peaks), 0.2)
        self.assertGreater(max(ranges), min(ranges) * 1.8)

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        ys = sorted(
            value
            for points in rows
            if (value := value_at_x(points, spacing * 0.5)) is not None
        )
        gaps = [second - first for first, second in zip(ys, ys[1:])]
        self.assertGreater(
            max(gaps) - min(gaps),
            spacing * 0.02,
            "phase-locked depth keeps crest phase, not exact row pitch",
        )

    def test_depth_wave_scales_amplitude_not_frequency_across_pitches(self):
        size = 128
        yy, _xx = self.np.mgrid[0:size, 0:size]
        tone = self.np.ones((size, size), dtype="float32")
        depth = self.np.where(
            yy < size * 0.42,
            0.12,
            0.92,
        ).astype("float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": float(size),
            "height_mm": float(size),
            "pixels_w": size,
            "pixels_h": size,
        }

        def crossings(points):
            baseline = points[0][1]
            signs = [1 if y > baseline else -1 for _x, y in points]
            return sum(
                first != second for first, second in zip(signs, signs[1:])
            )

        for spacing in (2.80, 3.36, 4.20):
            with self.subTest(spacing=spacing):
                waves = converter.screen_channel(
                    tone,
                    geometry,
                    style="waves_zero",
                    allow_variable_wave_spacing=True,
                    spacing_mm=spacing,
                    pen_diameter_mm=0.8,
                    depth_tone=depth,
                )
                rows = sorted(
                    (points for points in waves if len(points) > 100),
                    key=lambda points: sum(y for _x, y in points)
                    / len(points),
                )
                self.assertGreaterEqual(len(rows), 20)
                light_count = crossings(rows[1])
                dark_count = crossings(rows[-2])
                self.assertLessEqual(
                    abs(dark_count - light_count),
                    1,
                    "depth must change amplitude without changing row frequency",
                )
                light_range = max(y for _x, y in rows[1]) - min(
                    y for _x, y in rows[1]
                )
                dark_range = max(y for _x, y in rows[-2]) - min(
                    y for _x, y in rows[-2]
                )
                self.assertGreater(
                    dark_range,
                    light_range * 2.0,
                    "darker scene areas must retain visibly deeper waves",
                )

    def test_phase_locked_depth_clearance_scales_at_all_angles_and_pitches(
        self,
    ):
        import converter_core.cmyk as cmyk_core

        page_mm = 64.0
        pixels_per_mm = 4
        pixel_count = int(page_mm * pixels_per_mm)
        yy, xx = self.np.mgrid[0:pixel_count, 0:pixel_count]
        yy_mm = yy / pixels_per_mm
        xx_mm = xx / pixels_per_mm
        tone = self.np.ones((pixel_count, pixel_count), dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": page_mm,
            "height_mm": page_mm,
            "pixels_w": pixel_count,
            "pixels_h": pixel_count,
        }

        def value_at_x(points, x_value):
            lo, hi = 0, len(points) - 1
            while lo < hi:
                middle = (lo + hi) // 2
                if points[middle][0] < x_value:
                    lo = middle + 1
                else:
                    hi = middle
            if lo == 0:
                return points[0][1] if points[0][0] == x_value else None
            first, second = points[lo - 1], points[lo]
            if first[0] <= x_value <= second[0]:
                fraction = (x_value - first[0]) / max(
                    second[0] - first[0], 1e-9
                )
                return first[1] + fraction * (second[1] - first[1])
            return None

        minimum_clearance = 0.8 + converter.WAVE_MIN_EDGE_GAP_MM
        for spacing in (2.80, 3.36, 4.20):
            for angle_deg in converter.SCREEN_ANGLES_DEG.values():
                with self.subTest(spacing=spacing, angle_deg=angle_deg):
                    radians = math.radians(angle_deg)
                    local_normal = (
                        xx_mm * math.sin(radians)
                        + yy_mm * math.cos(radians)
                    )
                    depth = (
                        0.08
                        + 0.84
                        * (
                            0.5
                            + 0.5
                            * self.np.sin(
                                2.0
                                * self.np.pi
                                * local_normal
                                / (3.0 * spacing)
                            )
                        )
                    ).astype("float32")
                    waves = converter.screen_channel(
                        tone,
                        geometry,
                        style="waves_zero",
                        allow_variable_wave_spacing=True,
                        spacing_mm=spacing,
                        angle_deg=angle_deg,
                        pen_diameter_mm=0.8,
                        depth_tone=depth,
                    )
                    local_rows = [
                        [
                            (
                                x * math.cos(radians)
                                + y * math.sin(radians),
                                -x * math.sin(radians)
                                + y * math.cos(radians),
                            )
                            for x, y in points
                        ]
                        for points in waves
                    ]
                    local_rows.sort(
                        key=lambda points: sum(y for _x, y in points)
                        / len(points)
                    )
                    self.assertGreaterEqual(len(local_rows), 12)
                    for first, second in zip(
                        local_rows,
                        local_rows[1:],
                    ):
                        self.assertTrue(
                            cmyk_core._polyline_pair_is_clear(
                                cmyk_core._polyline_segments(first),
                                cmyk_core._polyline_segments(second),
                                minimum_clearance,
                            )
                        )

    def test_phase_locked_pitch_below_pen_envelope_fails_explicitly(self):
        tone = self.np.ones((64, 64), dtype="float32")
        with self.assertRaisesRegex(
            ValueError,
            "effective pitch is smaller than the pen width plus edge gap",
        ):
            converter.screen_channel(
                tone,
                {
                    "off_x": 0.0,
                    "off_y": 0.0,
                    "width_mm": 64.0,
                    "height_mm": 64.0,
                    "pixels_w": 64,
                    "pixels_h": 64,
                },
                style="waves_zero",
                allow_variable_wave_spacing=True,
                spacing_mm=0.8,
                pen_diameter_mm=0.8,
            )

    def test_depth_wave_keeps_row_variation_within_exact_clearance(self):
        spacing = 4.0
        yy, xx = self.np.mgrid[0:64, 0:64]
        tone = self.np.full((64, 64), 0.82, dtype="float32")
        depth = (
            0.1
            + 0.8 * yy / 63.0
            + 0.1 * self.np.sin(2.0 * self.np.pi * xx / 19.0)
        ).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_zero",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
            depth_tone=depth,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        for sample_x in (2.0, 10.0, 18.0, 26.0, 34.0, 42.0):
            with self.subTest(sample_x=sample_x):
                ys = sorted(
                    value
                    for points in waves
                    if (value := value_at_x(points, sample_x)) is not None
                )
                gaps = [
                    second - first
                    for first, second in zip(ys, ys[1:])
                    if 2.0 < second - first < 6.0
                ]
                self.assertGreaterEqual(len(gaps), 10)
                self.assertGreaterEqual(
                    min(gaps),
                    converter.WAVE_MIN_EDGE_GAP_MM
                    + 0.8
                    - 1e-6,
                )
                self.assertGreater(
                    max(gaps) - min(gaps),
                    0.05,
                    "row-specific waveform depth must survive the clearance "
                    "envelope",
                )

    def test_phase_locked_depth_preserves_untouched_rows(self):
        size = 128
        spacing = 2.8
        tone = self.np.ones((size, size), dtype="float32")
        depth = self.np.full((size, size), 0.80, dtype="float32")
        disturbed = depth.copy()
        # One short, steep tonal patch must not flatten unrelated rows across
        # the page. The old global safety scale reacted to this patch as if
        # every row contained the same maximum slope.
        disturbed[40:52, 60:64] = 0.10
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 64.0,
            "height_mm": 64.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        def vertical_ranges(depth_tone):
            waves = converter.screen_channel(
                tone,
                geometry,
                style="waves_zero",
                allow_variable_wave_spacing=True,
                spacing_mm=spacing,
                pen_diameter_mm=0.8,
                depth_tone=depth_tone,
            )
            rows = sorted(
                waves,
                key=lambda points: sum(y for _x, y in points)
                / len(points),
            )
            return [
                max(y for _x, y in points)
                - min(y for _x, y in points)
                for points in rows
            ]

        uniform_ranges = vertical_ranges(depth)
        disturbed_ranges = vertical_ranges(disturbed)
        self.assertGreaterEqual(len(uniform_ranges), 20)
        self.assertGreaterEqual(len(disturbed_ranges), 20)
        typical = sorted(uniform_ranges)[len(uniform_ranges) // 2]
        untouched = sorted(disturbed_ranges[:5])[2]
        self.assertGreater(
            untouched,
            typical * 0.9,
            "a local high-slope patch must not reduce amplitude of distant rows",
        )

    def test_phase_locked_blank_depth_changes_do_not_limit_inked_rows(self):
        size = 128
        spacing = 2.8
        ink_mask = self.np.zeros((size, size), dtype="float32")
        ink_mask[:, :64] = 1.0
        depth = self.np.full((size, size), 0.80, dtype="float32")
        changed_blank = depth.copy()
        changed_blank[:, 70:] = 0.10
        changed_blank[40:80, 90:94] = 1.0
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 64.0,
            "height_mm": 64.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        def visible_ranges(depth_tone):
            waves = converter.screen_channel(
                ink_mask,
                geometry,
                style="waves_zero",
                allow_variable_wave_spacing=True,
                spacing_mm=spacing,
                pen_diameter_mm=0.8,
                depth_tone=depth_tone,
            )
            ranges = []
            for points in waves:
                if len(points) <= 20:
                    continue
                ys = [y for _x, y in points]
                ranges.append(max(ys) - min(ys))
            return ranges

        uniform = sorted(visible_ranges(depth))
        changed = sorted(visible_ranges(changed_blank))
        self.assertGreaterEqual(len(uniform), 10)
        self.assertGreaterEqual(len(changed), 10)
        self.assertGreater(
            changed[len(changed) // 2],
            uniform[len(uniform) // 2] * 0.9,
            "depth changes over blank paper must not reduce ink-wave amplitude",
        )

    def test_phase_locked_clearance_checks_segment_distance(self):
        import converter_core.cmyk as cmyk_core

        positions = [
            [(0.0, 0.0), (1.0, 2.75), (2.0, 0.0)],
            [(0.0, 3.0), (1.0, 5.75), (2.0, 3.0)],
        ]
        self.assertFalse(
            cmyk_core._wave_clearance_ok(
                positions,
                4.0,
                minimum_clearance_mm=1.05,
            ),
            "the rows are three millimetres apart at every sampled column, "
            "but the steep segments come closer than a 1.05 mm pen envelope",
        )

    def test_clearance_does_not_impose_a_fixed_band_floor(self):
        import converter_core.cmyk as cmyk_core

        positions = [
            [(0.0, 1.0), (1.0, 1.0)],
            [(0.0, 3.4), (1.0, 3.4)],
        ]
        self.assertTrue(
            cmyk_core._wave_clearance_ok(
                positions,
                4.0,
                minimum_clearance_mm=1.05,
            ),
            "2.4 mm between rows is legal when the pen envelope is clear",
        )

    def test_phase_locked_wave_chords_stay_within_path_tolerance(self):
        spacing = 4.0
        tone = self.np.ones((64, 64), dtype="float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_zero",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
        )
        row = next(points for points in waves if len(points) > 100)
        baseline = row[0][1]
        amplitude = spacing * 0.5
        phase_rate = math.pi / spacing
        errors = []
        for first, second in zip(row, row[1:]):
            midpoint_x = (first[0] + second[0]) / 2.0
            chord_y = (first[1] + second[1]) / 2.0
            sine_y = baseline + amplitude * math.sin(
                phase_rate * midpoint_x
            )
            errors.append(abs(chord_y - sine_y))
        self.assertLess(max(errors), 0.05)

    def test_equidistant_wave_rows_keep_constant_spacing(self):
        spacing = 4.0
        yy, xx = self.np.mgrid[0:64, 0:64]
        tone = (
            0.2
            + 0.55 * xx / 63.0
            + 0.1 * self.np.sin(2.0 * self.np.pi * yy / (2.0 * spacing))
        ).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_even",
            spacing_mm=spacing,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        crest_values = []
        for sample_x in (2.0, 18.0, 34.0, 50.0):
            ys = sorted(
                value
                for points in waves
                if (value := value_at_x(points, sample_x)) is not None
            )
            gaps = [
                second - first
                for first, second in zip(ys, ys[1:])
                if abs((second - first) - spacing) < 0.1
            ]
            self.assertGreaterEqual(len(gaps), 10)
            self.assertLess(max(gaps) - min(gaps), 1e-5)
            crest_values.append((sample_x, ys))

        # The common waveform still changes size across the page even though
        # every row moves by exactly the same vertical offset.
        first_offsets = [
            value_at_x(points, 2.0) - points[0][1]
            for points in waves
            if value_at_x(points, 2.0) is not None
            and abs(points[0][0]) < 0.1
        ]
        later_offsets = [
            value_at_x(points, 18.0) - points[0][1]
            for points in waves
            if value_at_x(points, 18.0) is not None
            and abs(points[0][0]) < 0.1
        ]
        self.assertGreater(
            abs(sum(later_offsets) / len(later_offsets)
                - sum(first_offsets) / len(first_offsets)),
            0.2,
        )

    def test_dark_tone_changes_depth_without_dragging_row_baselines(self):
        spacing = 4.0
        _yy, xx = self.np.mgrid[0:64, 0:64]
        tone = self.np.where(xx < 32, 1.0, 0.15).astype("float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_even",
            spacing_mm=spacing,
            depth_tone=tone,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        # Ten and forty-two millimetres are one or more full wavelengths
        # apart. They sample dark and light tone at the same sine phase.
        dark_x = 10.0
        light_x = 42.0
        rows = sorted(waves, key=lambda points: points[0][1])
        dark_values = sorted(
            value
            for row in rows
            if (value := value_at_x(row, dark_x)) is not None
        )
        light_values = sorted(
            value
            for row in rows
            if (value := value_at_x(row, light_x)) is not None
        )
        dark_offsets = [
            value_at_x(row, dark_x) - row[0][1]
            for row in rows
        ]
        light_offsets = [
            value_at_x(row, light_x) - row[0][1]
            for row in rows
        ]

        for values in (dark_values, light_values):
            gaps = [
                second - first
                for first, second in zip(values, values[1:])
            ]
            self.assertEqual(len(gaps), 15)
            self.assertLess(max(gaps) - min(gaps), 1e-9)
            self.assertAlmostEqual(sum(gaps) / len(gaps), spacing, places=9)

        self.assertLess(max(dark_offsets) - min(dark_offsets), 1e-9)
        self.assertLess(max(light_offsets) - min(light_offsets), 1e-9)
        self.assertGreater(
            abs(sum(dark_offsets)) / len(dark_offsets),
            abs(sum(light_offsets)) / len(light_offsets) + 1.0,
            "full tone must deepen the wave without changing row baselines",
        )

    def test_phase_locked_variable_frequency_preserves_row_pitch(self):
        spacing = 4.0
        tone = self.np.ones((64, 64), dtype="float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves_even",
            spacing_mm=spacing,
            seed=7,
            wave_frequency_variation=converter.WAVE_FREQUENCY_VARIATION,
        )

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        for x_value in (8.0, 20.0, 32.0, 44.0, 56.0):
            values = sorted(
                value
                for row in waves
                if (value := value_at_x(row, x_value)) is not None
            )
            gaps = [
                second - first
                for first, second in zip(values, values[1:])
            ]
            self.assertGreaterEqual(len(gaps), 10)
            self.assertLess(max(gaps) - min(gaps), 1e-9)
            self.assertAlmostEqual(sum(gaps) / len(gaps), spacing, places=9)

        row = max(waves, key=len)
        peak_x = [
            x_value
            for index, (x_value, y_value) in enumerate(row[1:-1], start=1)
            if y_value >= row[index - 1][1]
            and y_value >= row[index + 1][1]
        ]
        peak_spacing = [
            second - first
            for first, second in zip(peak_x, peak_x[1:])
        ]
        self.assertGreaterEqual(len(peak_spacing), 4)
        self.assertGreater(
            max(peak_spacing) - min(peak_spacing),
            0.1,
            "the shared carrier must no longer repeat at one fixed frequency",
        )

    def test_equidistant_wave_rows_work_at_all_screen_angles(self):
        spacing = 4.0
        page_mm = 64.0
        pixels_per_mm = 4
        pixel_count = int(page_mm * pixels_per_mm)
        yy, xx = self.np.mgrid[0:pixel_count, 0:pixel_count]
        xx_mm = xx / pixels_per_mm
        yy_mm = yy / pixels_per_mm

        def value_at_x(points, x_value):
            ordered = sorted(points)
            for first, second in zip(ordered, ordered[1:]):
                if first[0] <= x_value <= second[0]:
                    fraction = (x_value - first[0]) / max(
                        second[0] - first[0], 1e-9
                    )
                    return first[1] + fraction * (second[1] - first[1])
            return None

        for angle_deg in converter.SCREEN_ANGLES_DEG.values():
            with self.subTest(angle_deg=angle_deg):
                radians = math.radians(angle_deg)
                local_u = xx_mm * math.cos(radians) + yy_mm * math.sin(radians)
                local_v = -xx_mm * math.sin(radians) + yy_mm * math.cos(radians)
                tone = (
                    0.35
                    + 0.25 * (local_u - local_u.min()) / self.np.ptp(local_u)
                    + 0.1
                    * self.np.sin(
                        2.0 * self.np.pi * local_v / (2.0 * spacing)
                    )
                ).astype("float32")
                waves = converter.screen_channel(
                    tone,
                    {
                        "off_x": 0.0,
                        "off_y": 0.0,
                        "width_mm": page_mm,
                        "height_mm": page_mm,
                        "pixels_w": pixel_count,
                        "pixels_h": pixel_count,
                    },
                    style="waves_even",
                    spacing_mm=spacing,
                    angle_deg=angle_deg,
                )
                local_rows = [
                    [
                        (
                            x * math.cos(radians) + y * math.sin(radians),
                            -x * math.sin(radians) + y * math.cos(radians),
                        )
                        for x, y in points
                    ]
                    for points in waves
                ]
                min_u = min(point[0] for row in local_rows for point in row)
                max_u = max(point[0] for row in local_rows for point in row)
                for fraction in (0.2, 0.4, 0.6, 0.8):
                    sample_u = min_u + fraction * (max_u - min_u)
                    ys = sorted(
                        value
                        for row in local_rows
                        if (value := value_at_x(row, sample_u)) is not None
                    )
                    gaps = [
                        second - first
                        for first, second in zip(ys, ys[1:])
                        if abs((second - first) - spacing) < 0.1
                    ]
                    self.assertGreaterEqual(len(gaps), 6)
                    self.assertLess(max(gaps) - min(gaps), 1e-5)

    def test_legacy_wave_styles_default_to_equidistant_rows(self):
        spacing = 4.0
        tone = self.np.ones((64, 64), dtype="float32")
        yy, _xx = self.np.mgrid[0:64, 0:64]
        depth = (0.2 + 0.7 * yy / 63.0).astype("float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 64.0,
            "height_mm": 64.0,
            "pixels_w": 64,
            "pixels_h": 64,
        }
        for angle_deg in converter.SCREEN_ANGLES_DEG.values():
            expected = converter.screen_channel(
                tone,
                geometry,
                style="waves_even",
                spacing_mm=spacing,
                angle_deg=angle_deg,
                depth_tone=depth,
            )
            for legacy_style in ("waves", "waves_zero"):
                with self.subTest(
                    style=legacy_style,
                    angle_deg=angle_deg,
                ):
                    actual = converter.screen_channel(
                        tone,
                        geometry,
                        style=legacy_style,
                        spacing_mm=spacing,
                        angle_deg=angle_deg,
                        depth_tone=depth,
                    )
                    self.assertEqual(actual, expected)

    def test_wave_rows_approximate_the_sinusoid_within_path_tolerance(self):
        spacing = 4.0
        tone = self.np.ones((64, 64), dtype="float32")
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=spacing,
        )

        row = next(points for points in waves if len(points) > 20)
        baseline = row[0][1]
        amplitude = spacing * 0.5
        errors = []
        for first, second in zip(row, row[1:]):
            midpoint_x = (first[0] + second[0]) / 2.0
            chord_y = (first[1] + second[1]) / 2.0
            sine_y = baseline + amplitude * math.sin(
                2.0 * math.pi * midpoint_x / (2.0 * spacing)
            )
            errors.append(abs(chord_y - sine_y))

        self.assertLess(
            max(errors),
            0.05,
            "wave chords must not turn the intended sine into visible facets",
        )

    def test_wave_rows_still_break_over_blank_image_regions(self):
        tone = self.np.ones((64, 64), dtype="float32")
        tone[:, 28:36] = 0.0
        waves = converter.screen_channel(
            tone,
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 64.0,
                "height_mm": 64.0,
                "pixels_w": 64,
                "pixels_h": 64,
            },
            style="waves",
            allow_variable_wave_spacing=True,
            spacing_mm=4.0,
        )
        self.assertGreater(len(waves), 4)
        centers = [
            (min(point[0] for point in row) + max(point[0] for point in row))
            / 2.0
            for row in waves
            if max(point[0] for point in row) - min(point[0] for point in row) > 5
        ]
        self.assertTrue(
            all(
                center < 28.0 or center > 36.0
                for center in centers
            ),
            "a blank image band must split the wave instead of drawing through it",
        )


if __name__ == "__main__":
    unittest.main()
