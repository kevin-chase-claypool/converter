"""3D Wireframe tab: mesh parsing, hidden-line culling, SVG, and tab shell."""

import os
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator_tabs._tab_common import polylines_to_svg
from generator_tabs.three_d_tab import (
    ThreeDTab,
    load_obj,
    load_stl,
    project_vertices,
    three_d_polylines,
)


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


CUBE_OBJ = """v -1 -1 -1
v 1 -1 -1
v 1 1 -1
v -1 1 -1
v -1 -1 1
v 1 -1 1
v 1 1 1
v -1 1 1
f 1 2 3 4
f 5 8 7 6
f 1 5 6 2
f 2 6 7 3
f 3 7 8 4
f 4 8 5 1
"""

# A flat plate with a small triangle floating behind it. Every edge of the
# small triangle projects inside the plate, so it is hidden-line culled.
OCCLUSION_OBJ = """v -2 -2 0
v 2 -2 0
v 2 2 0
v -2 2 0
v 0 0 -1
v 0.5 0 -1
v 0 0.5 -1
f 1 2 3
f 1 3 4
f 5 6 7
"""


class FakeHost:
    def __init__(self):
        self.status = []

    def generator_status(self, message):
        self.status.append(message)


def far_point(polylines, target, within=1.0):
    return any(
        abs(x - target[0]) <= within and abs(y - target[1]) <= within
        for line in polylines
        for x, y in line
    )


class ThreeDAlgorithmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = tempfile.mkdtemp(prefix="three-d-test-")
        cls.obj_path = str(Path(folder) / "cube.obj")
        Path(cls.obj_path).write_text(CUBE_OBJ, encoding="utf-8")
        cls.occlusion_path = str(Path(folder) / "occlusion.obj")
        Path(cls.occlusion_path).write_text(OCCLUSION_OBJ, encoding="utf-8")
        cls.vertices, cls.triangles = load_obj(CUBE_OBJ)

    def test_obj_parses_to_a_cube(self):
        self.assertEqual(len(self.vertices), 8)
        self.assertEqual(len(self.triangles), 12)

    def test_binary_stl_parses(self):
        triangle = ((0, 0, 0), (1, 0, 0), (0, 1, 0))
        payload = bytearray(b"\0" * 80) + struct.pack("<I", 1)
        for a, b, c in [triangle]:
            payload += struct.pack(
                "<12fH", 0.0, 0.0, 0.0, *a, *b, *c, 0
            )
        vertices, triangles = load_stl(bytes(payload))
        self.assertEqual(len(vertices), 3)
        self.assertEqual(triangles, [(0, 1, 2)])

    def test_hidden_line_culls_the_far_edge(self):
        vertices, _triangles = load_obj(OCCLUSION_OBJ)
        points, _depth = project_vertices(vertices, 0, 0, 0, 200, 200, 8)
        hidden_mid = (
            (points[4][0] + points[5][0]) / 2.0,
            (points[4][1] + points[5][1]) / 2.0,
        )
        hidden = three_d_polylines(
            self.occlusion_path, style="hidden", yaw=0, pitch=0, roll=0,
            width_mm=200, height_mm=200, margin_mm=8, sample_mm=0.5,
        )
        visible = three_d_polylines(
            self.occlusion_path, style="all", yaw=0, pitch=0, roll=0,
            width_mm=200, height_mm=200, margin_mm=8,
        )
        self.assertFalse(far_point(hidden, hidden_mid))
        self.assertTrue(far_point(visible, points[4]))
        # The plate's own silhouette stays visible.
        self.assertTrue(far_point(hidden, points[0]))

    def test_same_input_is_deterministic(self):
        first = three_d_polylines(self.obj_path, style="hidden", sample_mm=1.0)
        second = three_d_polylines(self.obj_path, style="hidden", sample_mm=1.0)
        self.assertEqual(first, second)

    def test_svg_document_is_valid_xml(self):
        polylines = three_d_polylines(self.obj_path, style="all")
        document = polylines_to_svg(polylines, 200.0, 200.0, 0.3)
        root = ET.fromstring(document)
        self.assertTrue(root.tag.endswith("svg"))


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class ThreeDTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        ThreeDAlgorithmTests.setUpClass()

    def test_tab_builds_svg_for_the_shared_preview(self):
        host = FakeHost()
        tab = ThreeDTab(host)
        self.addCleanup(tab.deleteLater)
        tab.model_path.setText(ThreeDAlgorithmTests.obj_path)
        tab.page_w.setValue(120)
        tab.page_h.setValue(120)
        tab.sample.setValue(1.0)
        path = tab.build_svg()
        self.assertTrue(path)
        ET.parse(path)
        self.assertTrue(host.status)


if __name__ == "__main__":
    unittest.main()
