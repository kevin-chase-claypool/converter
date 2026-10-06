"""Wobble tab: deviation, endpoint flags, determinism, and tab hand-off."""

import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.wobble_tab import WobbleTab, wobble_polylines


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


STRAIGHT = [[(0.0, 0.0), (100.0, 0.0)]]


class WobbleAlgorithmTests(unittest.TestCase):
    def test_wobble_adds_points_and_stays_within_amplitude(self):
        wobbled = wobble_polylines(
            STRAIGHT,
            frequency_mm=5.0,
            amplitude_mm=1.0,
            jitter_pct=20.0,
            wobble_end_amplitude=False,
            wobble_end_position=False,
        )
        self.assertEqual(len(wobbled), 1)
        self.assertGreater(len(wobbled[0]), 2)
        self.assertTrue(
            all(abs(y) <= 1.0 + 1e-9 for _x, y in wobbled[0])
        )
        self.assertEqual(wobbled[0][0], (0.0, 0.0))
        self.assertEqual(wobbled[0][-1], (100.0, 0.0))

    def test_deterministic(self):
        first = wobble_polylines(STRAIGHT, seed=3)
        second = wobble_polylines(STRAIGHT, seed=3)
        self.assertEqual(first, second)

    def test_svg_document_is_valid_xml(self):
        wobbled = wobble_polylines(STRAIGHT)
        root = ET.fromstring(polylines_to_svg(wobbled, 120.0, 20.0, 0.3))
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class WobbleTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost(STRAIGHT)
        tab = WobbleTab(host)
        self.addCleanup(tab.deleteLater)
        tab.build_svg()
        self.assertTrue(host.status)
