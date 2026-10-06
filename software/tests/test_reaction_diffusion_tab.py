"""Reaction-Diffusion tab: determinism, contours, SVG, and tab hand-off."""

import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.reaction_diffusion_tab import (
    ReactionDiffusionTab,
    reaction_diffusion_polylines,
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


def sample(**overrides):
    options = dict(grid=48, steps=400, seed=3)
    options.update(overrides)
    return reaction_diffusion_polylines(**options)


class ReactionDiffusionTests(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(sample(), sample())

    def test_contours_exist_and_stay_on_the_page(self):
        paths = sample()
        self.assertGreater(len(paths), 0)
        for line in paths:
            for x, y in line:
                self.assertGreaterEqual(x, -1e-6)
                self.assertLessEqual(x, 200.0 + 1e-6)

    def test_svg_document_is_valid_xml(self):
        root = ET.fromstring(polylines_to_svg(sample(), 200.0, 200.0, 0.3))
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class ReactionDiffusionTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = ReactionDiffusionTab(host)
        self.addCleanup(tab.deleteLater)
        tab.grid.setValue(48)
        tab.steps.setValue(300)
        tab.page_w.setValue(80)
        tab.page_h.setValue(80)
        tab.build_svg()
        self.assertTrue(host.status)
