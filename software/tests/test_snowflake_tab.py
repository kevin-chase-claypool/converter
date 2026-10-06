"""Snowflake tab: determinism, scale, SVG, and the shared preview hand-off."""

import math
import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.snowflake_tab import SnowflakeTab, snowflake_polylines


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
    options = dict(width_mm=120.0, height_mm=120.0, seed=3, arms=6, depth=2)
    options.update(overrides)
    return snowflake_polylines(**options)


def extent(polylines, width_mm=120.0, height_mm=120.0):
    centre_x, centre_y = width_mm / 2.0, height_mm / 2.0
    return max(
        math.hypot(x - centre_x, y - centre_y)
        for line in polylines
        for x, y in line
    )


class SnowflakeAlgorithmTests(unittest.TestCase):
    def test_same_seed_is_identical(self):
        self.assertEqual(sample(), sample())

    def test_branch_count_and_scale(self):
        segments = sample()
        self.assertEqual(len(segments), 6 * (2 ** 3 - 1))
        full = extent(segments)
        half = extent(sample(scale_pct=50))
        self.assertLessEqual(half, full * 0.5 + 1e-6)

    def test_svg_document_is_valid_xml(self):
        document = polylines_to_svg(sample(), 120.0, 120.0, 0.3)
        root = ET.fromstring(document)
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class SnowflakeTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = SnowflakeTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(120)
        tab.page_h.setValue(120)
        path = tab.build_svg()
        ET.parse(path)
        self.assertTrue(host.status)
