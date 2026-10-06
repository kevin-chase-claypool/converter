"""Vector Trace tab: outlines, hatch, invert, SVG, and tab hand-off."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.vector_trace_tab import VectorTraceTab, vector_trace_polylines


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
    from PIL import Image, ImageDraw

    folder = tempfile.mkdtemp(prefix="trace-test-")
    path = str(Path(folder) / "shape.png")
    image = Image.new("L", (80, 80), 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 60, 60), fill=0)
    image.save(path)
    return path


class VectorTraceTests(unittest.TestCase):
    def test_outline_is_closed(self):
        paths = vector_trace_polylines(
            _image(), fill="outlines", smooth_passes=1
        )
        self.assertGreaterEqual(len(paths), 1)
        self.assertEqual(paths[0][0], paths[0][-1])
        # Regression: closed loops must not collapse to two identical points.
        self.assertGreater(len(paths[0]), 4)

    def test_hatch_adds_paths(self):
        outlines = vector_trace_polylines(_image(), fill="outlines")
        both = vector_trace_polylines(_image(), fill="both")
        self.assertGreater(len(both), len(outlines))

    def test_invert_changes_the_hatch_side(self):
        # The outline of a shape is the same boundary either way; inversion
        # changes which side the hatch fill covers.
        normal = vector_trace_polylines(_image(), fill="hatch")
        inverted = vector_trace_polylines(
            _image(), fill="hatch", invert=True
        )
        self.assertNotEqual(len(normal), len(inverted))

    def test_deterministic_and_xml(self):
        first = vector_trace_polylines(_image(), fill="both")
        second = vector_trace_polylines(_image(), fill="both")
        self.assertEqual(first, second)
        root = ET.fromstring(polylines_to_svg(first, 80.0, 80.0, 0.3))
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class VectorTraceTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost(_image())
        tab = VectorTraceTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(80)
        tab.page_h.setValue(80)
        tab.build_svg()
        self.assertTrue(host.status)
