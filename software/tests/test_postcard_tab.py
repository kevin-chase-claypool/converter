"""Postcard tab: layout geometry, text, SVG, and the preview hand-off."""

import os
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.postcard_tab import PostcardTab, postcard_polylines


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


class PostcardTests(unittest.TestCase):
    def test_layout_has_border_stamp_and_address_lines(self):
        paths = postcard_polylines()
        self.assertGreater(len(paths), 5)
        self.assertEqual(len(paths[0]), 5)  # closed border

    def test_caption_and_address_add_strokes(self):
        plain = postcard_polylines(caption="", address="")
        decorated = postcard_polylines(
            caption="TO:", address="A. Person\n1 Main St"
        )
        self.assertGreater(len(decorated), len(plain))

    def test_message_adds_strokes(self):
        plain = postcard_polylines(message="")
        with_message = postcard_polylines(message="Wish you were here")
        self.assertGreater(len(with_message), len(plain))

    def test_same_input_is_deterministic(self):
        self.assertEqual(
            postcard_polylines(address="X"),
            postcard_polylines(address="X"),
        )

    def test_svg_document_is_valid_xml(self):
        root = ET.fromstring(
            polylines_to_svg(postcard_polylines(), 127.0, 177.8, 0.3)
        )
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class PostcardTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = PostcardTab(host)
        self.addCleanup(tab.deleteLater)
        tab.caption.setText("POSTCARD")
        tab.address.setPlainText("A. Person\n1 Main St")
        tab.build_svg()
        self.assertTrue(host.status)
