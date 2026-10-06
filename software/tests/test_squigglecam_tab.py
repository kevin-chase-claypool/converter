"""SquiggleCam tab: tone response, determinism, SVG, and tab hand-off."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.squigglecam_tab import SquiggleCamTab, squigglecam_polylines


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


def _image(fill):
    from PIL import Image

    folder = tempfile.mkdtemp(prefix="squigglecam-test-")
    path = str(Path(folder) / "image.png")
    Image.new("L", (80, 80), fill).save(path)
    return path


class SquiggleCamAlgorithmTests(unittest.TestCase):
    def test_dark_tone_makes_waves(self):
        white = squigglecam_polylines(_image(255), line_count=20)
        black = squigglecam_polylines(_image(0), line_count=20)

        def spread(polylines):
            return max(
                abs(y - line[0][1])
                for line in polylines
                for _x, y in line
            )

        self.assertEqual(spread(white), 0.0)
        self.assertGreater(spread(black), 0.0)

    def test_deterministic_and_xml(self):
        first = squigglecam_polylines(_image(80), line_count=12)
        second = squigglecam_polylines(_image(80), line_count=12)
        self.assertEqual(first, second)
        root = ET.fromstring(polylines_to_svg(first, 200.0, 200.0, 0.3))
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class SquiggleCamTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost(_image(60))
        tab = SquiggleCamTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(80)
        tab.page_h.setValue(80)
        tab.line_count.setValue(12)
        tab.build_svg()
        self.assertTrue(host.status)
