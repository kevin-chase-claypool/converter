"""Path Prep tab: merge, deduplicate, reloop, sort, and tab hand-off."""

import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.path_prep_tab import (
    PathPrepTab,
    path_prep_polylines,
    travel_distance,
)


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


class FakeHost:
    def __init__(self, contours=()):
        self.status = []
        self.contours = list(contours)

    def generator_status(self, message):
        self.status.append(message)

    def current_contours(self):
        return self.contours


class PathPrepTests(unittest.TestCase):
    def test_collinear_points_merge(self):
        lines = [[(0.0, 0.0), (5.0, 0.0), (10.0, 0.0), (10.0, 5.0)]]
        cleaned = path_prep_polylines(
            lines, merge_angle_deg=5.0, merge_distance_mm=0.1,
            duplicate_mm=0.0, gap_mm=0.0, sort=False,
        )
        self.assertEqual(len(cleaned[0]), 3)

    def test_duplicate_segments_drop(self):
        lines = [
            [(0.0, 0.0), (10.0, 0.0)],
            [(10.0, 0.0), (0.0, 0.0)],
        ]
        cleaned = path_prep_polylines(
            lines, merge_angle_deg=0.0, merge_distance_mm=0.0,
            duplicate_mm=0.05, gap_mm=0.0, sort=False,
        )
        self.assertEqual(len(cleaned), 1)

    def test_gap_closing_joins_lines(self):
        lines = [
            [(0.0, 0.0), (10.0, 0.0)],
            [(10.1, 0.0), (20.0, 0.0)],
        ]
        cleaned = path_prep_polylines(
            lines, merge_angle_deg=0.0, merge_distance_mm=0.0,
            duplicate_mm=0.0, gap_mm=0.5, sort=False,
        )
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(len(cleaned[0]), 3)

    def test_svg_document_is_valid_xml(self):
        cleaned = path_prep_polylines([[(0.0, 0.0), (10.0, 0.0)]])
        root = ET.fromstring(polylines_to_svg(cleaned, 20.0, 20.0, 0.3))
        self.assertTrue(root.tag.endswith("svg"))

    def test_two_opt_reduces_pen_up_travel(self):
        lines = [
            [(0.0, 0.0), (1.0, 0.0)],
            [(30.0, 0.0), (31.0, 0.0)],
            [(2.0, 0.0), (3.0, 0.0)],
            [(40.0, 0.0), (41.0, 0.0)],
            [(4.0, 0.0), (5.0, 0.0)],
        ]
        plain = path_prep_polylines(
            lines, merge_angle_deg=0.0, merge_distance_mm=0.0,
            duplicate_mm=0.0, gap_mm=0.0, sort=False,
        )
        optimized = path_prep_polylines(
            lines, merge_angle_deg=0.0, merge_distance_mm=0.0,
            duplicate_mm=0.0, gap_mm=0.0, sort=False, optimize_passes=20,
        )
        self.assertLess(
            travel_distance(optimized), travel_distance(plain)
        )


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class PathPrepTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost([[(10.0, 10.0), (60.0, 10.0), (60.0, 60.0)]])
        tab = PathPrepTab(host)
        self.addCleanup(tab.deleteLater)
        tab.build_svg()
        self.assertTrue(host.status)
