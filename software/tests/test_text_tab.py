"""Text tab: Hershey parsing, layout, SVG, and the shared preview hand-off."""

import math
import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._hershey import font, text_polylines
from generator_tabs._tab_common import polylines_to_svg, scale_polylines
from generator_tabs.text_tab import TextTab


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


class FakeHost:
    def __init__(self):
        self.status = []

    def generator_status(self, message):
        self.status.append(message)


def extent(polylines):
    xs = [x for line in polylines for x, _y in line]
    ys = [y for line in polylines for _x, y in line]
    return max(xs) - min(xs), max(ys) - min(ys)


class HersheyTests(unittest.TestCase):
    def test_glyph_shapes(self):
        glyphs = font()
        self.assertEqual(len(glyphs[ord("I")]["paths"]), 1)
        self.assertEqual(len(glyphs[ord("H")]["paths"]), 3)

    def test_layout_advances_and_is_deterministic(self):
        one = text_polylines("H", 0.0, 20.0, 12.0)
        two = text_polylines("HH", 0.0, 20.0, 12.0)
        self.assertGreater(extent(two)[0], extent(one)[0] + 5.0)
        self.assertEqual(two, text_polylines("HH", 0.0, 20.0, 12.0))

    def test_lines_and_alignment(self):
        lines = text_polylines("AA\nAA", 50.0, 20.0, 10.0, align="center")
        self.assertGreater(len(lines), 4)

    def test_svg_and_scale_helper(self):
        polylines = text_polylines("PLOT", 10.0, 20.0, 10.0)
        root = ET.fromstring(polylines_to_svg(polylines, 100.0, 60.0, 0.3))
        self.assertTrue(root.tag.endswith("svg"))
        full = extent(polylines)
        half = extent(scale_polylines(polylines, 0.5, 100.0, 60.0))
        self.assertLessEqual(half[0], full[0] * 0.5 + 1e-6)


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class TextTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = TextTab(host)
        self.addCleanup(tab.deleteLater)
        tab.text.setPlainText("PLOT")
        tab.build_svg()
        self.assertTrue(host.status)
