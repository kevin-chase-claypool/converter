import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


class CoordinateFrameTests(unittest.TestCase):
    def test_pen_tmag_offset_is_not_a_converter_setting(self):
        settings = converter.Settings()

        self.assertFalse(hasattr(settings, "tool_offset_x_mm"))
        self.assertFalse(hasattr(settings, "tool_offset_y_mm"))
        self.assertNotIn(
            "Tool offset",
            " ".join(
                label
                for _group, items in converter.TEXT_FIELD_GROUPS
                for label, _key, _default in items
            ),
        )

    def test_xy_formatting_emits_the_calculated_point_directly(self):
        self.assertEqual(converter.format_xy_command((10.5, -2.25)), "X10.5 Y-2.25")

    def test_preview_moves_use_one_xy_position_frame(self):
        contours = [[(-10.0, 0.0), (10.0, 0.0)]]
        moves = converter.build_preview_moves(contours, converter.Settings())

        self.assertTrue(moves)
        for move in moves:
            self.assertNotIn("command_start", move)
            self.assertNotIn("command_end", move)

    def test_fill_wide_strokes_only_fills_strokes_wider_than_threshold(self):
        import xml.etree.ElementTree as ET

        def stroke_contours(width, fill_wide, ratio=2.0):
            el = ET.fromstring(
                '<path d="M0 0 L10 0" stroke="black" stroke-width="%s" fill="none"/>' % width
            )
            return converter.element_contours(
                el,
                0.25,
                expand_strokes=False,
                fill_wide_strokes=fill_wide,
                stroke_fill_ratio=ratio,
                pen_diameter=0.3,
            )

        self.assertEqual(len(stroke_contours("0.5", True)), 1)
        self.assertEqual(len(stroke_contours("2", True)), 7)
        self.assertEqual(len(stroke_contours("2", False)), 1)
        self.assertEqual(len(stroke_contours("2", True, ratio=20.0)), 1)

    def test_fill_wide_strokes_supersedes_expand_strokes_for_thin_strokes(self):
        import xml.etree.ElementTree as ET

        el = ET.fromstring(
            '<path d="M0 0 L10 0" stroke="black" stroke-width="0.5" fill="none"/>'
        )
        outlined = converter.element_contours(el, 0.25, expand_strokes=True)
        self.assertGreater(len(outlined[0]), 2)  # expand_strokes outlines the segment

        el = ET.fromstring(
            '<path d="M0 0 L10 0" stroke="black" stroke-width="0.5" fill="none"/>'
        )
        combined = converter.element_contours(
            el,
            0.25,
            expand_strokes=True,
            fill_wide_strokes=True,
            stroke_fill_ratio=2.0,
            pen_diameter=0.3,
        )
        self.assertEqual(len(combined), 1)
        self.assertEqual(len(combined[0]), 2)  # unchanged centerline, not an outline


if __name__ == "__main__":
    unittest.main()
