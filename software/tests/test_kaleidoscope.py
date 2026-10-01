"""Kaleidoscope builder: raster tracing, wedge clipping, mirror repeats, G-code.

The kaleidoscope app reuses the plotter pipeline, so these tests cover the two
things it adds: turning an image into contours, and repeating a half-wedge
around the origin without losing the mirror symmetry.
"""

import math
import re
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


def _square_image(path, size=200, box=(40, 40, 160, 160), fill=0, background=255):
    from PIL import Image, ImageDraw

    image = Image.new("L", (size, size), background)
    ImageDraw.Draw(image).rectangle(list(box), fill=fill)
    image.save(path)
    return path


class RasterTraceTests(unittest.TestCase):
    def test_traces_a_square_into_a_closed_contour(self):
        with tempfile.TemporaryDirectory() as folder:
            path = _square_image(Path(folder) / "square.png")
            contours = converter.trace_raster(str(path), max_side=200, tolerance=0.5)

        self.assertEqual(len(contours), 1, "one dark rectangle -> one outline")
        contour = contours[0]
        xs = [x for x, _ in contour]
        ys = [y for _, y in contour]
        self.assertAlmostEqual(max(xs) - min(xs), 120.0, delta=2.0)
        self.assertAlmostEqual(max(ys) - min(ys), 120.0, delta=2.0)
        first, last = contour[0], contour[-1]
        self.assertLess(
            math.hypot(first[0] - last[0], first[1] - last[1]),
            0.01,
            "a traced region must come back as a closed loop so fill can use it",
        )

    def test_invert_traces_a_light_shape_on_dark(self):
        with tempfile.TemporaryDirectory() as folder:
            path = _square_image(
                Path(folder) / "inverted.png", fill=255, background=0
            )
            contours = converter.trace_raster(
                str(path), max_side=200, threshold=0.5, invert=True, tolerance=0.5
            )
        self.assertEqual(len(contours), 1)

    def test_blank_image_traces_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            from PIL import Image

            path = Path(folder) / "blank.png"
            Image.new("L", (64, 64), 255).save(path)
            contours = converter.trace_raster(str(path), max_side=64)
        self.assertEqual(contours, [])


class KaleidoscopeTests(unittest.TestCase):
    SQUARE = [[(10.0, 2.0), (40.0, 2.0), (40.0, 20.0), (10.0, 20.0), (10.0, 2.0)]]

    def test_mirrored_repeats_are_symmetric_about_the_x_axis(self):
        design = converter.kaleidoscope(self.SQUARE, 4, mirror=True)

        self.assertGreater(len(design), 1)
        ys = [y for contour in design for _, y in contour]
        self.assertAlmostEqual(
            min(ys) + max(ys),
            0.0,
            places=6,
            msg="a mirrored kaleidoscope must be symmetric about the wedge axis",
        )
        spans = [
            math.hypot(x, y) for contour in design for x, y in contour
        ]
        self.assertLessEqual(max(spans), 40.0 * math.sqrt(2.0) + 1e-6)

    def test_wedge_clip_drops_content_outside_the_sector(self):
        # Divisions 4 -> a 45 degree half-wedge, so anything with y > x is cut.
        pieces = converter.clip_to_wedge(self.SQUARE, 45.0)

        self.assertTrue(pieces, "the square crosses the wedge, so it must be cut")
        for piece in pieces:
            for x, y in piece:
                self.assertGreaterEqual(y, -1e-6, "the wedge starts at the x axis")
                self.assertLessEqual(y, x + 1e-6, "the wedge ends at 45 degrees")
        ys = [y for piece in pieces for _, y in piece]
        self.assertLessEqual(max(ys), 20.0 + 1e-6, "the (40, 60) corner is clipped")

    def test_designs_emit_clean_gcode(self):
        design = converter.kaleidoscope(self.SQUARE, 6, mirror=True)
        settings = converter.Settings(
            fit_mode="manual", scale=1.0, flip_y=False, hatch_spacing_mm=0.0
        )
        gcode = converter.contours_to_gcode(design, settings)

        self.assertEqual(gcode.count("\nM3"), len(design))
        self.assertNotIn("keep-down bridge", gcode)
        self.assertIn("G53 G0", gcode, "the program must still park at the end")

    def test_kaleidoscope_output_obeys_the_a_axis_guards(self):
        """This app emits through the converter's planner, so it inherits the
        A-axis guards: no segment may rotate the bed more than
        `MAX_BED_STEP_DEG`, no move may ask for more than the assumed A rate, and
        no pen-up move may carry bed rotation as a bare `G0` rapid."""
        design = converter.random_pattern(
            seed=83382, intricacy=10, radius_mm=181.0, wedge_deg=15.0
        )
        settings = converter.Settings(fit_mode="manual", scale=1.0, flip_y=False)
        gcode = converter.contours_to_gcode(design, settings)

        step_limit = converter.MAX_BED_STEP_DEG * settings.theta_drive_ratio
        rate_limit = settings.theta_controller_limits.max_rate_deg_min / 60.0
        previous = None
        worst_step = 0.0
        worst_rate = 0.0
        rapids_with_rotation = 0
        for line in gcode.splitlines():
            match = re.match(
                r"G([01]) X(-?[\d.]+) Y(-?[\d.]+)(?: A(-?[\d.]+))?(?: F([\d.]+))?", line
            )
            if not match:
                continue
            kind, x, y, a, feed = match.groups()
            point = (float(x), float(y), float(a) if a is not None else None)
            if previous is not None and point[2] is not None and previous[2] is not None:
                delta = abs(point[2] - previous[2])
                if "(travel)" not in line:
                    worst_step = max(worst_step, delta)
                if delta > 1e-9:
                    if kind == "0":
                        rapids_with_rotation += 1
                    elif feed:
                        xy = math.hypot(point[0] - previous[0], point[1] - previous[1])
                        seconds = (math.hypot(xy, delta) / float(feed)) * 60.0
                        if seconds > 0.0:
                            worst_rate = max(worst_rate, delta / seconds)
            previous = point

        self.assertLessEqual(worst_step, step_limit + 1e-6)
        self.assertLessEqual(worst_rate, rate_limit * 1.01)
        self.assertEqual(rapids_with_rotation, 0)

    def test_radius_trims_the_design_to_a_fixed_frame(self):
        # A long bar reaches 200 mm; the design must stay inside a 120 mm frame
        # however the source is later dragged around inside it.
        bar = [[(0.0, 0.0), (200.0, 0.0), (200.0, 40.0), (0.0, 40.0), (0.0, 0.0)]]
        design = converter.kaleidoscope(bar, 4, mirror=True, radius=120.0)

        self.assertTrue(design)
        radius = max(math.hypot(x, y) for contour in design for x, y in contour)
        self.assertLessEqual(radius, 120.0 + 1e-6)

    def test_closed_loop_wrapping_the_wedge_keeps_both_crossings(self):
        # The loop starts outside the wedge, so the clipper has to open it at a
        # boundary crossing; the buggy version dropped the wrap-around piece and
        # left the design empty once an image was dragged around.
        loop = [
            [
                (-30.0, -30.0),
                (30.0, -30.0),
                (30.0, 30.0),
                (-30.0, 30.0),
                (-30.0, -30.0),
            ]
        ]
        pieces = converter.clip_to_wedge(loop, 45.0)

        ys = [y for piece in pieces for _, y in piece]
        self.assertAlmostEqual(min(ys), 0.0, delta=1e-4, msg="entry crossing kept")
        self.assertAlmostEqual(max(ys), 30.0, delta=1e-4, msg="exit corner kept")


if __name__ == "__main__":
    unittest.main()
