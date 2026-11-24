"""Screen contours should chain after the motion planner chooses their order."""

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


def _settings(**overrides):
    values = dict(
        theta_mode="fixed",
        bed_compensation_path="",
        flip_y=False,
        scale=1.0,
        tolerance=0.05,
        pen_diameter_mm=0.5,
        screen_chain_gap_mm=3.0,
    )
    values.update(overrides)
    return converter.Settings(**values)


class ScreenChainingTests(unittest.TestCase):
    def test_planner_ordered_adjacent_screen_lines_keep_the_pen_down(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(12.0, 0.0), (20.0, 0.0)]),
        ]
        settings = _settings()

        plan = converter.plan_program(contours, settings)
        gcode = converter.contours_to_gcode(contours, settings, plan)

        self.assertEqual(len(plan["contours"]), 2)
        self.assertEqual(gcode.count("\nM3\n"), 1)
        self.assertEqual(gcode.count("(keep-down bridge)"), 1)
        self.assertIn(
            "(screen chain up to 3 mm after X/Y/A planner order)",
            gcode,
        )

    def test_screen_gap_above_the_limit_still_lifts(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(14.0, 0.0), (20.0, 0.0)]),
        ]
        settings = _settings(screen_chain_gap_mm=3.0)

        gcode = converter.contours_to_gcode(contours, settings)

        self.assertEqual(gcode.count("\nM3\n"), 2)
        self.assertNotIn("(keep-down bridge)", gcode)

    def test_touching_screen_lines_need_no_connector_move(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(10.0, 0.0), (20.0, 0.0)]),
        ]

        gcode = converter.contours_to_gcode(contours, _settings())

        self.assertEqual(gcode.count("\nM3\n"), 1)
        self.assertNotIn("(keep-down bridge)", gcode)

    def test_screen_bridge_follows_the_paper_line_when_the_bed_turns(self):
        settings = _settings(tolerance=0.001)
        contours = [
            converter.ScreenTrail([(10.0, 0.0), (10.0, 2.0)]),
            converter.ScreenTrail([(10.05, 0.0), (10.05, 2.0)]),
        ]
        plan = {
            "center": (0.0, 0.0),
            "bed_compensation": None,
            "planned_jobs": [
                (
                    {"index": 0, "reversed": False},
                    contours[0],
                    [0.0, 0.0],
                    ["fixed"],
                ),
                (
                    {"index": 1, "reversed": False},
                    contours[1],
                    [10.0, 10.0],
                    ["fixed"],
                ),
            ],
        }

        gcode = converter.contours_to_gcode(
            contours,
            settings,
            program_plan=plan,
        )

        self.assertEqual(gcode.count("\nM3\n"), 1)
        self.assertGreater(gcode.count("(keep-down bridge)"), 1)

    def test_screen_bridging_keeps_the_cost_optimized_planner_order(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(30.0, 0.0), (40.0, 0.0)]),
            converter.ScreenTrail([(12.0, 4.0), (20.0, 4.0)]),
            converter.ScreenTrail([(40.0, 4.0), (48.0, 4.0)]),
        ]

        planned_without = converter.plan_program(
            contours,
            _settings(screen_chain_gap_mm=0.0),
        )
        planned_with = converter.plan_program(
            contours,
            _settings(screen_chain_gap_mm=3.0),
        )

        def signature(plan):
            return [
                (
                    planned["index"],
                    planned["reversed"],
                    tuple(points),
                )
                for planned, points, _thetas, _strategies
                in plan["planned_jobs"]
            ]

        self.assertEqual(signature(planned_with), signature(planned_without))

    def test_screen_bridge_is_rejected_when_lifting_is_cheaper(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(12.0, 0.0), (20.0, 0.0)]),
        ]
        settings = _settings(
            feed_rate=1.0,
            travel_rate=3000.0,
            pen_up_ms=0.0,
            pen_down_ms=0.0,
        )

        gcode = converter.contours_to_gcode(contours, settings)

        self.assertEqual(gcode.count("\nM3\n"), 2)
        self.assertNotIn("(keep-down bridge)", gcode)

    def test_regular_artwork_strokes_are_not_globally_chainable(self):
        contours = [
            [(0.0, 0.0), (10.0, 0.0)],
            [(12.0, 0.0), (20.0, 0.0)],
        ]
        settings = _settings()

        gcode = converter.contours_to_gcode(contours, settings)

        self.assertEqual(gcode.count("\nM3\n"), 2)
        self.assertNotIn("(keep-down bridge)", gcode)

    def test_screen_chain_tag_survives_svg_round_trip(self):
        document = converter.svg_document(
            {
                "c": [
                    converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
                ]
            },
            40.0,
            40.0,
            order=["c"],
        )
        self.assertIn('data-screen-chain="1"', document)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "screen.svg"
            path.write_text(document, encoding="utf-8")
            contours = converter.read_svg(str(path), _settings())

        self.assertEqual(len(contours), 1)
        self.assertIsInstance(contours[0], converter.ScreenTrail)

    def test_ink_preview_tag_preserves_screen_chain_eligibility(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(12.0, 0.0), (20.0, 0.0)]),
        ]

        tagged = converter.tag_ink(contours, "y")

        self.assertIsInstance(tagged[0], converter.ScreenTrail)
        self.assertEqual(tagged[0].ink, "y")
        moves = converter.build_preview_moves(tagged, _settings())
        self.assertEqual(
            sum(move.get("strategy") == "keep_down_bridge" for move in moves),
            1,
        )

    def test_preview_marks_the_screen_connector_as_drawn_ink(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(12.0, 0.0), (20.0, 0.0)]),
        ]
        settings = _settings()

        moves = converter.build_preview_moves(contours, settings)

        bridges = [
            move
            for move in moves
            if move.get("strategy") == "keep_down_bridge"
        ]
        self.assertEqual(len(bridges), 1)
        self.assertEqual(bridges[0]["type"], "draw")
        self.assertAlmostEqual(
            converter.distance(
                bridges[0]["bed_start"],
                bridges[0]["bed_end"],
            ),
            2.0,
        )

    def test_screen_chain_reduces_the_previewed_pen_cycle_time(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(12.0, 0.0), (20.0, 0.0)]),
        ]
        unchained = converter.build_preview_moves(
            contours,
            _settings(screen_chain_gap_mm=0.0),
        )
        chained = converter.build_preview_moves(
            contours,
            _settings(screen_chain_gap_mm=3.0),
        )

        self.assertEqual(
            sum(move["type"] == "pen_up" for move in chained),
            sum(move["type"] == "pen_up" for move in unchained) - 1,
        )
        self.assertLess(
            sum(float(move["duration_ms"]) for move in chained),
            sum(float(move["duration_ms"]) for move in unchained),
        )

    def test_screen_bridge_preview_matches_the_emitted_gcode(self):
        contours = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
            converter.ScreenTrail([(12.0, 0.0), (20.0, 0.0)]),
        ]
        settings = _settings()
        moves = converter.build_preview_moves(contours, settings)
        gcode = converter.contours_to_gcode(contours, settings)

        bridge_lines = [
            move["gcode"]
            for move in moves
            if move.get("strategy") == "keep_down_bridge"
        ]
        self.assertTrue(bridge_lines)
        for line in bridge_lines:
            self.assertIn(line, gcode)

    def test_negative_screen_chain_gap_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "screen chain gap"):
            converter.validate_settings(
                converter.Settings(screen_chain_gap_mm=-0.1)
            )


if __name__ == "__main__":
    unittest.main()
