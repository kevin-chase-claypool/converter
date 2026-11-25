"""Guided CMYK photo workflow and its print-order handoff."""

import math
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter
from generator_tabs.cmyk_tab import CmykPhotoTab


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover
    HAVE_QT = False


class FakeHost:
    def __init__(self, artwork):
        self._artwork = artwork
        self.status = []
        self.log = []
        self.saved_labels = []
        self.export_base_path = None
        self.planning_states = []
        self.preview_thread = None
        self.preview_started = 0

    def artwork_path(self):
        return self._artwork

    def generator_status(self, message):
        self.status.append(message)

    def generator_planning_changed(self, _tab, running):
        self.planning_states.append(running)

    def settings_for_source(self, _tab):
        return converter.Settings()

    def active_ink_colors(self):
        return None

    def motion_estimate_scale(self):
        return converter.DEFAULT_MOTION_ESTIMATE_SCALE

    def export_program_set(self, entries, base_path=None, default_base=""):
        del default_base
        self.export_base_path = base_path
        written = []
        base = Path(base_path)
        for label, gcode in entries:
            path = base.parent / f"{base.stem}-{label}.gcode"
            path.write_text(gcode, encoding="utf-8")
            self.saved_labels.append(label)
            written.append(str(path))
        return written

    def preview(self):
        self.preview_started += 1
        self.preview_thread = FakePreviewThread()


class FakePreviewThread:
    def __init__(self):
        self.finished = FakeSignal()


class FakeSignal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class CmykPhotoTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PIL import Image

        cls.app = QApplication.instance() or QApplication([])
        cls.folder = tempfile.mkdtemp(prefix="cmyk-photo-tab-")
        image = Image.new("RGB", (64, 64), (30, 120, 180))
        for x in range(18, 46):
            for y in range(18, 46):
                image.putpixel((x, y), (220, 80, 40))
        cls.image_path = str(Path(cls.folder) / "portrait.png")
        image.save(cls.image_path)

    def make_tab(self, host=None):
        host = host or FakeHost(self.image_path)
        tab = CmykPhotoTab(host)
        self.addCleanup(tab.deleteLater)
        return tab, host

    def test_guided_page_is_simple_and_inside_a_fourteen_inch_circle(self):
        tab, _host = self.make_tab()
        # Parent windows are not shown offscreen; visibility state is what
        # matters, not isVisible().
        tab.show()
        self.app.processEvents()
        self.assertTrue(tab.guided_panel.isVisible())
        self.assertFalse(tab.controls_scroll.isVisible())
        self.assertIn("Create 4 G-code files", tab.quick_create_button.text())
        self.assertTrue(tab._apply_quick_defaults())
        self.assertEqual(tab.style.currentData(), "edge_flow_coherent")
        self.assertGreaterEqual(tab.gcr.value(), 40.0)
        self.assertEqual(tab.page_w.value(), 250.0)
        self.assertEqual(tab.page_h.value(), 250.0)
        corner_radius = math.hypot(125.0, 125.0)
        self.assertLessEqual(corner_radius, 355.6 / 2.0)

    def test_advanced_toggle_reveals_and_hides_the_full_tuner(self):
        tab, _host = self.make_tab()
        tab.show()
        self.app.processEvents()
        tab.advanced_button.click()
        self.app.processEvents()
        self.assertTrue(tab.controls_scroll.isVisible())
        self.assertFalse(tab.guided_panel.isVisible())
        self.assertEqual(tab.advanced_button.text(), "Back to guided setup")
        tab.advanced_button.click()
        self.app.processEvents()
        self.assertFalse(tab.controls_scroll.isVisible())
        self.assertTrue(tab.guided_panel.isVisible())

    def test_save_handoff_uses_physical_ymck_order_and_one_folder(self):
        tab, host = self.make_tab()
        results = {
            channel: {
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "moves": [],
                "checks": {},
                "seconds": 1.0,
                "marks": 1,
                "draw_mm": 1.0,
                "x_count": 1,
                "y_count": 0,
                "pen_down_count": 1,
                "pen_up_count": 1,
                "compensation": {},
            }
            for channel in converter.CHANNELS
        }
        output = Path(self.folder) / "out"
        output.mkdir(exist_ok=True)
        tab._next_export_base_path = str(output / "portrait-cmyk.gcode")
        with (
            mock.patch.object(tab, "_preflight_errors", return_value=[]),
            mock.patch.object(tab, "_write_set_manifest", return_value=None),
        ):
            tab._write_files(results)
        self.assertEqual(
            host.saved_labels,
            ["01-yellow", "02-magenta", "03-cyan", "04-black"],
        )
        self.assertEqual(
            Path(host.export_base_path).name,
            "portrait-cmyk.gcode",
        )

    def test_create_action_starts_preview_and_defers_save_until_ready(self):
        tab, host = self.make_tab()
        folder = Path(self.folder) / "guided-output"
        folder.mkdir(exist_ok=True)
        with (
            mock.patch.object(
                tab,
                "_apply_quick_defaults",
                return_value=True,
            ),
            mock.patch(
                "generator_tabs.cmyk_tab.QFileDialog.getExistingDirectory",
                return_value=str(folder),
            ),
            mock.patch.object(tab, "save_all") as save,
        ):
            tab.create_guided_set()
            self.assertEqual(host.preview_started, 1)
            self.assertTrue(tab._quick_pending_save)
            self.assertEqual(
                Path(tab._next_export_base_path).name,
                "portrait-cmyk.gcode",
            )
            tab.on_preview_finished()
            save.assert_called_once_with()
        self.assertFalse(tab._quick_pending_save)


if __name__ == "__main__":
    unittest.main()
