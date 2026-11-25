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
            0.85,
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


if __name__ == "__main__":
    unittest.main()
