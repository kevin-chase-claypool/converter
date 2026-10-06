"""Line Draw tab: contours, hatch, determinism, SVG, and tab shell."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.line_draw_tab import LineDrawTab, line_draw_polylines


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


class FakeHost:
    def __init__(self):
        self.loaded = []
        self.status = []

    def use_svg(self, path, preview=False):
        self.loaded.append((path, preview))

    def generator_status(self, message):
        self.status.append(message)


class LineDrawAlgorithmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PIL import Image, ImageDraw

        folder = tempfile.mkdtemp(prefix="line-draw-test-")
        cls.image_path = str(Path(folder) / "disc.png")
        image = Image.new("L", (120, 120), 255)
        draw = ImageDraw.Draw(image)
        draw.ellipse((28, 28, 92, 92), fill=0)
        image.save(cls.image_path)

    def render(self, mode, **overrides):
        options = dict(
            mode=mode,
            width_mm=80.0,
            height_mm=80.0,
            margin_mm=4.0,
            jitter_mm=0.2,
            seed=5,
        )
        options.update(overrides)
        return line_draw_polylines(self.image_path, **options)

    def test_contours_and_hatch_both_produce_paths(self):
        contours = self.render("contour")
        hatch = self.render("hatch")
        both = self.render("both")
        self.assertGreater(len(contours), 0)
        self.assertGreater(len(hatch), 0)
        self.assertGreaterEqual(len(both), len(contours))
        self.assertGreaterEqual(len(both), len(hatch))

    def test_same_seed_is_identical(self):
        self.assertEqual(self.render("both"), self.render("both"))

    def test_svg_document_is_valid_xml(self):
        document = polylines_to_svg(self.render("both"), 80.0, 80.0, 0.3)
        root = ET.fromstring(document)
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class LineDrawTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        LineDrawAlgorithmTests.setUpClass()

    def test_tab_generates_and_hands_off_svg(self):
        host = FakeHost()
        tab = LineDrawTab(host)
        self.addCleanup(tab.deleteLater)
        tab.image_path.setText(LineDrawAlgorithmTests.image_path)
        tab.page_w.setValue(80)
        tab.page_h.setValue(80)
        tab.margin.setValue(4)
        tab.generate()
        self.assertTrue(tab._svg_path)
        ET.parse(tab._svg_path)
        tab.use_in_convert()
        self.assertEqual(len(host.loaded), 1)


if __name__ == "__main__":
    unittest.main()
