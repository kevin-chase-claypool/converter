"""Voronoi tab: cell count, determinism, SVG, and the preview hand-off."""

import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.voronoi_tab import VoronoiTab, voronoi_polylines


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


class VoronoiTests(unittest.TestCase):
    def test_sites_style_draws_one_marker_per_point(self):
        paths = voronoi_polylines(count=25, seed=3, style="sites")
        self.assertEqual(len(paths), 25)

    def test_cell_style_is_deterministic(self):
        first = voronoi_polylines(count=40, seed=5, style="cells")
        second = voronoi_polylines(count=40, seed=5, style="cells")
        self.assertEqual(first, second)
        self.assertGreater(len(first), 10)

    def test_relaxation_keeps_cells_inside_the_page(self):
        paths = voronoi_polylines(count=20, seed=1, relax=2, style="cells")
        for line in paths:
            for x, y in line:
                self.assertGreaterEqual(x, -1e-6)
                self.assertLessEqual(x, 200.0 + 1e-6)

    def test_svg_document_is_valid_xml(self):
        root = ET.fromstring(
            polylines_to_svg(
                voronoi_polylines(count=15, style="cells"), 200.0, 200.0, 0.3
            )
        )
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class VoronoiTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = VoronoiTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(80)
        tab.page_h.setValue(80)
        tab.count.setValue(20)
        tab.build_svg()
        self.assertTrue(host.status)
