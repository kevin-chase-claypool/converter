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


if __name__ == "__main__":
    unittest.main()
