"""CMYK SVG, ink-tag, contour, and cost-summary contracts."""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


class CmykContractTests(unittest.TestCase):
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

    def test_contours_need_a_gradient(self):
        ramp = self.np.tile(
            self.np.linspace(0.0, 1.0, 32, dtype="float32"), (32, 1)
        )
        contours = converter.screen_channel(
            ramp, self.geometry(), style="contours", spacing_mm=4.0
        )
        self.assertGreater(len(contours), 3)
        flat = self.np.full((32, 32), 0.8, dtype="float32")
        self.assertEqual(
            converter.screen_channel(
                flat, self.geometry(), style="contours", spacing_mm=4.0
            ),
            [],
        )

    def test_svg_document_groups_and_order(self):
        polyline = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
        document = converter.svg_document(
            {"c": [polyline], "k": [polyline]}, 50.0, 50.0, order=["c", "k"]
        )
        root = ET.fromstring(document)
        groups = [
            element
            for element in root.iter()
            if element.tag.split("}")[-1] == "g"
        ]
        self.assertEqual([group.get("data-ink") for group in groups], ["c", "k"])
        self.assertEqual(
            [group.get("stroke") for group in groups],
            [converter.CHANNEL_COLORS["c"], converter.CHANNEL_COLORS["k"]],
        )
        # Layer groups blend multiplicatively so external SVG viewers show
        # overprint the way the ink simulation does.
        self.assertTrue(
            all(
                "mix-blend-mode" in (group.get("style") or "")
                for group in groups
            )
        )

    def test_ink_tags_survive_the_geometry_pipeline(self):
        tagged = converter.tag_ink(
            [[(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]], "c"
        )
        moved = converter.apply_geometry_settings(tagged, converter.Settings())
        self.assertEqual(getattr(moved[0], "ink", None), "c")
        clipped = converter.clip_contours_to_bed(moved, (10.0, 0.0), 3.0)
        self.assertTrue(clipped)
        self.assertTrue(all(getattr(c, "ink", None) == "c" for c in clipped))

    def test_cost_summary_names_both_strategies(self):
        from generator_tabs.cmyk_tab import format_cost_summary, format_seconds

        rows = {
            "c": {
                "marks": 10,
                "moves": 42,
                "x_count": 30,
                "y_count": 12,
                "draw_mm": 100.0,
                "seconds": 61.0,
            }
        }
        summary = format_cost_summary(rows)
        self.assertIn("x30/y12", summary)
        self.assertIn("C ", summary)
        self.assertIn("1m01s", summary)
        self.assertEqual(format_seconds(61.0), "1m01s")
        self.assertEqual(format_seconds(3600.0), "1h00m")

    def test_cost_summary_names_xy_only(self):
        from generator_tabs.cmyk_tab import format_cost_summary

        rows = {
            "k": {
                "marks": 4,
                "moves": 9,
                "x_count": 0,
                "y_count": 0,
                "draw_mm": 12.0,
                "seconds": 5.0,
            }
        }
        summary = format_cost_summary(rows)
        self.assertIn("XY only", summary)
        self.assertIn("5s", summary)


if __name__ == "__main__":
    unittest.main()
