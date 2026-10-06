"""Substitution tab: grid growth, styles, SVG, and the preview hand-off."""

import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.substitution_tab import (
    SubstitutionTab,
    substitution_grid,
    substitution_polylines,
)


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


class SubstitutionTests(unittest.TestCase):
    def test_grid_doubles_each_iteration(self):
        grid = substitution_grid(seed=3, palette=3, iterations=3)
        self.assertEqual(len(grid), 16)
        self.assertTrue(all(len(row) == 16 for row in grid))

    def test_same_seed_is_identical(self):
        self.assertEqual(
            substitution_grid(seed=5, palette=4, iterations=2),
            substitution_grid(seed=5, palette=4, iterations=2),
        )

    def test_styles(self):
        outlines = substitution_polylines(
            seed=4, palette=3, iterations=2, style="outlines"
        )
        diagonals = substitution_polylines(
            seed=4, palette=3, iterations=2, style="diagonals"
        )
        self.assertGreater(len(outlines), 1)
        self.assertEqual(len(diagonals), 64)  # 8 x 8 cells

    def test_svg_document_is_valid_xml(self):
        document = polylines_to_svg(
            substitution_polylines(seed=1, iterations=2), 120.0, 120.0, 0.3
        )
        root = ET.fromstring(document)
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class SubstitutionTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = SubstitutionTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(120)
        tab.page_h.setValue(120)
        tab.iterations.setValue(3)
        tab.build_svg()
        self.assertTrue(host.status)
