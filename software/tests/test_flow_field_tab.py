"""Flow Field tab: deterministic streamlines, spacing, SVG, and tab shell."""

import math
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.flow_field_tab import FlowFieldTab, flow_field_polylines


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

    def artwork_path(self):
        return ""


def sample_field(**overrides):
    options = dict(
        width_mm=40.0,
        height_mm=40.0,
        spacing_mm=4.0,
        step_mm=1.0,
        max_steps=60,
        noise_scale_mm=16.0,
        seed=11,
        octaves=2,
        margin_mm=2.0,
    )
    options.update(overrides)
    return list(flow_field_polylines(**options))


class FlowFieldAlgorithmTests(unittest.TestCase):
    def test_same_seed_is_identical(self):
        first = sample_field()
        second = sample_field()
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first), 2)

    def test_streamlines_respect_spacing(self):
        spacing = 4.0
        polylines = sample_field(spacing_mm=spacing)
        points = [
            (index, x, y)
            for index, line in enumerate(polylines)
            for x, y in line
        ]
        self.assertGreater(len(points), 10)
        minimum = spacing * 0.6
        for position, (line_index, x, y) in enumerate(points):
            for other_line, other_x, other_y in points[position + 1:]:
                if other_line == line_index:
                    continue
                distance = math.hypot(x - other_x, y - other_y)
                self.assertGreaterEqual(distance, minimum)

    def test_svg_document_is_valid_xml(self):
        polylines = sample_field()
        document = polylines_to_svg(polylines, 40.0, 40.0, 0.3)
        root = ET.fromstring(document)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertGreater(len(root.findall(".//{http://www.w3.org/2000/svg}polyline")), 0)


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class FlowFieldTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = FlowFieldTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(60)
        tab.page_h.setValue(60)
        tab.spacing.setValue(6.0)
        tab.step.setValue(1.5)
        tab.max_steps.setValue(50)
        tab.scale.setValue(20)
        tab.margin.setValue(3)
        path = tab.build_svg()
        self.assertTrue(path)
        ET.parse(path)
        self.assertTrue(host.status)


if __name__ == "__main__":
    unittest.main()
