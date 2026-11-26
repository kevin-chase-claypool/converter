"""Guided CMYK photo workflow and its print-order handoff."""

import json
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
from generator_tabs.cmyk_tab import (
    REFERENCE_PHOTO_CHAIN_GAP_MM,
    CmykPhotoTab,
)
from generator_tabs.cmyk_workflow import CMYK_WORKFLOW_STAGES


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

    def resolve_program_set_base(self, default_base=""):
        return default_base

    def export_program_set(
        self,
        entries,
        base_path=None,
        default_base="",
        companion_files=None,
    ):
        del default_base
        self.export_base_path = base_path
        written = []
        base = Path(base_path)
        for label, gcode in entries:
            path = base.parent / f"{base.stem}-{label}.gcode"
            path.write_bytes(gcode.encode("utf-8"))
            self.saved_labels.append(label)
            written.append(str(path))
        for path, content in companion_files or ():
            Path(path).write_bytes(content.encode("utf-8"))
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
        for box in tab.write_boxes.values():
            box.setChecked(False)
        # Parent windows are not shown offscreen; visibility state is what
        # matters, not isVisible().
        tab.show()
        self.app.processEvents()
        self.assertTrue(tab.guided_panel.isVisible())
        self.assertFalse(tab.controls_scroll.isVisible())
        self.assertIn("Create 4 G-code files", tab.quick_create_button.text())
        self.assertTrue(tab.workflow_navigator.isVisible())
        self.assertEqual(
            len(tab.workflow_navigator.stages),
            9,
        )
        mapped_groups = {
            title
            for stage in CMYK_WORKFLOW_STAGES
            for title in stage.group_titles
        }
        self.assertEqual(mapped_groups, set(tab.group_boxes))
        self.assertTrue(tab._apply_quick_defaults())
        self.assertEqual(tab.style.currentData(), "edge_flow_coherent")
        self.assertGreaterEqual(tab.gcr.value(), 40.0)
        self.assertEqual(tab.page_w.value(), 250.0)
        self.assertEqual(tab.page_h.value(), 250.0)
        self.assertTrue(all(box.isChecked() for box in tab.write_boxes.values()))
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
        self.assertTrue(
            tab.group_boxes["Page"].isVisible()
        )
        self.assertFalse(
            tab.group_boxes["Flow geometry"].isVisible()
        )
        tab.workflow_navigator.set_stage("review")
        self.app.processEvents()
        self.assertTrue(
            tab.group_boxes["Recommended"].isVisible()
        )
        tab.workflow_navigator.set_stage("direction")
        self.app.processEvents()
        self.assertTrue(
            tab.group_boxes["Flow geometry"].isVisible()
        )
        self.assertFalse(
            tab.group_boxes["Screening"].isVisible()
        )
        tab.advanced_button.click()
        self.app.processEvents()
        self.assertFalse(tab.controls_scroll.isVisible())
        self.assertTrue(tab.guided_panel.isVisible())

    def test_stage_button_opens_advanced_and_reset_restores_defaults(self):
        tab, _host = self.make_tab()
        tab.show()
        self.app.processEvents()
        tab.workflow_navigator._buttons["direction"].click()
        self.app.processEvents()
        self.assertFalse(tab.guided_panel.isVisible())
        self.assertTrue(tab.controls_scroll.isVisible())
        self.assertEqual(tab.workflow_navigator.current_stage, "direction")

        tab.flow_smoothing.setValue(7.5)
        tab.workflow_navigator.reset_button.click()
        self.app.processEvents()
        self.assertEqual(tab.flow_smoothing.value(), 2.5)

    def test_locked_stage_survives_recommended_recipe(self):
        tab, _host = self.make_tab()
        tab.show()
        self.app.processEvents()
        tab.style.setCurrentIndex(tab.style.findData("lines"))
        tab.pitch.setValue(3.20)
        tab.workflow_navigator.set_stage("streamlines")
        tab.workflow_navigator.lock_box.setChecked(True)

        with mock.patch.object(
            tab,
            "_apply_auto_settings_body",
            return_value={},
        ):
            self.assertTrue(tab.apply_reference_defaults())

        self.assertEqual(tab.style.currentData(), "lines")
        self.assertEqual(tab.pitch.value(), 3.20)

    def test_recipe_preset_applies_complete_comparison_recipe(self):
        tab, _host = self.make_tab()
        index = tab.workflow_navigator.recipe_combo.findData(
            "edge_flow_per_ink"
        )
        tab.workflow_navigator.recipe_combo.setCurrentIndex(index)
        with mock.patch.object(
            tab,
            "_apply_auto_settings_body",
            return_value={},
        ):
            tab.workflow_navigator.recipe_button.click()
        self.assertEqual(tab.style.currentData(), "edge_flow")
        self.assertTrue(tab.flow_keylines.isChecked())
        self.assertEqual(
            tab.chain_gap.value(),
            REFERENCE_PHOTO_CHAIN_GAP_MM,
        )
        self.assertEqual(tab.tone_bridge.value(), 1.0)

    def test_separate_flow_controls_reach_coherent_renderer(self):
        tab, _host = self.make_tab()
        np = __import__("numpy")
        tones = {
            channel: np.full((16, 16), 0.6, dtype="float32")
            for channel in (*converter.CHANNELS, "depth", "flow_guide")
        }
        geometry = {
            "off_x": 0.0,
            "off_y": 0.0,
            "width_mm": 250.0,
            "height_mm": 250.0,
            "pixels_w": 16,
            "pixels_h": 16,
        }
        tab.style.setCurrentIndex(
            tab.style.findData("edge_flow_coherent")
        )
        tab.flow_keylines.setChecked(True)
        tab.keyline_quiet.setValue(35)
        tab.color_hold.setValue(9.5)
        tab.color_mix.setValue(81)
        tab.shadow_layer_start.setValue(55)
        tab.shadow_layer_end.setValue(97)
        tab.tone_bridge.setValue(7.5)
        tab.chain_marks.setChecked(False)
        with (
            mock.patch.object(
                converter,
                "prepare_image_tones",
                return_value=(tones, geometry),
            ),
            mock.patch.object(
                converter,
                "screen_coherent_color_flow",
                return_value={
                    channel: []
                    for channel in converter.CHANNELS
                },
            ) as screen,
        ):
            tab._build_artwork_layers()

        kwargs = screen.call_args.kwargs
        self.assertAlmostEqual(kwargs["color_quiet"], 0.35)
        self.assertAlmostEqual(kwargs["color_hold_mm"], 9.5)
        self.assertAlmostEqual(kwargs["color_mix_ratio"], 0.81)
        self.assertAlmostEqual(kwargs["dark_layer_start"], 0.55)
        self.assertAlmostEqual(kwargs["dark_layer_end"], 0.97)
        self.assertAlmostEqual(kwargs["bridge_mm"], 7.5)

    def test_exposed_flow_controls_invalidate_the_layer_cache(self):
        tab, _host = self.make_tab()
        before = tab._control_key()
        tab.keyline_quiet.setValue(tab.keyline_quiet.value() + 5)
        self.assertNotEqual(tab._control_key(), before)

    def test_shadow_layer_thresholds_stay_in_ascending_order(self):
        tab, _host = self.make_tab()
        tab.shadow_layer_start.setValue(88)
        self.assertGreater(tab.shadow_layer_end.value(), 88)
        tab.shadow_layer_end.setValue(40)
        self.assertLess(tab.shadow_layer_start.value(), 40)
        tab.shadow_layer_start.setValue(99)
        self.assertEqual(tab.shadow_layer_start.value(), 98)
        self.assertEqual(tab.shadow_layer_end.value(), 99)

    def test_direction_diagnostic_renders_orientation_image(self):
        tab, _host = self.make_tab()
        image = tab.flow_field_diagnostic_image()
        self.assertGreater(image.width, 1)
        self.assertGreater(image.height, 1)
        self.assertEqual(image.mode, "RGB")
        with mock.patch.object(
            tab,
            "show_flow_field_diagnostic",
        ) as show:
            tab.show_stage_diagnostic("direction")
            show.assert_called_once_with()

    def test_stage_validation_reports_missing_artwork_and_pen_floor(self):
        tab, _host = self.make_tab(FakeHost(""))
        tab._artwork = ""
        self.assertTrue(
            any(
                "Import an artwork" in issue
                for issue in tab.validate_stage("composition")
            )
        )
        tab.pen_width.setValue(2.0)
        tab.scale_pct.setValue(10)
        tab.pitch.setValue(0.1)
        self.assertTrue(
            any(
                "pen-safe" in issue
                for issue in tab.validate_stage("streamlines")
            )
        )

    def test_workflow_stage_and_locks_round_trip_with_recipe(self):
        tab, _host = self.make_tab()
        tab.workflow_navigator.set_stage("motion")
        tab.workflow_navigator.set_locked("direction", True)
        tab.shadow_layer_start.setValue(62)
        tab.shadow_layer_end.setValue(96)
        tab.keyline_quiet.setValue(45)
        tab.color_hold.setValue(11.5)
        tab.color_mix.setValue(84)
        tab.tone_bridge.setValue(8.5)
        state = tab.artwork_layout_state()
        tab.workflow_navigator.set_stage("composition")
        tab.workflow_navigator.set_locked("direction", False)
        tab.shadow_layer_start.setValue(40)
        tab.color_hold.setValue(6.0)
        tab.tone_bridge.setValue(4.0)

        self.assertTrue(tab.restore_artwork_layout_state(state))
        self.assertEqual(tab.workflow_navigator.current_stage, "motion")
        self.assertTrue(tab.workflow_navigator.is_locked("direction"))
        self.assertEqual(tab.shadow_layer_start.value(), 62)
        self.assertEqual(tab.shadow_layer_end.value(), 96)
        self.assertEqual(tab.keyline_quiet.value(), 45)
        self.assertEqual(tab.color_hold.value(), 11.5)
        self.assertEqual(tab.color_mix.value(), 84)
        self.assertEqual(tab.tone_bridge.value(), 8.5)

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
        tab.style.setCurrentIndex(
            tab.style.findData("edge_flow_coherent")
        )
        tab._next_export_base_path = str(output / "portrait-cmyk.gcode")
        with mock.patch.object(tab, "_preflight_errors", return_value=[]):
            tab._write_files(results)
        self.assertEqual(
            host.saved_labels,
            ["01-yellow", "02-magenta", "03-cyan", "04-black"],
        )
        self.assertEqual(
            Path(host.export_base_path).name,
            "portrait-cmyk.gcode",
        )
        manifest_path = output / "portrait-cmyk-set.json"
        self.assertTrue(manifest_path.is_file())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            set(manifest["workflow"]["stage_settings_sha256"]),
            {stage.key for stage in CMYK_WORKFLOW_STAGES},
        )
        self.assertAlmostEqual(
            manifest["screen"]["shadow_layer_start_pct"],
            40.0,
        )
        self.assertAlmostEqual(
            manifest["screen"]["shadow_layer_end_pct"],
            90.0,
        )
        self.assertAlmostEqual(
            manifest["screen"]["keyline_color_quiet_pct"],
            25.0,
        )
        self.assertAlmostEqual(
            manifest["screen"]["coherent_color_hold_mm"],
            6.0,
        )
        self.assertAlmostEqual(
            manifest["screen"]["coherent_color_mix_ratio"],
            0.72,
        )
        self.assertAlmostEqual(
            manifest["screen"]["pen_down_chain"]["local_flow_bridge_mm"],
            4.0,
        )

    def test_complete_set_rejects_different_ink_contracts(self):
        tab, _host = self.make_tab()
        identity = {
            "scale": 1.0,
            "frame_center_mm": [125.0, 125.0],
            "bed_compensation": {"full_profile_fingerprint": "abc"},
        }
        results = {
            channel: {
                "set_identity": dict(identity),
            }
            for channel in converter.CHANNELS
        }
        results["m"]["set_identity"]["frame_center_mm"] = [124.0, 125.0]
        errors = tab._set_consistency_errors(
            results,
            list(converter.CHANNELS),
        )
        self.assertTrue(
            any("do not share one scale" in error for error in errors)
        )
        del results["k"]
        errors = tab._set_consistency_errors(results, list(results))
        self.assertTrue(
            any("requires all four inks" in error for error in errors)
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
