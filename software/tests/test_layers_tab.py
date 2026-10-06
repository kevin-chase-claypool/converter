"""Layers tab: colour grouping, per-layer SVG, and the Convert hand-off."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs.layers_tab import LayersTab, svg_layer_groups, write_layer_svg


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


SVG = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <path d="M0,0 L10,0" stroke="#ff0000" fill="none"/>
  <path d="M0,10 L10,10" stroke="#00ff00" fill="none"/>
  <path d="M0,20 L10,20" stroke="#00ff00" fill="none"/>
  <path d="M0,30 L10,30" stroke="#0000ff" fill="none"/>
</svg>
"""


class FakeHost:
    def __init__(self, artwork=""):
        self.status = []
        self.artwork = artwork
        self.adopted = []

    def generator_status(self, message):
        self.status.append(message)

    def artwork_path(self):
        return self.artwork

    def adopt_artwork(self, path):
        self.adopted.append(path)


class LayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = tempfile.mkdtemp(prefix="layers-test-")
        cls.path = str(Path(folder) / "art.svg")
        Path(cls.path).write_text(SVG, encoding="utf-8")

    def test_groups_by_paint(self):
        groups = dict(svg_layer_groups(self.path))
        self.assertEqual(groups["#ff0000"], [0])
        self.assertEqual(groups["#00ff00"], [1, 2])
        self.assertEqual(groups["#0000ff"], [3])

    def test_layer_svg_contains_only_its_colour(self):
        tree = ET.parse(self.path)
        layer = write_layer_svg(tree, [1, 2], "test-layer")
        text = Path(layer).read_text(encoding="utf-8")
        self.assertIn("#00ff00", text)
        self.assertNotIn("#ff0000", text)
        self.assertNotIn("#0000ff", text)
        ET.parse(layer)


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class LayersTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        LayerTests.setUpClass()

    def test_tab_lists_layers_and_adopts_one(self):
        host = FakeHost(LayerTests.path)
        tab = LayersTab(host)
        self.addCleanup(tab.deleteLater)
        tab.build_svg()
        self.assertEqual(tab.layer.count(), 4)  # all colours + three layers
        tab.layer.setCurrentIndex(1)
        tab._use_layer()
        self.assertEqual(len(host.adopted), 1)
