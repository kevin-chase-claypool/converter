"""Pixel Art tab: big/line/snake modes, determinism, SVG, and tab hand-off."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.pixel_art_tab import PixelArtTab, pixel_art_polylines


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


def _pixel_image():
    from PIL import Image

    folder = tempfile.mkdtemp(prefix="pixel-art-test-")
    path = str(Path(folder) / "pixels.png")
    image = Image.new("RGBA", (3, 2), (255, 255, 255, 255))
    image.putpixel((0, 0), (0, 0, 0, 255))
    image.putpixel((1, 0), (0, 0, 0, 255))
    image.save(path)
    return path


class PixelArtAlgorithmTests(unittest.TestCase):
    def test_big_mode_has_one_spiral_per_pixel(self):
        paths = pixel_art_polylines(_pixel_image(), mode="big", max_pixels=16)
        self.assertEqual(len(paths), 2)
        self.assertTrue(all(len(path) == 10 for path in paths))

    def test_line_mode_merges_runs_with_overdraw(self):
        paths = pixel_art_polylines(
            _pixel_image(),
            mode="line",
            max_pixels=16,
            overdraw=0.1,
            pitch_mm=1.0,
        )
        self.assertEqual(len(paths), 1)
        (start, end) = paths[0]
        # The two-pixel run is drawn 1 px long with 0.1 px of overdraw at
        # each end; the whole path is centred on the page afterwards.
        self.assertGreater(end[0] - start[0], 1.0)

    def test_snake_mode_connects_neighbours(self):
        paths = pixel_art_polylines(_pixel_image(), mode="snake", max_pixels=16)
        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0]), 2)

    def test_deterministic_and_xml(self):
        first = pixel_art_polylines(_pixel_image(), mode="snake", max_pixels=16)
        second = pixel_art_polylines(_pixel_image(), mode="snake", max_pixels=16)
        self.assertEqual(first, second)
        root = ET.fromstring(polylines_to_svg(first, 50.0, 50.0, 0.3))
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class PixelArtTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost(_pixel_image())
        tab = PixelArtTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(60)
        tab.page_h.setValue(60)
        tab.build_svg()
        self.assertTrue(host.status)
