"""Stipple/TSP tab: density stippling, TSP ordering, SVG, and tab hand-off."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.stipple_tsp_tab import (
    StippleTspTab,
    stipple_points,
    stipple_tsp_polylines,
    tsp_order,
)


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


class FakeHost:
    def __init__(self, artwork=""):
        self.status = []
        self.artwork = artwork

    def generator_status(self, message):
        self.status.append(message)

    def artwork_path(self):
        return self.artwork


def _image():
    from PIL import Image

    folder = tempfile.mkdtemp(prefix="stipple-test-")
    path = str(Path(folder) / "image.png")
    image = Image.new("L", (64, 64), 255)
    for x in range(16, 48):
        for y in range(16, 48):
            image.putpixel((x, y), 0)
    image.save(path)
    return path


class StippleTspTests(unittest.TestCase):
    def test_stippling_is_deterministic(self):
        first = stipple_points(_image(), count=80, iterations=1, seed=3)
        second = stipple_points(_image(), count=80, iterations=1, seed=3)
        self.assertEqual(len(first), 80)
        self.assertTrue((first == second).all())

    def test_tsp_order_visits_every_point(self):
        points = [(float(index), float(index % 7)) for index in range(40)]
        order = tsp_order(points, passes=2)
        self.assertEqual(sorted(order), list(range(40)))

    def test_styles(self):
        dots = stipple_tsp_polylines(
            _image(), count=50, iterations=1, style="dots"
        )
        line = stipple_tsp_polylines(
            _image(), count=50, iterations=1, style="tsp", tsp_passes=0
        )
        self.assertEqual(len(dots), 50)
        self.assertEqual(len(line), 1)
        self.assertEqual(len(line[0]), 50)

    def test_svg_document_is_valid_xml(self):
        paths = stipple_tsp_polylines(
            _image(), count=40, iterations=1, style="dots"
        )
        root = ET.fromstring(polylines_to_svg(paths, 80.0, 80.0, 0.3))
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class StippleTspTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost(_image())
        tab = StippleTspTab(host)
        self.addCleanup(tab.deleteLater)
        tab.count.setValue(60)
        tab.iterations.setValue(1)
        tab.passes.setValue(0)
        tab.page_w.setValue(80)
        tab.page_h.setValue(80)
        tab.build_svg()
        self.assertTrue(host.status)
