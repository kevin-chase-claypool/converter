"""Edge-flow structure, tone, and streamline behavior."""

import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


class CmykEdgeFlowTests(unittest.TestCase):
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

    def test_structure_diagnostic_is_undirected_and_confidence_weighted(self):
        size = 64
        coords = self.np.arange(size, dtype="float32")
        xx, _yy = self.np.meshgrid(coords, coords)
        guide = xx / float(size - 1)
        reversed_guide = guide[:, ::-1]
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        forward = converter.structure_field_diagnostic(
            guide,
            geometry,
            2.0,
        )
        reversed_direction = converter.structure_field_diagnostic(
            reversed_guide,
            geometry,
            2.0,
        )
        self.assertEqual(forward.shape, (size, size, 3))
        self.assertTrue(self.np.array_equal(forward, reversed_direction))

        flat = converter.structure_field_diagnostic(
            self.np.full((size, size), 0.5, dtype="float32"),
            geometry,
            2.0,
        )
        self.assertLess(float(flat.mean()), float(forward.mean()))

    def test_process_color_area_screen_is_deterministic_and_pen_bounded(self):
        size = 96
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        depth = 0.15 + 0.75 * (xx + yy) / float(2 * (size - 1))
        tones = {
            "c": depth * 0.25,
            "m": depth * 0.75,
            "y": depth * 0.60,
            "k": 1.0 - depth,
            "depth": depth,
            "flow_guide": depth,
        }
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 40.0,
            "height_mm": 40.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        first = converter.screen_process_color_area_cmyk(
            tones,
            geometry,
            spacing_mm=1.0,
            pen_diameter_mm=0.9,
            max_marks=5000,
            seed=7,
        )
        second = converter.screen_process_color_area_cmyk(
            tones,
            geometry,
            spacing_mm=1.0,
            pen_diameter_mm=0.9,
            max_marks=5000,
            seed=7,
        )
        self.assertEqual(
            {
                channel: [
                    [tuple(point) for point in line]
                    for line in lines
                ]
                for channel, lines in first.items()
            },
            {
                channel: [
                    [tuple(point) for point in line]
                    for line in lines
                ]
                for channel, lines in second.items()
            },
        )
        self.assertGreater(sum(len(lines) for lines in first.values()), 0)
        self.assertGreater(len(first["k"]), 0)
        for lines in first.values():
            for line in lines:
                self.assertEqual(len(line), 3)
                for x, y in line:
                    self.assertGreaterEqual(x, 0.0)
                    self.assertLessEqual(x, 40.0)
                    self.assertGreaterEqual(y, 0.0)
                    self.assertLessEqual(y, 40.0)
                length = sum(
                    math.hypot(
                        end[0] - start[0],
                        end[1] - start[1],
                    )
                    for start, end in zip(line, line[1:])
                )
                self.assertLessEqual(length, 1.30)

    def test_process_color_area_screen_keeps_tilted_edge_marks_on_page(self):
        size = 64
        field = self.np.full((size, size), 0.5, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 40.0,
            "height_mm": 40.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        for channel in converter.CHANNELS:
            tones = {
                name: (
                    field
                    if name == channel
                    else self.np.zeros_like(field)
                )
                for name in converter.CHANNELS
            }
            tones["depth"] = self.np.ones_like(field)
            tones["flow_guide"] = self.np.ones_like(field)
            marks = converter.screen_process_color_area_cmyk(
                tones,
                geometry,
                spacing_mm=1.0,
                pen_diameter_mm=0.9,
                edge_keylines=False,
                max_marks=5000,
                seed=7,
                overdraw=3,
            )
            self.assertGreater(len(marks[channel]), 0)
            for line in marks[channel]:
                self.assertEqual(len(line), 3)
                for x, y in line:
                    self.assertGreaterEqual(x, 0.0)
                    self.assertLessEqual(x, 40.0)
                    self.assertGreaterEqual(y, 0.0)
                    self.assertLessEqual(y, 40.0)

    def test_process_color_area_screen_preserves_light_coverage(self):
        size = 64
        levels = (0.15, 0.35, 0.55, 0.25)
        tones = {
            channel: self.np.full(
                (size, size),
                level,
                dtype="float32",
            )
            for channel, level in zip(converter.CHANNELS, levels)
        }
        tones["depth"] = self.np.ones((size, size), dtype="float32")
        tones["flow_guide"] = tones["depth"]
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 40.0,
            "height_mm": 40.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        marks = converter.screen_process_color_area_cmyk(
            tones,
            geometry,
            spacing_mm=1.0,
            pen_diameter_mm=0.9,
            edge_keylines=False,
            max_marks=5000,
            seed=7,
        )
        cell_count = 40 * 40
        for channel, level in zip(converter.CHANNELS, levels):
            self.assertAlmostEqual(
                len(marks[channel]) / cell_count,
                level,
                delta=0.02,
            )

    def test_process_color_area_diffusion_matches_calibrated_mix(self):
        from converter_core import cmyk as cmyk_core

        size = 80
        levels = (0.5, 0.5, 0.5, 0.0)
        coverage = self.np.broadcast_to(
            self.np.asarray(levels, dtype="float64"),
            (size, size, len(converter.CHANNELS)),
        )
        masks = cmyk_core._coverage_masks(coverage, seed=7)
        factors = converter.ink_transmittance_matrix()
        actual = self.np.ones((size, size, 3), dtype="float64")
        for index, factor in enumerate(factors):
            actual *= self.np.where(
                masks[..., index, None],
                factor,
                1.0,
            )
        target = converter.predict_cmyk_rgb(
            {
                channel: self.np.full((size, size), level)
                for channel, level in zip(converter.CHANNELS, levels)
            }
        )
        mean_error = self.np.abs(
            actual.mean(axis=(0, 1))
            - target.mean(axis=(0, 1))
        )
        self.assertLess(float(mean_error.max()), 0.02)

    def test_process_color_area_auto_uses_plate_coverage_directly(self):
        from converter_core import cmyk as cmyk_core

        shape = (24, 24)
        tones = {
            channel: self.np.full(
                shape,
                0.1 + index * 0.2,
                dtype="float32",
            )
            for index, channel in enumerate(converter.CHANNELS)
        }
        coverage = cmyk_core._auto_screen_coverage(
            tones,
            "process_area",
            pen_width_mm=0.9,
            effective_pitch_mm=0.91,
        )
        for channel in converter.CHANNELS:
            self.np.testing.assert_array_equal(
                coverage[channel],
                tones[channel],
            )

    def test_process_color_area_keylines_add_black_on_strong_edge(self):
        size = 96
        guide = self.np.zeros((size, size), dtype="float32")
        guide[:, size // 2 :] = 1.0
        empty = self.np.zeros_like(guide)
        tones = {
            channel: empty.copy()
            for channel in converter.CHANNELS
        }
        tones["depth"] = empty.copy()
        tones["flow_guide"] = guide
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 40.0,
            "height_mm": 40.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        without = converter.screen_process_color_area_cmyk(
            tones,
            geometry,
            spacing_mm=1.0,
            pen_diameter_mm=0.9,
            edge_keylines=False,
            keyline_smoothing_mm=0.6,
            max_marks=5000,
            seed=7,
        )
        with_keyline = converter.screen_process_color_area_cmyk(
            tones,
            geometry,
            spacing_mm=1.0,
            pen_diameter_mm=0.9,
            edge_keylines=True,
            edge_threshold=0.5,
            keyline_smoothing_mm=0.6,
            max_marks=5000,
            seed=7,
        )
        self.assertFalse(any(without.values()))
        self.assertGreater(len(with_keyline["k"]), 0)
        self.assertFalse(any(with_keyline[channel] for channel in "cmy"))

    def test_process_color_area_screen_grows_pitch_to_respect_mark_cap(self):
        size = 64
        field = self.np.full((size, size), 0.75, dtype="float32")
        tones = {
            channel: field
            for channel in converter.CHANNELS
        }
        tones["depth"] = self.np.ones((size, size), dtype="float32")
        tones["flow_guide"] = tones["depth"]
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 40.0,
            "height_mm": 40.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        marks = converter.screen_process_color_area_cmyk(
            tones,
            geometry,
            spacing_mm=0.25,
            pen_diameter_mm=0.1,
            edge_keylines=False,
            max_marks=100,
            seed=7,
        )
        self.assertGreater(sum(len(lines) for lines in marks.values()), 0)
        for lines in marks.values():
            self.assertLessEqual(len(lines), 100)

    def test_process_color_area_preserves_broad_bright_highlights(self):
        size = 96
        field = self.np.full((size, size), 0.55, dtype="float32")
        field[42:55, 42:55] = 0.12
        tones = {
            channel: field.copy()
            for channel in converter.CHANNELS
        }
        depth = self.np.full((size, size), 0.60, dtype="float32")
        depth[42:55, 42:55] = 0.05
        tones["depth"] = depth
        tones["flow_guide"] = tuple(
            tones[channel] for channel in converter.CHANNELS
        ) + (tones["depth"],)
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 40.0,
            "height_mm": 40.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        common = {
            "spacing_mm": 1.0,
            "pen_diameter_mm": 0.9,
            "edge_keylines": False,
            "max_marks": 5000,
            "seed": 7,
            "detail_alignment": 0.0,
        }
        unprotected = converter.screen_process_color_area_cmyk(
            tones,
            geometry,
            protect_highlights=False,
            **common,
        )
        protected = converter.screen_process_color_area_cmyk(
            tones,
            geometry,
            protect_highlights=True,
            highlight_detail=0.16,
            highlight_fraction=0.40,
            **common,
        )

        def center_marks(marks):
            return sum(
                1
                for lines in marks.values()
                for line in lines
                if 18.0 <= line[len(line) // 2][0] <= 22.0
                and 18.0 <= line[len(line) // 2][1] <= 22.0
            )

        self.assertGreater(center_marks(unprotected), 0)
        self.assertLess(
            center_marks(protected),
            center_marks(unprotected),
        )

    def test_process_color_detail_alignment_moves_toward_local_ink(self):
        from converter_core import cmyk as cmyk_core

        tone = self.np.zeros((8, 8), dtype="float32")
        tone[:, 6:] = 1.0
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 8.0,
            "height_mm": 8.0,
            "pixels_w": 8,
            "pixels_h": 8,
        }
        offset_x, offset_y = cmyk_core._tone_centroid_offset(
            tone,
            geometry,
            4.0,
            4.0,
            8.0,
            8.0,
        )
        self.assertGreater(offset_x, 1.0)
        self.assertAlmostEqual(offset_y, 0.0, places=6)

    def test_coherent_screen_forwards_exposed_flow_controls(self):
        from converter_core import cmyk as cmyk_core

        field = self.np.full((16, 16), 0.5, dtype="float32")
        tones = {
            channel: field
            for channel in (*converter.CHANNELS, "depth", "flow_guide")
        }
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": 16,
            "pixels_h": 16,
        }
        with mock.patch.object(
            cmyk_core,
            "trace_shared_structure_streamlines",
            return_value={},
        ) as trace:
            cmyk_core.screen_coherent_color_flow(
                tones,
                geometry,
                spacing_mm=4.0,
                pen_diameter_mm=0.8,
                path_tolerance_mm=0.1,
                flow_layers=3,
                keylines=True,
                color_quiet=0.35,
                color_hold_mm=9.5,
                color_mix_ratio=0.81,
                bridge_mm=7.5,
                dark_layer_start=0.55,
                dark_layer_end=0.97,
            )
        kwargs = trace.call_args.kwargs
        self.assertAlmostEqual(kwargs["color_hold_mm"], 9.5)
        self.assertAlmostEqual(kwargs["color_mix_ratio"], 0.81)
        self.assertAlmostEqual(kwargs["bridge_mm"], 7.5)
        self.assertAlmostEqual(kwargs["dark_layer_start"], 0.55)
        self.assertAlmostEqual(kwargs["dark_layer_end"], 0.97)

    def test_edge_flow_streamlines_follow_structure_orientation(self):
        size = 80
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        guide = (xx + yy) / float(2 * (size - 1))
        tone = self.np.full((size, size), 0.85, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        marks = converter.screen_channel(
            tone,
            geometry,
            style="edge_flow",
            spacing_mm=8.0,
            angle_deg=0.0,
            max_marks=200,
            flow_smoothing_mm=4.0,
            flow_layers=1,
            depth_tone=guide,
        )

        long_segments = []
        for line in marks:
            for first, second in zip(line, line[1:]):
                dx = second[0] - first[0]
                dy = second[1] - first[1]
                length = math.hypot(dx, dy)
                if length >= 0.5:
                    # The guide gradient is (1, 1), so edge-directed paths
                    # should run along the perpendicular (-1, 1).
                    alignment = abs(dy - dx) / (math.sqrt(2.0) * length)
                    long_segments.append(alignment)
        self.assertGreater(len(long_segments), 20)
        self.assertGreater(
            sum(long_segments) / len(long_segments),
            0.85,
        )

    def test_edge_flow_keeps_color_only_detail(self):
        size = 96
        tone = self.np.full((size, size), 0.9, dtype="float32")
        # These colours have equal luminance but a strong chromatic boundary.
        color_guide = self.np.zeros((size, size, 3), dtype="float32")
        color_guide[:, : size // 2] = (1.0, 0.0, 0.0)
        color_guide[:, size // 2 :] = (0.0, 0.509, 0.0)
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        marks = converter.screen_channel(
            tone,
            geometry,
            style="edge_flow",
            spacing_mm=8.0,
            angle_deg=0.0,
            max_marks=200,
            flow_smoothing_mm=1.0,
            flow_layers=1,
            flow_guide=color_guide,
        )

        vertical_segments = []
        for line in marks:
            for first, second in zip(line, line[1:]):
                dx = second[0] - first[0]
                dy = second[1] - first[1]
                length = math.hypot(dx, dy)
                midpoint_x = 0.5 * (first[0] + second[0])
                if length >= 0.5 and abs(midpoint_x - 50.0) <= 6.0:
                    vertical_segments.append(abs(dy) / length)
        self.assertGreater(len(vertical_segments), 5)
        self.assertGreater(
            sum(vertical_segments) / len(vertical_segments),
            0.75,
        )

    def test_edge_flow_black_keylines_strengthen_coherent_edges(self):
        size = 96
        guide = self.np.zeros((size, size), dtype="float32")
        guide[:, size // 2 :] = 1.0
        tone = self.np.full((size, size), 0.08, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        common = {
            "style": "edge_flow",
            "spacing_mm": 8.0,
            "angle_deg": 0.0,
            "seed": 7,
            "max_marks": 500,
            "flow_smoothing_mm": 1.0,
            "flow_layers": 1,
            "depth_tone": guide,
            "flow_guide": guide,
        }

        tone_gated = converter.screen_channel(tone, geometry, **common)
        keylined = converter.screen_channel(
            tone,
            geometry,
            flow_keylines=True,
            **common,
        )

        def ink_length(marks):
            return sum(
                math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                for line in marks
                for first, second in zip(line, line[1:])
            )

        # The low-tone screen alone leaves a broken vertical edge. Continuous
        # keylines retain more of that path without changing where it runs.
        self.assertGreater(ink_length(keylined), ink_length(tone_gated) * 1.4)

    def test_edge_flow_color_quiet_reduces_coverage_at_keylines(self):
        size = 96
        guide = self.np.zeros((size, size), dtype="float32")
        guide[:, size // 2 :] = 1.0
        tone = self.np.full((size, size), 0.30, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        common = {
            "style": "edge_flow",
            "spacing_mm": 8.0,
            "angle_deg": 0.0,
            "seed": 7,
            "max_marks": 500,
            "flow_smoothing_mm": 1.0,
            "flow_layers": 2,
            "depth_tone": guide,
            "flow_guide": guide,
        }

        normal = converter.screen_channel(tone, geometry, **common)
        quieted = converter.screen_channel(
            tone,
            geometry,
            flow_color_quiet=0.65,
            **common,
        )

        def ink_length(marks):
            return sum(
                math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                for line in marks
                for first, second in zip(line, line[1:])
            )

        self.assertLess(ink_length(quieted), ink_length(normal) * 0.95)

    def test_edge_flow_can_limit_each_mark_to_a_short_local_stroke(self):
        size = 96
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        guide = (xx + yy) / float(2 * (size - 1))
        tone = self.np.full((size, size), 0.9, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        marks = converter.screen_channel(
            tone,
            geometry,
            style="edge_flow",
            spacing_mm=8.0,
            angle_deg=0.0,
            seed=7,
            max_marks=500,
            flow_smoothing_mm=2.0,
            flow_layers=1,
            flow_guide=guide,
            flow_max_path_mm=4.0,
        )

        longest = max(
            sum(
                math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                for first, second in zip(line, line[1:])
            )
            for line in marks
        )
        self.assertLessEqual(longest, 4.6)

    def test_shared_edge_flow_plates_share_one_geometry_network(self):
        from converter_core import structure_tensor

        size = 96
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        guide = (xx + yy) / float(2 * (size - 1))
        coverage = self.np.full((size, size), 0.9, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        calls = []

        def capture_gating(points, *args):
            calls.append((tuple(points), int(args[-1])))
            return [[points[0], points[-1]]]

        with mock.patch.object(
            structure_tensor,
            "_tone_gated_runs",
            side_effect=capture_gating,
        ):
            converter.screen_cmyk_edge_flow(
                {
                    "c": coverage,
                    "m": coverage,
                    "y": coverage,
                    "k": coverage,
                    "depth": guide,
                },
                geometry,
                spacing_mm=8.0,
                pen_diameter_mm=1.0,
                path_tolerance_mm=0.2,
                flow_smoothing_mm=4.0,
                flow_layers=1,
                max_marks=240,
                seed=7,
                flow_guide=guide,
            )

        self.assertGreaterEqual(len(calls), len(converter.CHANNELS))
        for start in range(0, len(calls), len(converter.CHANNELS)):
            group = calls[start : start + len(converter.CHANNELS)]
            self.assertEqual(len(group), len(converter.CHANNELS))
            self.assertEqual(
                {salt for _points, salt in group},
                set(range(1, len(converter.CHANNELS) + 1)),
            )
            self.assertTrue(
                all(points == group[0][0] for points, _salt in group[1:])
            )

    def test_shared_edge_flow_does_not_render_as_a_black_mass(self):
        from PIL import Image, ImageDraw

        size = 48
        image = self.np.ones((size, size, 3), dtype="float32")
        image[:] = (0.11, 0.18, 0.10)
        image[4:44, 11:37] = (0.92, 0.70, 0.54)
        tones = converter.rgb_to_cmyk_tone(
            image,
            gcr=1.0,
            gamma=0.70,
        )
        luminance = image @ self.np.array(
            [0.299, 0.587, 0.114],
            dtype="float32",
        )
        tones["depth"] = 1.0 - luminance
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 80.0,
            "height_mm": 80.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        marks = converter.screen_cmyk_edge_flow(
            tones,
            geometry,
            spacing_mm=1.2,
            pen_diameter_mm=0.6,
            path_tolerance_mm=0.12,
            flow_smoothing_mm=2.0,
            flow_layers=3,
            max_marks=200000,
            seed=7,
            keylines=True,
            color_quiet=0.25,
            tone_segment_mm=2.0,
            max_path_mm=12.0,
            bridge_mm=1.5,
            flow_guide=tones["depth"],
        )

        pixels_per_mm = 4
        pixels = 80 * pixels_per_mm
        pen_pixels = 2
        masks = []
        for channel in converter.CHANNELS:
            mask = Image.new("L", (pixels, pixels), 0)
            draw = ImageDraw.Draw(mask)
            for line in marks[channel]:
                points = [
                    (
                        int(round(x * pixels_per_mm)),
                        int(round(y * pixels_per_mm)),
                    )
                    for x, y in line
                ]
                if len(points) >= 2:
                    draw.line(
                        points,
                        fill=255,
                        width=pen_pixels,
                        joint="curve",
                    )
            masks.append(
                self.np.asarray(mask, dtype="float32") / 255.0
            )

        stack = self.np.stack(masks, axis=-1)
        union = stack.max(axis=-1) > 0.0
        self.assertGreater(int(union.sum()), 100)
        rendered = self.np.ones((pixels, pixels, 3), dtype="float32")
        for index, factor in enumerate(
            converter.ink_transmittance_matrix()
        ):
            rendered *= 1.0 - stack[..., index : index + 1] * (
                1.0 - factor
            )
        rendered_luminance = rendered @ self.np.array(
            [0.299, 0.587, 0.114],
            dtype="float32",
        )

        all_four_over_union = float(
            (stack.min(axis=-1) > 0.0).sum() / union.sum()
        )
        black_over_union = float(
            (stack[..., 3] > 0.0).sum() / union.sum()
        )
        dark_over_union = float(
            (rendered_luminance[union] < 0.20).mean()
        )
        self.assertLessEqual(
            sum(len(marks[channel]) for channel in converter.CHANNELS),
            700,
        )
        self.assertLess(all_four_over_union, 0.08)
        self.assertLess(black_over_union, 0.75)
        self.assertLess(dark_over_union, 0.70)
        self.assertGreater(
            float(rendered_luminance[union].mean()),
            0.20,
        )

    def test_edge_flow_mark_cap_does_not_coarsen_a_dense_fine_pitch(self):
        size = 800
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 200.0,
            "height_mm": 200.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        guide = self.np.ones((size, size), dtype="float32")
        coverage = self.np.zeros((size, size), dtype="float32")
        coverage[300:500, 300:500] = 0.9

        marks = converter.screen_channel(
            coverage,
            geometry,
            style="edge_flow",
            spacing_mm=0.31,
            angle_deg=0.0,
            seed=7,
            max_marks=200000,
            pen_diameter_mm=0.3,
            path_tolerance_mm=0.15,
            depth_tone=guide,
            flow_guide=guide,
            flow_smoothing_mm=2.0,
            flow_layers=3,
        )

        self.assertGreater(len(marks), 180)

    def test_edge_flow_plate_angle_controls_flat_field_direction(self):
        size = 96
        tone = self.np.full((size, size), 0.8, dtype="float32")
        guide = self.np.full((size, size), 0.5, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        common = {
            "style": "edge_flow",
            "spacing_mm": 8.0,
            "seed": 7,
            "max_marks": 240,
            "flow_smoothing_mm": 2.0,
            "flow_layers": 1,
            "depth_tone": guide,
            "flow_guide": guide,
        }

        horizontal = converter.screen_channel(
            tone, geometry, angle_deg=0.0, **common
        )
        vertical = converter.screen_channel(
            tone, geometry, angle_deg=90.0, **common
        )

        def vertical_fraction(marks):
            ratios = []
            for line in marks:
                for first, second in zip(line, line[1:]):
                    dx = second[0] - first[0]
                    dy = second[1] - first[1]
                    length = math.hypot(dx, dy)
                    if length > 0.0:
                        ratios.append(abs(dy) / length)
            return sum(ratios) / len(ratios)

        self.assertLess(vertical_fraction(horizontal), 0.25)
        self.assertGreater(vertical_fraction(vertical), 0.75)

    def test_edge_flow_uses_fixed_angle_without_structure(self):
        tone = self.np.full((40, 40), 0.8, dtype="float32")
        guide = self.np.full((40, 40), 0.5, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": 40,
            "pixels_h": 40,
        }

        marks = converter.screen_channel(
            tone,
            geometry,
            style="edge_flow",
            spacing_mm=9.0,
            angle_deg=30.0,
            max_marks=120,
            flow_smoothing_mm=3.0,
            flow_layers=1,
            depth_tone=guide,
        )

        alignments = []
        expected_x = math.cos(math.radians(30.0))
        expected_y = math.sin(math.radians(30.0))
        for line in marks:
            for first, second in zip(line, line[1:]):
                dx = second[0] - first[0]
                dy = second[1] - first[1]
                length = math.hypot(dx, dy)
                if length >= 0.5:
                    alignments.append(
                        abs(dx * expected_x + dy * expected_y) / length
                    )
        self.assertGreater(len(alignments), 20)
        self.assertGreater(
            sum(alignments) / len(alignments),
            0.98,
        )

    def test_edge_flow_weak_tonal_gradient_keeps_screen_direction(self):
        size = 80
        tone = self.np.full((size, size), 0.8, dtype="float32")
        weak_x = self.np.linspace(
            0.5,
            0.5005,
            size,
            dtype="float32",
        )
        guide = self.np.tile(weak_x, (size, 1))
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        marks = converter.screen_channel(
            tone,
            geometry,
            style="edge_flow",
            spacing_mm=8.0,
            angle_deg=0.0,
            max_marks=200,
            flow_smoothing_mm=1.0,
            flow_layers=1,
            flow_guide=guide,
        )

        vertical_fraction = []
        for line in marks:
            for first, second in zip(line, line[1:]):
                dx = second[0] - first[0]
                dy = second[1] - first[1]
                length = math.hypot(dx, dy)
                if length > 0.0:
                    vertical_fraction.append(abs(dy) / length)
        self.assertGreater(len(vertical_fraction), 20)
        self.assertLess(
            sum(vertical_fraction) / len(vertical_fraction),
            0.25,
        )

    def test_edge_flow_moderate_gradient_steers_the_shared_form(self):
        size = 80
        tone = self.np.full((size, size), 0.8, dtype="float32")
        guide_x = self.np.linspace(
            0.34,
            0.66,
            size,
            dtype="float32",
        )
        guide = self.np.tile(guide_x, (size, 1))
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        marks = converter.screen_channel(
            tone,
            geometry,
            style="edge_flow",
            spacing_mm=8.0,
            angle_deg=0.0,
            max_marks=200,
            flow_smoothing_mm=2.0,
            flow_layers=1,
            flow_guide=guide,
        )

        vertical_fraction = []
        for line in marks:
            for first, second in zip(line, line[1:]):
                dx = second[0] - first[0]
                dy = second[1] - first[1]
                length = math.hypot(dx, dy)
                if length > 0.0:
                    vertical_fraction.append(abs(dy) / length)
        self.assertGreater(len(vertical_fraction), 20)
        self.assertGreater(
            sum(vertical_fraction) / len(vertical_fraction),
            0.75,
        )

    def test_edge_flow_pitch_compresses_continuously_in_dark_tone(self):
        from converter_core import structure_tensor

        base_pitch = 2.0
        pitches = [
            structure_tensor._edge_flow_local_pitch(
                base_pitch,
                tone,
                pen_diameter_mm=0.5,
                compression=0.8,
            )
            for tone in (0.0, 0.25, 0.5, 0.75, 1.0)
        ]
        self.assertEqual(pitches[0], base_pitch)
        self.assertTrue(
            all(first > second for first, second in zip(pitches, pitches[1:]))
        )
        self.assertGreaterEqual(pitches[-1], 0.45)

        size = 160
        tone = self.np.full((size, size), 0.9, dtype="float32")
        guide = self.np.full((size, size), 0.5, dtype="float32")
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        common = {
            "style": "edge_flow",
            "spacing_mm": 5.0,
            "seed": 7,
            "max_marks": 2000,
            "pen_diameter_mm": 0.5,
            "path_tolerance_mm": 0.1,
            "flow_smoothing_mm": 2.0,
            "flow_layers": 1,
            "flow_guide": guide,
        }
        fixed = converter.screen_channel(tone, geometry, **common)
        compressed = converter.screen_channel(
            tone,
            geometry,
            flow_pitch_compression=0.7,
            **common,
        )

        def ink_length(marks):
            return sum(
                math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                for line in marks
                for first, second in zip(line, line[1:])
            )

        self.assertGreater(ink_length(compressed), ink_length(fixed) * 1.25)

    def test_edge_flow_adds_layers_to_darker_ink(self):
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": 40,
            "pixels_h": 40,
        }
        guide = self.np.full((40, 40), 0.5, dtype="float32")

        def total_length(tone_value):
            tone = self.np.full((40, 40), tone_value, dtype="float32")
            marks = converter.screen_channel(
                tone,
                geometry,
                style="edge_flow",
                spacing_mm=9.0,
                angle_deg=0.0,
                max_marks=160,
                flow_smoothing_mm=3.0,
                flow_layers=3,
                depth_tone=guide,
            )
            return sum(
                math.hypot(b[0] - a[0], b[1] - a[1])
                for line in marks
                for a, b in zip(line, line[1:])
            )

        light_length = total_length(0.34)
        dark_length = total_length(0.95)
        self.assertGreater(light_length, 0.0)
        self.assertGreater(dark_length, light_length * 1.35)

    def test_edge_flow_tone_ramp_has_no_broad_density_plateaus(self):
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": 80,
            "pixels_h": 80,
        }
        guide = self.np.full((80, 80), 0.5, dtype="float32")

        def total_length(tone_value):
            tone = self.np.full((80, 80), tone_value, dtype="float32")
            marks = converter.screen_channel(
                tone,
                geometry,
                style="edge_flow",
                spacing_mm=4.0,
                angle_deg=0.0,
                seed=7,
                max_marks=2000,
                flow_smoothing_mm=2.0,
                flow_layers=3,
                flow_guide=guide,
            )
            return sum(
                math.hypot(b[0] - a[0], b[1] - a[1])
                for line in marks
                for a, b in zip(line, line[1:])
            )

        lengths = [
            total_length(value)
            for value in (0.12, 0.18, 0.24, 0.32, 0.42, 0.55)
        ]
        self.assertTrue(
            all(first < second for first, second in zip(lengths, lengths[1:]))
        )
        self.assertGreater(lengths[-1], lengths[0] * 3.0)

    def test_edge_flow_tone_breaks_are_path_local_not_a_2d_grid(self):
        from converter_core import structure_tensor

        distances = [index * 0.25 for index in range(96)]
        first = [
            structure_tensor._path_tone_threshold(
                distance,
                1001,
                4.0,
                0,
            )
            for distance in distances
        ]
        second = [
            structure_tensor._path_tone_threshold(
                distance,
                2002,
                4.0,
                0,
            )
            for distance in distances
        ]
        self.assertGreater(len(set(first)), 4)
        self.assertNotEqual(first, second)

    def test_coherent_color_flow_keeps_long_ink_runs(self):
        size = 160
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        guide = (xx + yy) / float(2 * (size - 1))
        tones = {
            "c": self.np.zeros((size, size), dtype="float32"),
            "m": self.np.zeros((size, size), dtype="float32"),
            "y": self.np.full((size, size), 0.82, dtype="float32"),
            "k": self.np.zeros((size, size), dtype="float32"),
            "depth": self.np.full((size, size), 0.5, dtype="float32"),
        }
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        marks = converter.screen_coherent_color_flow(
            tones,
            geometry,
            spacing_mm=8.0,
            pen_diameter_mm=1.0,
            path_tolerance_mm=0.15,
            flow_smoothing_mm=3.0,
            flow_layers=1,
            max_marks=2000,
            seed=7,
            flow_guide=guide,
        )

        lengths = [
            sum(
                math.hypot(second[0] - first[0], second[1] - first[1])
                for first, second in zip(line, line[1:])
            )
            for line in marks["y"]
        ]
        self.assertTrue(lengths)
        self.assertGreater(max(lengths), 55.0)
        self.assertGreater(
            sum(length for length in lengths if length >= 20.0),
            sum(lengths) * 0.70,
        )
        self.assertEqual(marks["c"], [])
        self.assertEqual(marks["m"], [])
        self.assertEqual(marks["k"], [])

    def test_coherent_color_flow_assigns_local_ink_planes(self):
        size = 128
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        guide = yy / float(size - 1)
        tones = {
            "c": self.np.zeros((size, size), dtype="float32"),
            "m": self.np.zeros((size, size), dtype="float32"),
            "y": self.np.zeros((size, size), dtype="float32"),
            "k": self.np.zeros((size, size), dtype="float32"),
            "depth": self.np.full((size, size), 0.5, dtype="float32"),
        }
        tones["y"][:, : size // 2] = 0.82
        tones["m"][:, size // 2 :] = 0.82
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        marks = converter.screen_coherent_color_flow(
            tones,
            geometry,
            spacing_mm=6.0,
            pen_diameter_mm=1.0,
            path_tolerance_mm=0.12,
            flow_smoothing_mm=1.0,
            flow_layers=1,
            max_marks=2000,
            seed=11,
            flow_guide=guide,
        )

        def ink_length(lines):
            return sum(
                math.hypot(second[0] - first[0], second[1] - first[1])
                for line in lines
                for first, second in zip(line, line[1:])
            )

        self.assertGreater(ink_length(marks["y"]), 80.0)
        self.assertGreater(ink_length(marks["m"]), 80.0)
        self.assertEqual(ink_length(marks["c"]), 0.0)
        self.assertEqual(ink_length(marks["k"]), 0.0)

    def test_coherent_color_flow_uses_layer_fallback_angles(self):
        size = 112
        guide = self.np.full((size, size), 0.5, dtype="float32")
        tones = {
            "c": self.np.zeros((size, size), dtype="float32"),
            "m": self.np.zeros((size, size), dtype="float32"),
            "y": self.np.full((size, size), 0.82, dtype="float32"),
            "k": self.np.zeros((size, size), dtype="float32"),
            "depth": self.np.full((size, size), 0.5, dtype="float32"),
        }
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        marks = converter.screen_coherent_color_flow(
            tones,
            geometry,
            spacing_mm=8.0,
            pen_diameter_mm=1.0,
            path_tolerance_mm=0.12,
            flow_smoothing_mm=2.0,
            flow_layers=2,
            max_marks=2000,
            seed=7,
            fallback_angles_deg=[0.0, 90.0],
            flow_guide=guide,
        )

        horizontal = 0
        vertical = 0
        for line in marks["y"]:
            for first, second in zip(line, line[1:]):
                dx = abs(second[0] - first[0])
                dy = abs(second[1] - first[1])
                if dx > 0.5 and dy < dx * 0.1:
                    horizontal += 1
                elif dy > 0.5 and dx < dy * 0.1:
                    vertical += 1
        self.assertGreater(horizontal, 20)
        self.assertGreater(vertical, 20)

    def test_coherent_color_flow_gates_extra_layers_by_scene_depth(self):
        size = 128
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        guide = (xx + yy) / float(2 * (size - 1))
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        def ink_length(depth):
            tones = {
                "c": self.np.zeros((size, size), dtype="float32"),
                "m": self.np.zeros((size, size), dtype="float32"),
                "y": self.np.full((size, size), 0.82, dtype="float32"),
                "k": self.np.zeros((size, size), dtype="float32"),
                "depth": self.np.full(
                    (size, size),
                    depth,
                    dtype="float32",
                ),
            }
            common = {
                "spacing_mm": 6.0,
                "pen_diameter_mm": 0.8,
                "path_tolerance_mm": 0.12,
                "flow_smoothing_mm": 2.0,
                "max_marks": 3000,
                "seed": 7,
                "flow_guide": guide,
            }
            one_layer = converter.screen_coherent_color_flow(
                tones,
                geometry,
                flow_layers=1,
                **common,
            )
            three_layers = converter.screen_coherent_color_flow(
                tones,
                geometry,
                flow_layers=3,
                **common,
            )

            def length(marks):
                return sum(
                    math.hypot(second[0] - first[0], second[1] - first[1])
                    for line in marks["y"]
                    for first, second in zip(line, line[1:])
                )

            return length(one_layer), length(three_layers)

        bright_one, bright_three = ink_length(0.12)
        mid_one, mid_three = ink_length(0.36)
        dark_one, dark_three = ink_length(0.88)
        self.assertAlmostEqual(bright_three, bright_one, delta=bright_one * 0.02)
        self.assertAlmostEqual(mid_three, mid_one, delta=mid_one * 0.02)
        self.assertGreater(dark_three, dark_one * 1.40)

    def test_coherent_shade_compression_follows_scene_depth(self):
        size = 128
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        guide = (xx + yy) / float(2 * (size - 1))
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }

        def ink_length(depth, compression):
            tones = {
                "c": self.np.zeros((size, size), dtype="float32"),
                "m": self.np.zeros((size, size), dtype="float32"),
                "y": self.np.full((size, size), 0.82, dtype="float32"),
                "k": self.np.zeros((size, size), dtype="float32"),
                "depth": self.np.full(
                    (size, size),
                    depth,
                    dtype="float32",
                ),
            }
            marks = converter.screen_coherent_color_flow(
                tones,
                geometry,
                spacing_mm=6.0,
                pen_diameter_mm=0.8,
                path_tolerance_mm=0.12,
                flow_smoothing_mm=2.0,
                flow_layers=1,
                flow_pitch_compression=compression,
                max_marks=3000,
                seed=7,
                flow_guide=guide,
            )
            return sum(
                math.hypot(second[0] - first[0], second[1] - first[1])
                for line in marks["y"]
                for first, second in zip(line, line[1:])
            )

        bright_fixed = ink_length(0.12, 0.0)
        bright_compressed = ink_length(0.12, 0.8)
        dark_fixed = ink_length(0.88, 0.0)
        dark_compressed = ink_length(0.88, 0.8)
        self.assertLess(bright_compressed, bright_fixed * 1.12)
        self.assertGreater(dark_compressed, dark_fixed * 1.30)

    def test_coherent_color_flow_black_keylines_stay_on_structure(self):
        size = 128
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        guide = self.np.zeros((size, size), dtype="float32")
        guide[:, size // 2 :] = 1.0
        tones = {
            "c": self.np.zeros((size, size), dtype="float32"),
            "m": self.np.zeros((size, size), dtype="float32"),
            "y": self.np.full((size, size), 0.55, dtype="float32"),
            "k": self.np.full((size, size), 0.05, dtype="float32"),
            "depth": self.np.full((size, size), 0.5, dtype="float32"),
        }
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 100.0,
            "height_mm": 100.0,
            "pixels_w": size,
            "pixels_h": size,
        }
        common = {
            "spacing_mm": 7.0,
            "pen_diameter_mm": 1.0,
            "path_tolerance_mm": 0.12,
            "flow_smoothing_mm": 1.0,
            "flow_layers": 1,
            "max_marks": 1000,
            "seed": 7,
            "flow_guide": guide,
        }

        normal = converter.screen_coherent_color_flow(
            tones,
            geometry,
            **common,
        )
        keylined = converter.screen_coherent_color_flow(
            tones,
            geometry,
            keylines=True,
            color_quiet=0.25,
            **common,
        )

        def ink_length(lines):
            return sum(
                math.hypot(second[0] - first[0], second[1] - first[1])
                for line in lines
                for first, second in zip(line, line[1:])
            )

        self.assertGreater(
            ink_length(keylined["k"]),
            max(30.0, ink_length(normal["k"]) * 2.0),
        )
        self.assertGreater(
            ink_length(keylined["y"]),
            ink_length(normal["y"]) * 0.45,
        )

    def test_edge_preserving_simplify_keeps_the_strong_boundary(self):
        from converter_core import structure_tensor

        size = 96
        coords = self.np.arange(size, dtype="float32")
        xx, yy = self.np.meshgrid(coords, coords)
        image = self.np.full((size, size, 3), 0.55, dtype="float32")
        checker = ((xx.astype(int) + yy.astype(int)) % 2) * 0.08
        image += checker[..., None]
        image[:, size // 2 :] = self.np.clip(
            image[:, size // 2 :] + 0.32,
            0.0,
            1.0,
        )

        simplified = structure_tensor.edge_preserving_simplify(
            image,
            radius_mm=4.0,
            mm_per_px=1.0,
            epsilon=0.01,
        )

        interior = slice(8, 36)
        left_texture_before = float(image[interior, interior, 0].std())
        left_texture_after = float(simplified[interior, interior, 0].std())
        edge_before = float(
            image[:, size // 2 - 2 : size // 2 + 2, 0].mean()
            - image[:, size // 2 - 6 : size // 2 - 2, 0].mean()
        )
        edge_after = float(
            simplified[:, size // 2 - 2 : size // 2 + 2, 0].mean()
            - simplified[:, size // 2 - 6 : size // 2 - 2, 0].mean()
        )

        self.assertLess(left_texture_after, left_texture_before * 0.55)
        self.assertGreater(edge_after, edge_before * 0.80)


if __name__ == "__main__":
    unittest.main()
