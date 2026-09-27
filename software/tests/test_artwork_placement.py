"""The artwork can be placed off the bed center, the way a slicer moves a part.

`plan_program` centers the artwork's bounding box on the registered bed center by
default. `artwork_offset_x_mm` and `artwork_offset_y_mm` move it, which is how a
drawing whose bounding box is not its visual center gets positioned by hand.
"""

import math
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


FILLED_SQUARE = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 60 60">'
    '<rect x="10" y="10" width="40" height="40" fill="black"/></svg>'
)


def _plan(offset_x=0.0, offset_y=0.0):
    settings = converter.Settings(
        artwork_offset_x_mm=offset_x,
        artwork_offset_y_mm=offset_y,
        hatch_spacing_mm=3.0,
        hatch_pattern="linear",
        scale=1.0,
        flip_y=False,
        tolerance=0.25,
        compensate_pen_width=False,
    )
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "case.svg"
        path.write_text(FILLED_SQUARE, encoding="utf-8")
        contours = converter.read_svg(str(path), settings)
    return converter.plan_program(contours, settings)


def _center(plan):
    points = [point for contour in plan["contours"] for point in contour]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)


class ArtworkPlacementTests(unittest.TestCase):
    def test_default_placement_centers_the_artwork_on_the_bed(self):
        cx, cy = _center(_plan())
        self.assertAlmostEqual(cx, 0.0, places=6)
        self.assertAlmostEqual(cy, 0.0, places=6)

    def test_offset_moves_the_artwork_by_exactly_that_amount(self):
        cx, cy = _center(_plan(10.0, -5.0))
        self.assertAlmostEqual(cx, 10.0, places=6)
        self.assertAlmostEqual(cy, -5.0, places=6)

    def test_offset_only_translates(self):
        base = _plan()
        moved = _plan(12.5, -3.25)
        self.assertEqual(len(base["contours"]), len(moved["contours"]))

        base_points = sorted(
            tuple(round(value, 6) for value in point)
            for contour in base["contours"]
            for point in contour
        )
        expected = sorted(
            (round(x + 12.5, 6), round(y - 3.25, 6)) for x, y in base_points
        )
        actual = sorted(
            tuple(round(value, 6) for value in point)
            for contour in moved["contours"]
            for point in contour
        )
        self.assertEqual(actual, expected)

    def test_negative_offsets_are_valid(self):
        settings = converter.Settings(artwork_offset_x_mm=-25.0, artwork_offset_y_mm=-10.0)
        self.assertEqual(converter.validate_settings(settings).artwork_offset_x_mm, -25.0)

    def test_non_finite_offset_is_rejected(self):
        with self.assertRaises(ValueError):
            converter.validate_settings(converter.Settings(artwork_offset_x_mm=math.nan))
        with self.assertRaises(ValueError):
            converter.validate_settings(converter.Settings(artwork_offset_y_mm=math.inf))


if __name__ == "__main__":
    unittest.main()
