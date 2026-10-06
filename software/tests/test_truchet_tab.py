"""Truchet tab: determinism, tile styles, scale, SVG, and tab hand-off."""

import math
import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg, scale_polylines
from generator_tabs.truchet_tab import TruchetTab, truchet_polylines


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


def sample(**overrides):
    options = dict(width_mm=120.0, height_mm=120.0, seed=11, tile_mm=20.0)
    options.update(overrides)
    return truchet_polylines(**options)


class TruchetAlgorithmTests(unittest.TestCase):
    def test_same_seed_is_identical(self):
        self.assertEqual(sample(), sample())

    def test_styles(self):
        arcs = sample(style="arcs")
        diagonals = sample(style="diagonal")
        self.assertTrue(all(len(line) > 2 for line in arcs))
        self.assertTrue(all(len(line) == 2 for line in diagonals))

    def test_scale_helper_halves_the_extent(self):
        polylines = sample()
        scaled = scale_polylines(polylines, 0.5, 120.0, 120.0)
        centre = (60.0, 60.0)
        full = max(
            math.hypot(x - centre[0], y - centre[1])
            for line in polylines
            for x, y in line
        )
        half = max(
            math.hypot(x - centre[0], y - centre[1])
            for line in scaled
            for x, y in line
        )
        self.assertLessEqual(half, full * 0.5 + 1e-6)

    def test_svg_document_is_valid_xml(self):
        document = polylines_to_svg(sample(), 120.0, 120.0, 0.3)
        root = ET.fromstring(document)
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class TruchetTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = TruchetTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(120)
        tab.page_h.setValue(120)
        tab.tile.setValue(20.0)
        path = tab.build_svg()
        ET.parse(path)
        self.assertTrue(host.status)
