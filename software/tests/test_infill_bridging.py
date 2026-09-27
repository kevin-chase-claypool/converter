"""Infill should keep the pen down across passes when the connector is short.

`line_region_contours` already emits consecutive hatch rows head-to-tail, so a
dense fill can be drawn as one continuous zigzag instead of lifting the pen once
per row. The gap guards in `bridge_motion` are what keep that safe: a connector
is only drawn when it is short, so sparse parallel hatching keeps separate
passes and crosshatch still lifts between its two angle families.
"""

import math
import re
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


def _settings(**overrides):
    values = dict(
        hatch_spacing_mm=3.0,
        hatch_angle_deg=45.0,
        hatch_pattern="linear",
        shade_levels=1,
        scale=1.0,
        flip_y=False,
        tolerance=0.25,
        pen_diameter_mm=0.3,
        compensate_pen_width=False,
        raster_shading=False,
    )
    values.update(overrides)
    return converter.Settings(**values)


def _emit(svg_text, settings):
    """Return (fill passes, contours, pen cycles, bridges) for one conversion."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "case.svg"
        path.write_text(svg_text, encoding="utf-8")
        contours = converter.read_svg(str(path), settings)
        lines = converter.contours_to_gcode(contours, settings).splitlines()
    passes = [c for c in contours if len(c) == 2]
    cycles = sum(1 for line in lines if line.strip() == "M3")
    bridges = sum(1 for line in lines if "keep-down bridge" in line)
    return passes, contours, cycles, bridges


class InfillBridgingTests(unittest.TestCase):
    def test_dense_linear_fill_chains_into_a_few_pen_cycles(self):
        passes, _contours, cycles, bridges = _emit(
            FILLED_SQUARE, _settings(hatch_spacing_mm=0.3)
        )

        self.assertGreater(len(passes), 150, "the fixture should be a dense fill")
        self.assertTrue(bridges, "a solid fill should chain passes")
        self.assertLess(
            cycles,
            10,
            f"{len(passes)} passes should not cost {cycles} pen cycles",
        )

    def test_sparse_linear_fill_keeps_separate_passes(self):
        # At shading spacing the connector is over 4 mm, far more than the guard
        # allows, so nothing is drawn between passes and the output is unchanged
        # from before line families could bridge.
        passes, contours, cycles, bridges = _emit(
            FILLED_SQUARE, _settings(hatch_spacing_mm=3.0)
        )

        self.assertTrue(passes)
        self.assertEqual(bridges, 0)
        # No bridged transitions means one pen cycle per drawn contour: every
        # fill pass plus the rectangle's own outline.
        self.assertEqual(cycles, len(contours))

    def test_bridge_connector_stays_within_the_gap_guard(self):
        """A bridged move must be a short connector, never a long drag."""
        settings = _settings(hatch_spacing_mm=0.3)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "case.svg"
            path.write_text(FILLED_SQUARE, encoding="utf-8")
            contours = converter.read_svg(str(path), settings)
            lines = converter.contours_to_gcode(contours, settings).splitlines()

        max_gap = max(settings.hatch_spacing_mm * 0.85, settings.pen_diameter_mm * 6.0)
        last = None
        bridged = 0
        worst = 0.0
        for line in lines:
            match_x = re.search(r"X(-?[\d.]+)", line)
            match_y = re.search(r"Y(-?[\d.]+)", line)
            if match_x is None or match_y is None:
                continue
            point = (float(match_x.group(1)), float(match_y.group(1)))
            if "keep-down bridge" in line and last is not None:
                worst = max(worst, math.hypot(point[0] - last[0], point[1] - last[1]))
                bridged += 1
            last = point

        self.assertGreater(bridged, 0, "the dense fixture should chain some passes")
        self.assertLessEqual(
            worst,
            max_gap + 1e-6,
            f"a bridged connector of {worst:.3f} mm exceeds the {max_gap:.3f} mm guard",
        )

    def test_patterns_that_do_not_serpentine_never_bridge(self):
        _, _contours, _cycles, bridges = _emit(
            FILLED_SQUARE, _settings(hatch_pattern="dots", hatch_spacing_mm=2.0)
        )
        self.assertEqual(bridges, 0)

    def _moves(self, settings):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "case.svg"
            path.write_text(FILLED_SQUARE, encoding="utf-8")
            contours = converter.read_svg(str(path), settings)
            plan = converter.plan_program(contours, settings)
            return converter.build_preview_moves(contours, settings, None, plan)

    def test_bridge_moves_carry_bed_endpoints_for_the_preview(self):
        """A connector is drawn ink, so the preview needs real bed coordinates."""
        moves = self._moves(_settings(hatch_spacing_mm=0.3))

        bridges = [m for m in moves if m.get("strategy") == "keep_down_bridge"]
        self.assertTrue(bridges, "the dense fixture should chain passes")
        for move in bridges:
            self.assertGreater(
                converter.distance(move["bed_start"], move["bed_end"]),
                1e-9,
                "a bridge with a zero-length bed segment cannot be previewed",
            )

    def test_dense_fill_previews_as_continuous_strokes(self):
        """Draw moves must chain, lifting only where bridging was refused."""
        moves = self._moves(_settings(hatch_spacing_mm=0.3))

        lifts = 0
        breaks = 0
        previous_end = None
        for move in moves:
            if move.get("type") == "pen_up":
                lifts += 1
                previous_end = None
            elif move.get("type") == "draw":
                if previous_end is not None and converter.distance(
                    previous_end, move["start"]
                ) > 1e-9:
                    breaks += 1
                previous_end = move["end"]

        draw_moves = sum(1 for move in moves if move.get("type") == "draw")
        self.assertGreater(draw_moves, 100)
        self.assertEqual(breaks, 0, "a down-stroke must not jump between passes")
        self.assertLess(lifts, 10, f"{draw_moves} draw moves should be a few strokes")


if __name__ == "__main__":
    unittest.main()
