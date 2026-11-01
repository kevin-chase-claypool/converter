"""Regression tests for deterministic Wave row-order planning."""

import dataclasses
import re
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter
from generator_tabs._tab_common import scale_polylines


def row_major_contours():
    contours = []
    for y_mm in (-12.0, -4.0, 4.0, 12.0):
        contours.append(
            [(-20.0 + 2.0 * index, y_mm) for index in range(11)]
        )
        contours.append(
            [(10.0 + 2.0 * index, y_mm) for index in range(11)]
        )
    return contours


def tagged_row_contours():
    contours = row_major_contours()
    return [
        converter.WaveTrail(contour, wave_row_index=index // 2)
        for index, contour in enumerate(contours)
    ]


def rotated_flipped_row_contours(angle_deg=45.0, height_mm=100.0):
    """Return screen rows after the converter's normal SVG Y-axis flip.

    CMYK screen angles rotate the generated rows before serializing them to
    SVG. ``read_svg`` then flips Y around the document height. Keeping that
    transformation in this fixture catches a row-axis sign error that an
    unrotated test cannot see.
    """
    angle = np.deg2rad(float(angle_deg))
    cosine, sine = float(np.cos(angle)), float(np.sin(angle))

    def screen_to_svg(point):
        x_mm, y_mm = point
        return (
            x_mm * cosine - y_mm * sine,
            height_mm - (x_mm * sine + y_mm * cosine),
        )

    contours = []
    for index, contour in enumerate(row_major_contours()):
        contours.append(
            converter.WaveTrail(
                [screen_to_svg(point) for point in contour],
                wave_row_index=index // 2,
            )
        )
    return contours


class ContourOrderTests(unittest.TestCase):
    def ordered_indexes(self, order, contours=None):
        settings = converter.Settings(
            theta_mode="fixed",
            theta_center_hold_diameter_mm=0.0,
            bed_compensation_path="",
            contour_order=order,
        )
        planned = converter.planned_contours(
            row_major_contours() if contours is None else contours,
            settings,
            (0.0, 0.0),
        )
        return [item["index"] for item in planned]

    def test_default_planner_keeps_travel_optimization(self):
        self.assertNotEqual(self.ordered_indexes("optimized"), list(range(8)))

    def test_ascending_preserves_source_row_order(self):
        self.assertEqual(
            self.ordered_indexes("rows_ascending"),
            list(range(8)),
        )

    def test_descending_reverses_source_row_order(self):
        self.assertEqual(
            self.ordered_indexes("rows_descending"),
            list(reversed(range(8))),
        )

    def test_tagged_rows_sweep_in_a_serpentine_direction(self):
        self.assertEqual(
            self.ordered_indexes("rows_ascending", tagged_row_contours()),
            [0, 1, 3, 2, 4, 5, 7, 6],
        )
        self.assertEqual(
            self.ordered_indexes("rows_descending", tagged_row_contours()),
            [6, 7, 5, 4, 2, 3, 1, 0],
        )

    def test_invalid_contour_order_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "contour order"):
            converter.validate_settings(
                converter.Settings(contour_order="sideways")
            )

    def test_gcode_emits_serpentine_rows_in_the_selected_direction(self):
        contours = tagged_row_contours()
        settings = converter.Settings(
            theta_mode="fixed",
            theta_center_hold_diameter_mm=0.0,
            bed_compensation_path="",
        )
        ascending = converter.contours_to_gcode(
            contours,
            dataclasses.replace(
                settings,
                contour_order="rows_ascending",
            ),
        )
        descending = converter.contours_to_gcode(
            contours,
            dataclasses.replace(
                settings,
                contour_order="rows_descending",
            ),
        )
        pattern = re.compile(r"^\(contour (\d+)")
        self.assertEqual(
            [
                int(match.group(1))
                for line in ascending.splitlines()
                if (match := pattern.match(line))
            ],
            [1, 2, 4, 3, 5, 6, 8, 7],
        )
        self.assertEqual(
            [
                int(match.group(1))
                for line in descending.splitlines()
                if (match := pattern.match(line))
            ],
            [7, 8, 6, 5, 3, 4, 2, 1],
        )

    def test_rotated_flipped_rows_keep_their_serpentine_direction(self):
        angle = 45.0
        radians = np.deg2rad(angle)
        along = (float(np.cos(radians)), -float(np.sin(radians)))
        for order in ("rows_ascending", "rows_descending"):
            with self.subTest(order=order):
                settings = converter.Settings(
                    theta_mode="fixed",
                    theta_center_hold_diameter_mm=0.0,
                    bed_compensation_path="",
                    contour_order=order,
                    row_lock_screen_angle_deg=angle,
                )
                planned = converter.planned_contours(
                    rotated_flipped_row_contours(angle),
                    settings,
                    (0.0, 0.0),
                )
                directions = []
                for item in planned:
                    path = item["path"]
                    start = path[0][0] * along[0] + path[0][1] * along[1]
                    end = path[-1][0] * along[0] + path[-1][1] * along[1]
                    directions.append(1 if end > start else -1)

                self.assertEqual(
                    directions,
                    [1, 1, -1, -1, 1, 1, -1, -1],
                )

    def test_svg_persists_wave_row_index(self):
        document = converter.svg_document(
            {"y": tagged_row_contours()},
            50.0,
            50.0,
            0.8,
        )
        self.assertIn('data-wave-row="0"', document)
        self.assertIn('data-wave-row="3"', document)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "rows.svg"
            path.write_text(document, encoding="utf-8")
            contours = converter.read_svg(
                str(path),
                converter.Settings(),
            )
        self.assertEqual(
            [
                getattr(contour, "wave_row_index", None)
                for contour in contours
            ],
            [0, 0, 1, 1, 2, 2, 3, 3],
        )

    def test_wave_screen_marks_each_generated_row(self):
        rows = converter.screen_channel(
            np.ones((20, 20), dtype=np.float32),
            {
                "off_x": 0.0,
                "off_y": 0.0,
                "width_mm": 20.0,
                "height_mm": 20.0,
                "pixels_w": 20,
                "pixels_h": 20,
            },
            style="waves_even",
            spacing_mm=2.0,
            angle_deg=0.0,
            pen_diameter_mm=0.2,
            max_marks=1000,
            path_tolerance_mm=0.05,
            row_clearance_mm=0.4,
        )
        self.assertEqual(
            [row.wave_row_index for row in rows],
            list(range(10)),
        )

    def test_artwork_scaling_preserves_wave_row_index(self):
        scaled = scale_polylines(
            tagged_row_contours(),
            factor=2.0,
            width_mm=100.0,
            height_mm=100.0,
        )
        self.assertEqual(
            [row.wave_row_index for row in scaled],
            [0, 0, 1, 1, 2, 2, 3, 3],
        )


if __name__ == "__main__":
    unittest.main()
