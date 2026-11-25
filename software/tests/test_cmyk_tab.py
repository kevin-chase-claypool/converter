"""CMYK separation, screening, layer SVGs, and per-ink cost analysis."""

import hashlib
import json
import math
import os
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover - the core tests do not need Qt
    HAVE_QT = False


def svg_groups(root):
    """Return the data-ink groups (the SVG root also ends in 'g')."""
    return [
        element.get("data-ink")
        for element in root.iter()
        if element.tag.split("}")[-1] == "g"
    ]




@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class CmykTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from generator_tabs.cmyk_tab import CmykTab

        cls.CmykTab = CmykTab
        cls.app = QApplication.instance() or QApplication([])
        folder = tempfile.mkdtemp(prefix="cmyk-tab-")
        cls.folder = folder
        from PIL import Image

        image = Image.new("RGB", (48, 48), (255, 255, 255))
        for x in range(12, 36):
            for y in range(12, 36):
                image.putpixel((x, y), (0, 0, 0))
        cls.image_path = str(Path(folder) / "art.png")
        image.save(cls.image_path)
        # A full-ink, asymmetric image: every channel carries marks in a
        # different region, so per-ink bounding boxes differ strongly.
        colour = Image.new("RGB", (96, 96), (255, 255, 255))
        for x in range(96):
            for y in range(96):
                if x < 48 and y < 48:
                    colour.putpixel((x, y), (0, 200, 220))
                elif x >= 48 and y < 48:
                    colour.putpixel((x, y), (220, 0, 150))
                elif x < 48:
                    colour.putpixel((x, y), (240, 220, 0))
                else:
                    colour.putpixel((x, y), (40, 40, 40))
        cls.colour_path = str(Path(folder) / "colour.png")
        colour.save(cls.colour_path)

    def make_tab(self, host=None):
        host = host or FakeHost(self.image_path)
        tab = self.CmykTab(host)
        self.addCleanup(tab.deleteLater)
        tab.page_w.setValue(60)
        tab.page_h.setValue(60)
        tab.margin.setValue(4)
        tab.pitch.setValue(4.0)
        tab.max_marks.setValue(400)
        return tab

    @staticmethod
    def clean_checks():
        return {
            "drawing": 1,
            "travel": 0,
            "hold": 0,
            "strategies": {},
            "step": 0.0,
            "step_line": 0,
            "rate": 0.0,
            "rate_line": 0,
            "deviation": (0.0, 0.0, 0, ""),
            "tolerance": 0.05,
            "over_tolerance": 0,
            "rapids_with_rotation": 0,
            "fed_rotations": 0,
            "unwinds": 0,
            "cap": 15.0,
            "rate_cap": 500.0,
        }

    def test_build_svg_writes_every_layer_for_the_planner(self):
        tab = self.make_tab()
        path = tab.build_svg()
        root = ET.parse(path).getroot()
        self.assertEqual(svg_groups(root), list(converter.CHANNELS))
        tab.preview_boxes["k"].setChecked(False)
        path = tab.build_svg()
        root = ET.parse(path).getroot()
        self.assertEqual(svg_groups(root), list(converter.CHANNELS))
        self.assertEqual(tab.preview_visible_inks(), ["c", "m", "y"])

    def test_preview_can_hide_every_layer(self):
        tab = self.make_tab()
        for box in tab.preview_boxes.values():
            box.setChecked(False)
        path = tab.build_svg()
        self.assertTrue(Path(path).exists())
        self.assertEqual(tab.preview_visible_inks(), [])

    def test_every_screen_style_builds_all_four_layers(self):
        tab = self.make_tab()
        tab.levels.setValue(3)
        tab.overdraw.setValue(2)
        for style in (
            "halftone",
            "stipple",
            "lines",
            "rectilinear",
            "continuous",
            "crosshatch",
            "waves_even",
            "waves_zero",
            "gyroid",
            "tsp",
            "contours",
            "edge_flow",
            "edge_flow_shared",
        ):
            tab.style.setCurrentIndex(tab.style.findData(style))
            root = ET.parse(tab.build_svg()).getroot()
            self.assertEqual(svg_groups(root), list(converter.CHANNELS), style)

    def test_edge_flow_controls_build_and_round_trip(self):
        tab = self.make_tab()
        style_index = tab.style.findData("edge_flow")
        self.assertGreaterEqual(style_index, 0)
        tab.style.setCurrentIndex(style_index)
        tab.flow_smoothing.setValue(2.5)
        tab.flow_layers.setValue(2)
        tab.flow_keylines.setChecked(True)

        state = tab.artwork_layout_state()
        self.assertEqual(state["screen"]["style"], "edge_flow")
        self.assertAlmostEqual(state["screen"]["flow_smoothing_mm"], 2.5)
        self.assertEqual(state["screen"]["flow_layers"], 2)
        self.assertTrue(state["screen"]["preserve_black_keylines"])

        root = ET.parse(tab.build_svg()).getroot()
        self.assertEqual(svg_groups(root), list(converter.CHANNELS))

        restored = self.make_tab()
        self.assertTrue(restored.restore_artwork_layout_state(state))
        self.assertEqual(restored.style.currentData(), "edge_flow")
        self.assertAlmostEqual(restored.flow_smoothing.value(), 2.5)
        self.assertEqual(restored.flow_layers.value(), 2)
        self.assertTrue(restored.flow_keylines.isChecked())

    def test_pen_down_chain_round_trips_with_the_artwork_recipe(self):
        tab = self.make_tab()
        tab.chain_marks.setChecked(False)
        tab.chain_gap.setValue(8.5)

        state = tab.artwork_layout_state()
        self.assertFalse(state["screen"]["chain_marks"])
        self.assertAlmostEqual(state["screen"]["chain_gap_mm"], 8.5)

        restored = self.make_tab()
        self.assertTrue(restored.restore_artwork_layout_state(state))
        self.assertFalse(restored.chain_marks.isChecked())
        self.assertAlmostEqual(restored.chain_gap.value(), 8.5)

    def test_pen_down_chain_gap_reaches_post_planner_settings(self):
        tab = self.make_tab()
        tab.chain_marks.setChecked(True)
        tab.chain_gap.setValue(6.5)

        settings = tab.apply_tab_settings(converter.Settings())

        self.assertAlmostEqual(settings.screen_chain_gap_mm, 6.5)
        tab.chain_marks.setChecked(False)
        settings = tab.apply_tab_settings(converter.Settings())
        self.assertEqual(settings.screen_chain_gap_mm, 0.0)

    def test_pen_offset_translation_preserves_screen_chain_tag(self):
        tab = self.make_tab()
        marks = [
            converter.ScreenTrail([(0.0, 0.0), (10.0, 0.0)]),
        ]

        translated = tab._translate_marks(marks, 1.0, 2.0)

        self.assertIsInstance(translated[0], converter.ScreenTrail)
        self.assertEqual(translated[0], [(1.0, 2.0), (11.0, 2.0)])

    def test_pen_down_chain_joins_short_marks_for_non_edge_flow(self):
        tab = self.make_tab()
        tab.chain_marks.setChecked(True)
        tab.chain_gap.setValue(5.0)
        short_marks = [
            [(10.0, 20.0), (20.0, 20.0)],
            [(21.5, 20.0), (30.0, 20.0)],
        ]
        with mock.patch.object(
            converter,
            "screen_channel",
            return_value=short_marks,
        ):
            tab._ensure_layers()

        for channel in converter.CHANNELS:
            self.assertEqual(len(tab._layers[channel]), 1)
            self.assertIsInstance(
                tab._layers[channel][0],
                converter.ScreenTrail,
            )
            self.assertEqual(
                tab._pen_chain_stats[channel]["connections"],
                1,
            )

    def test_shared_edge_flow_chains_short_marks_to_reduce_penups(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow_shared"))
        tab.chain_marks.setChecked(True)
        tab.chain_gap.setValue(5.0)
        short_marks = [
            [(10.0, 20.0), (20.0, 20.0)],
            [(21.5, 20.0), (30.0, 20.0)],
        ]
        with mock.patch.object(
            converter,
            "screen_cmyk_edge_flow",
            return_value={
                channel: list(short_marks)
                for channel in converter.CHANNELS
            },
        ):
            tab._ensure_layers()

        for channel in converter.CHANNELS:
            self.assertEqual(len(tab._layers[channel]), 1)
            self.assertEqual(
                tab._pen_chain_stats[channel]["connections"],
                1,
            )

    def test_shared_edge_flow_builds_one_network_for_all_inks(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow_shared"))
        tab.scale_pct.setValue(260)
        captured = {}
        calls = []

        def capture_shared(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            calls.append((args, kwargs))
            return {channel: [] for channel in converter.CHANNELS}

        tab.flow_keylines.setChecked(True)
        with mock.patch.object(
            converter,
            "screen_cmyk_edge_flow",
            side_effect=capture_shared,
        ):
            tab._ensure_layers()

        self.assertEqual(len(calls), 1)
        tones, geometry = captured["args"]
        self.assertIs(captured["kwargs"]["flow_guide"], tones["depth"])
        self.assertEqual(captured["kwargs"]["seed"], 7)
        self.assertAlmostEqual(
            captured["kwargs"]["pen_diameter_mm"],
            tab.pen_width.value() / 2.6,
            places=6,
        )
        self.assertTrue(captured["kwargs"]["keylines"])
        self.assertEqual(captured["kwargs"]["color_quiet"], 0.25)
        self.assertIsNone(captured["kwargs"]["tone_segment_mm"])
        self.assertIsNone(captured["kwargs"]["max_path_mm"])

    def test_edge_flow_builds_four_independent_ink_networks(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.chain_marks.setChecked(False)
        tab.flow_keylines.setChecked(True)
        tab.scale_pct.setValue(260)
        calls = []

        def capture_channel(tone, geometry, **kwargs):
            calls.append((tone, geometry, kwargs))
            seed = int(kwargs["seed"])
            return [
                [
                    (float(seed), 10.0),
                    (float(seed + 1), 20.0),
                ]
            ]

        with mock.patch.object(
            converter,
            "screen_channel",
            side_effect=capture_channel,
        ), mock.patch.object(
            converter,
            "screen_cmyk_edge_flow",
            side_effect=AssertionError("default Edge-flow must be per-ink"),
        ):
            tab._ensure_layers()

        self.assertEqual(len(calls), len(converter.CHANNELS))
        self.assertEqual(
            [call[2]["seed"] for call in calls],
            [tab.seed.value() + index for index in range(4)],
        )
        self.assertEqual(
            [call[2]["angle_deg"] for call in calls],
            [
                converter.SCREEN_ANGLES_DEG[channel]
                for channel in converter.CHANNELS
            ],
        )
        self.assertTrue(
            all(
                call[2]["flow_guide"] is calls[0][2]["flow_guide"]
                for call in calls
            )
        )
        self.assertEqual(
            [call[2]["flow_keylines"] for call in calls],
            [False, False, False, True],
        )
        self.assertEqual(
            [call[2]["flow_color_quiet"] for call in calls],
            [0.25, 0.25, 0.25, 0.0],
        )
        self.assertEqual(len(set(tab._layer_files.values())), 4)

    def test_fine_detail_uses_two_mm_tone_segments_on_paper(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.pen_width.setValue(0.6)
        tab.scale_pct.setValue(260)
        tab.detail_button.click()
        tone_segments = []
        max_paths = []

        def capture_segment(*args, **kwargs):
            tone_segments.append(kwargs.get("flow_tone_segment_mm"))
            max_paths.append(kwargs.get("flow_max_path_mm"))
            return []

        with mock.patch.object(
            converter,
            "screen_channel",
            side_effect=capture_segment,
        ):
            tab._ensure_layers()

        self.assertEqual(len(tone_segments), len(converter.CHANNELS))
        for value in tone_segments:
            self.assertAlmostEqual(value, 2.0 / 2.6, places=6)
        for value in max_paths:
            self.assertAlmostEqual(value, 12.0 / 2.6, places=6)

    def test_analysis_worker_reports_strategy_split(self):
        from generator_tabs.cmyk_tab import ProgramAnalysisWorker

        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._ensure_layers()
        results = {}
        worker = ProgramAnalysisWorker(
            host,
            converter.Settings(),
            converter.DEFAULT_MOTION_ESTIMATE_SCALE,
            [("k", tab._layer_files["k"])],
        )
        worker.finished.connect(results.update)
        worker.run()
        record = results["k"]
        self.assertEqual(record["x_count"], 2)
        self.assertEqual(record["y_count"], 1)
        self.assertEqual(record["marks"], 2)
        self.assertGreater(record["seconds"], 0.0)

    def test_analysis_worker_passes_each_inks_screen_angle(self):
        from generator_tabs.cmyk_tab import ProgramAnalysisWorker

        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._ensure_layers()
        seen = {}
        analyze = host.analyze_program

        def recording_analyze(path, settings, cancel_check=None):
            seen[settings.row_lock_screen_angle_deg] = path
            return analyze(path, settings, cancel_check)

        host.analyze_program = recording_analyze
        worker = ProgramAnalysisWorker(
            host,
            converter.Settings(row_locked_compensation=True),
            converter.DEFAULT_MOTION_ESTIMATE_SCALE,
            [
                (channel, tab._layer_files[channel])
                for channel in converter.CHANNELS
            ],
        )
        results = {}
        worker.finished.connect(results.update)

        worker.run()

        self.assertEqual(
            set(seen),
            set(converter.SCREEN_ANGLES_DEG.values()),
        )
        self.assertEqual(set(results), set(converter.CHANNELS))

    def test_analysis_worker_prepares_the_row_lock_set_once(self):
        from generator_tabs.cmyk_tab import ProgramAnalysisWorker

        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._ensure_layers()
        seen = []
        analyze = host.analyze_program

        def recording_analyze(path, settings, cancel_check=None):
            seen.append(
                (
                    settings.row_lock_screen_angle_deg,
                    settings.row_lock_projection.fingerprint,
                )
            )
            return analyze(path, settings, cancel_check)

        host.analyze_program = recording_analyze
        defaults = converter.default_settings()
        settings = converter.Settings(
            row_locked_compensation=True,
            bed_compensation_path=defaults.bed_compensation_path,
        )
        worker = ProgramAnalysisWorker(
            host,
            settings,
            converter.DEFAULT_MOTION_ESTIMATE_SCALE,
            [
                (channel, tab._layer_files[channel])
                for channel in converter.CHANNELS
            ],
        )
        results = {}
        worker.finished.connect(results.update)

        with mock.patch.object(
            converter,
            "row_locked_bed_compensation_set",
            wraps=converter.row_locked_bed_compensation_set,
        ) as prepare:
            worker.run()

        prepare.assert_called_once()
        self.assertEqual(set(results), set(converter.CHANNELS))
        self.assertEqual(
            {angle for angle, _fingerprint in seen},
            set(converter.SCREEN_ANGLES_DEG.values()),
        )
        self.assertEqual(
            len({fingerprint for _angle, fingerprint in seen}),
            len(converter.CHANNELS),
        )

    def test_kinematics_bullets_override_the_settings(self):
        tab = self.make_tab()
        self.assertEqual(
            [button.property("choice_value") for button in tab.theta_mode._buttons],
            ["optimized", "fixed"],
            "the CMYK tab offers exactly the two kinematic bullets",
        )
        settings = tab.apply_tab_settings(converter.Settings())
        self.assertEqual(settings.theta_mode, "optimized")
        self.assertEqual(settings.theta_center_hold_diameter_mm, 60.0)
        tab.theta_mode.set_value("fixed")
        tab.center_hold.setValue(70.0)
        settings = tab.apply_tab_settings(converter.Settings())
        self.assertEqual(settings.theta_mode, "fixed")
        self.assertEqual(settings.theta_center_hold_diameter_mm, 70.0)
        self.assertEqual(tab._effective_settings().theta_mode, "fixed")

    def test_wave_row_order_selector_overrides_planner_optimization(self):
        tab = self.make_tab()
        values = [
            tab.contour_order.itemData(index)
            for index in range(tab.contour_order.count())
        ]
        self.assertEqual(
            values,
            ["optimized", "rows_ascending", "rows_descending"],
        )
        self.assertFalse(tab.contour_order.isEnabled())

        tab.style.setCurrentIndex(tab.style.findData("waves_even"))
        self.assertTrue(tab.contour_order.isEnabled())
        tab.contour_order.setCurrentIndex(
            tab.contour_order.findData("rows_ascending")
        )
        self.assertEqual(
            tab.apply_tab_settings(converter.Settings()).contour_order,
            "rows_ascending",
        )

        tab.style.setCurrentIndex(tab.style.findData("rectilinear"))
        self.assertFalse(tab.contour_order.isEnabled())
        self.assertEqual(
            tab.apply_tab_settings(converter.Settings()).contour_order,
            "optimized",
        )

    def test_cmyk_wave_selector_separates_production_and_legacy_modes(self):
        tab = self.make_tab()
        self.assertEqual(tab.style.findData("waves"), -1)
        exact = tab.style.findData("waves_even")
        legacy = tab.style.findData("waves_zero")
        self.assertGreaterEqual(exact, 0)
        self.assertGreaterEqual(legacy, 0)
        self.assertEqual(
            tab.style.itemText(exact),
            "Wave screen - equidistant rows",
        )
        self.assertEqual(
            tab.style.itemText(legacy),
            "Wave screen - legacy phase-locked depth (diagnostic)",
        )
        tooltip = tab.style.toolTip().lower()
        self.assertIn("exactly one pitch apart", tooltip)
        self.assertIn("legacy diagnostic", tooltip)
        self.assertIn("selected bed-compensation profile", tooltip)

    def test_legacy_wave_diagnostic_keeps_selected_dense_v3_mesh(self):
        host = FakeHost(self.colour_path)
        host.settings_for_source = mock.Mock(
            return_value=converter.default_settings()
        )
        tab = self.make_tab(host)
        tab.style.setCurrentIndex(tab.style.findData("waves_zero"))

        settings = tab._effective_settings()
        self.assertEqual(
            Path(settings.bed_compensation_path).name,
            "bed-error-compensation-2026-11-01-dense-v3-360mm-reach-extrapolated.json",
        )
        self.assertFalse(settings.row_locked_compensation)
        self.assertFalse(tab._wave_spacing_guard_active())
        self.assertFalse(tab._variable_wave_frequency_active())
        self.assertTrue(tab._legacy_wave_screen_active())
        self.assertFalse(tab.preserve_wave_pitch.isEnabled())
        self.assertFalse(tab.vary_wave_frequency.isEnabled())
        self.assertIn(
            "raw selected profile",
            tab._summary_text().lower(),
        )

        with mock.patch.object(
            converter,
            "screen_channel",
            wraps=converter.screen_channel,
        ) as screen_channel:
            tab._ensure_layers()
        calls = screen_channel.call_args_list
        self.assertTrue(calls)
        for call in calls:
            self.assertEqual(call.kwargs["style"], "waves_zero")
            self.assertTrue(call.kwargs["allow_variable_wave_spacing"])
            self.assertEqual(call.kwargs["wave_frequency_variation"], 0.0)

        contours = converter.read_svg(
            str(tab._layer_files["y"]), settings
        )
        plan = converter.plan_program(contours, settings)
        compensation = plan["bed_compensation"]
        self.assertEqual(compensation.fingerprint, "f85ec410dbac")
        self.assertFalse(getattr(compensation, "row_locked", False))

    def test_wave_spacing_guard_row_locks_bed_compensation(self):
        tab = self.make_tab()
        tab.host.settings_for_source = mock.Mock(
            return_value=converter.default_settings()
        )
        tab.style.setCurrentIndex(tab.style.findData("waves_even"))

        guarded = tab._effective_settings()
        self.assertEqual(
            guarded.bed_compensation_path,
            converter.default_settings().bed_compensation_path,
        )
        self.assertTrue(guarded.row_locked_compensation)
        self.assertTrue(tab._wave_spacing_guard_active())
        self.assertTrue(tab._variable_wave_frequency_active())
        self.assertTrue(tab.vary_wave_frequency.isEnabled())

        tab.preserve_wave_pitch.setChecked(False)
        unguarded = tab._effective_settings()
        self.assertEqual(
            unguarded.bed_compensation_path,
            converter.default_settings().bed_compensation_path,
        )
        self.assertFalse(unguarded.row_locked_compensation)
        self.assertIn(
            "raw compensation may alter pitch",
            tab._summary_text().lower(),
        )

        tab.style.setCurrentIndex(tab.style.findData("rectilinear"))
        self.assertEqual(
            tab._effective_settings().bed_compensation_path,
            converter.default_settings().bed_compensation_path,
        )
        self.assertFalse(
            tab._effective_settings().row_locked_compensation
        )
        self.assertFalse(tab.preserve_wave_pitch.isEnabled())
        self.assertFalse(tab.vary_wave_frequency.isEnabled())
        self.assertFalse(tab._variable_wave_frequency_active())

        tab.style.setCurrentIndex(tab.style.findData("waves_even"))
        tab.calibration_mode.setChecked(True)
        self.assertFalse(tab._wave_spacing_guard_active())
        self.assertFalse(tab.preserve_wave_pitch.isEnabled())
        self.assertFalse(tab.vary_wave_frequency.isEnabled())
        self.assertFalse(tab._variable_wave_frequency_active())
        self.assertIn("not applicable", tab._summary_text().lower())
        self.assertEqual(
            tab._effective_settings().bed_compensation_path,
            converter.default_settings().bed_compensation_path,
        )

    def test_xy_only_layer_program_holds_the_bed(self):
        tab = self.make_tab()
        tab._ensure_layers()
        tab.theta_mode.set_value("fixed")
        settings = tab._effective_settings()
        contours = converter.read_svg(str(tab._layer_files["k"]), settings)
        plan = converter.plan_program(contours, settings)
        text = converter.contours_to_gcode(contours, settings, plan)
        self.assertIsNone(plan["wave_row_schedule"])
        self.assertIn(
            "(frame center 30.000,30.000 mm, bed motion XY only)", text
        )
        angles = set()
        for line in text.splitlines():
            if line.startswith(("G0 ", "G1 ", "G53 ")):
                angles.update(
                    float(value) for value in re.findall(r"A(-?\d+\.?\d*)", line)
                )
        self.assertEqual(angles, {0.0}, "XY only must never rotate the bed")
        strategies = set()
        for _planned, _points, _thetas, labels in plan["planned_jobs"]:
            strategies.update(label for label in labels if label)
        self.assertEqual(strategies, {"fixed"})

    def test_pen_offsets_shift_only_the_selected_ink(self):
        tab = self.make_tab()
        tab.registration_marks.setChecked(False)
        tab._ensure_layers()
        before = {
            channel: [list(line) for line in tab._layers[channel]]
            for channel in converter.CHANNELS
        }
        tab.offset_spins["m"][0].setValue(1.25)
        tab.offset_spins["m"][1].setValue(-0.50)
        tab._ensure_layers()
        for channel in converter.CHANNELS:
            dx, dy = (1.25, -0.50) if channel == "m" else (0.0, 0.0)
            after = tab._layers[channel]
            self.assertEqual(len(before[channel]), len(after), channel)
            for line_before, line_after in zip(before[channel], after):
                self.assertEqual(len(line_before), len(line_after), channel)
                for (x0, y0), (x1, y1) in zip(line_before, line_after):
                    self.assertAlmostEqual(x1, x0 + dx, places=6)
                    self.assertAlmostEqual(y1, y0 + dy, places=6)

    def test_measured_alignment_sets_opposite_corrections(self):
        tab = self.make_tab()
        tab.measured_spins["y"][0].setValue(1.20)
        tab.measured_spins["y"][1].setValue(-0.40)
        tab.measured_spins["c"][0].setValue(9.0)
        tab._apply_measured_offsets()
        self.assertAlmostEqual(
            tab.offset_spins["y"][0].value(), -1.20, places=2
        )
        self.assertAlmostEqual(
            tab.offset_spins["y"][1].value(), 0.40, places=2
        )
        self.assertEqual(tab.offset_spins["c"][0].value(), 0.0)

    def test_every_ink_inherits_the_centered_dense_compensation(self):
        host = FakeHost(self.colour_path)
        host.settings_for_source = lambda _tab: converter.default_settings()
        tab = self.make_tab(host)
        tab._ensure_layers()
        settings = tab._effective_settings()

        self.assertEqual(
            Path(settings.bed_compensation_path).name,
            "bed-error-compensation-2026-11-01-dense-v3-360mm-reach-extrapolated.json",
        )
        for channel in converter.CHANNELS:
            contours = converter.read_svg(
                str(tab._layer_files[channel]), settings
            )
            plan = converter.plan_program(contours, settings)
            self.assertEqual(
                plan["bed_compensation"].fingerprint,
                "f85ec410dbac",
                channel,
            )

    def test_pen_offsets_keep_the_shared_page_frame(self):
        tab = self.make_tab(FakeHost(self.colour_path))
        tab.scale_pct.setValue(280)
        tab.offset_spins["y"][0].setValue(3.0)
        tab.offset_spins["y"][1].setValue(-2.0)
        tab._ensure_layers()
        settings = tab._effective_settings()
        expected = (tab.page_w.value() / 2.0, tab.page_h.value() / 2.0)
        for channel in converter.CHANNELS:
            contours = converter.read_svg(
                str(tab._layer_files[channel]), settings
            )
            plan = converter.plan_program(contours, settings)
            self.assertAlmostEqual(
                plan["source_center"][0], expected[0], places=6, msg=channel
            )
            self.assertAlmostEqual(
                plan["source_center"][1], expected[1], places=6, msg=channel
            )

    def test_calibration_sheet_ignores_pen_offsets(self):
        tab = self.make_tab()
        tab.calibration_mode.setChecked(True)
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        tab._ensure_layers()
        before = {
            channel: [list(line) for line in tab._layers[channel]]
            for channel in converter.CHANNELS
        }
        tab.offset_spins["m"][0].setValue(2.0)
        tab._ensure_layers()
        for channel in converter.CHANNELS:
            self.assertEqual(tab._layers[channel], before[channel], channel)

    def test_pass_summary_reports_offsets_and_preflight(self):
        tab = self.make_tab()
        tab.offset_spins["m"][0].setValue(0.50)
        text = tab._summary_text()
        self.assertIn("pen offsets", text)
        self.assertIn("M +0.50", text)
        clean = {"c": {"checks": self.clean_checks()}}
        self.assertIn("preflight OK", tab._summary_text(clean))
        broken = self.clean_checks()
        broken["step"] = 20.0
        self.assertIn(
            "preflight BLOCKED",
            tab._summary_text({"c": {"checks": broken}}),
        )

    def test_hard_preflight_violation_blocks_save(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        broken = self.clean_checks()
        broken["rate"] = 600.0
        results = {
            channel: {
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "checks": dict(broken),
            }
            for channel in converter.CHANNELS
        }
        tab._write_files(results)
        self.assertEqual(host.saved_labels, [])
        self.assertIn("preflight blocked", tab.status.text().lower())

    def test_artwork_save_writes_a_set_manifest(self):
        host = FakeHost(self.image_path)
        host.settings_for_source = mock.Mock(
            return_value=converter.default_settings()
        )
        tab = self.make_tab(host)
        tab.style.setCurrentIndex(tab.style.findData("waves_even"))
        tab.contour_order.setCurrentIndex(
            tab.contour_order.findData("rows_ascending")
        )
        tab.offset_spins["m"][0].setValue(0.75)
        checks = self.clean_checks()
        results = {
            channel: {
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "checks": dict(checks),
                "compensation": {
                    "mode": "row_locked_projection",
                    "projected_max_correction_mm": 0.5,
                    "raw_translation_means_mm": [
                        [0.17, 0.16],
                        [-0.02, 0.23],
                        [0.21, 0.11],
                        [0.08, 0.21],
                        [0.00, 0.00],
                        [0.00, 0.00],
                        [0.00, 0.00],
                        [0.00, 0.00],
                    ],
                    "common_translation_mm": [0.0, 0.0],
                    "translation_domain_radius_mm": 180.0,
                    "translation_samples_per_axis": 65,
                },
            }
            for channel in converter.CHANNELS
        }
        tab._write_files(results)
        manifest = Path(host.saved_paths["cyan"]).with_name("art-cmyk-set.json")
        self.assertTrue(manifest.exists())
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["kind"], "cmyk-print-set")
        self.assertEqual(data["version"], 4)
        self.assertAlmostEqual(data["pen_offsets_mm"]["m"][0], 0.75)
        self.assertEqual(set(data["preflight"]), set(converter.CHANNELS))
        self.assertEqual(
            data["source"]["sha256"],
            hashlib.sha256(Path(self.image_path).read_bytes()).hexdigest(),
        )
        self.assertEqual(
            data["screen"]["style"],
            tab.style.currentData(),
        )
        self.assertEqual(
            data["screen"]["wave_phase_mode"],
            "identical_translated_rows",
        )
        self.assertEqual(
            data["screen"]["contour_order"],
            "rows_ascending",
        )
        self.assertTrue(data["row_theta_lock"])
        self.assertNotIn(
            "wave_frequency_tone_gain",
            data["screen"],
        )
        self.assertAlmostEqual(
            data["screen"]["effective_pitch_mm"],
            tab.pitch.value() * tab.scale_pct.value() / 100.0,
        )
        self.assertEqual(data["ink_processing"]["weights"]["y"], 1.0)
        self.assertEqual(
            data["bed_compensation_path"],
            converter.default_settings().bed_compensation_path,
        )
        self.assertTrue(data["screen"]["preserve_exact_row_pitch"])
        self.assertEqual(
            data["screen"]["wave_frequency_mode"],
            "shared_phase_modulated",
        )
        self.assertAlmostEqual(
            data["screen"]["wave_frequency_variation_pct"],
            converter.WAVE_FREQUENCY_VARIATION * 100.0,
        )
        self.assertEqual(
            data["bed_compensation"]["mode"],
            "row_locked_projection",
        )
        self.assertEqual(
            data["bed_compensation"]["profile_fingerprint"],
            "f85ec410dbac",
        )
        normalization = data["bed_compensation"][
            "translation_normalization"
        ]
        self.assertEqual(normalization["mode"], "shared_zero_mean")
        self.assertEqual(normalization["domain"], "compensation_coverage_disk")
        self.assertEqual(normalization["common_mean_mm"], [0.0, 0.0])
        self.assertEqual(
            set(
                data["bed_compensation"][
                    "per_channel_raw_translation_means_mm"
                ]
            ),
            set(converter.CHANNELS),
        )
        self.assertEqual(
            set(data["bed_compensation"]["screen_angles_deg"]),
            set(converter.CHANNELS),
        )
        self.assertEqual(
            data["ink_processing"]["sharpening"],
            {
                "enabled": True,
                "amount_pct": 60.0,
                "radius_mm": 1.5,
            },
        )
        self.assertIn("bed_compensation_path", data)
        for channel in converter.CHANNELS:
            saved = Path(
                host.saved_paths[converter.CHANNEL_LABELS[channel].lower()]
            )
            self.assertEqual(
                data["file_sha256"][channel],
                hashlib.sha256(saved.read_bytes()).hexdigest(),
            )
        self.assertIn("Set manifest", tab.status.text())

    def test_set_manifest_records_the_global_artwork_placement(self):
        host = FakeHost(self.image_path)
        host.settings_for_source = mock.Mock(
            return_value=converter.Settings(
                artwork_offset_x_mm=-3.17,
                artwork_offset_y_mm=-28.74,
            )
        )
        tab = self.make_tab(host)
        results = {
            channel: {
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "checks": self.clean_checks(),
            }
            for channel in converter.CHANNELS
        }

        tab._write_files(results)

        manifest = Path(host.saved_paths["cyan"]).with_name(
            "art-cmyk-set.json"
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            data["artwork_placement_mm"],
            [-3.17, -28.74],
        )

    def test_legacy_wave_manifest_records_current_mesh_raw_mode(self):
        host = FakeHost(self.image_path)
        host.settings_for_source = mock.Mock(
            return_value=converter.default_settings()
        )
        tab = self.make_tab(host)
        tab.style.setCurrentIndex(tab.style.findData("waves_zero"))
        checks = self.clean_checks()
        results = {
            channel: {
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "checks": dict(checks),
            }
            for channel in converter.CHANNELS
        }

        tab._write_files(results)

        manifest = Path(host.saved_paths["cyan"]).with_name(
            "art-cmyk-set.json"
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["screen"]["style"], "waves_zero")
        self.assertEqual(
            data["screen"]["wave_phase_mode"],
            "shared_zero_anchored",
        )
        self.assertFalse(data["screen"]["preserve_exact_row_pitch"])
        self.assertEqual(
            data["screen"]["wave_frequency_mode"],
            "constant",
        )
        self.assertEqual(
            data["bed_compensation"]["mode"],
            "raw_unconstrained",
        )
        self.assertEqual(
            data["bed_compensation"]["profile_fingerprint"],
            "f85ec410dbac",
        )
        self.assertEqual(
            Path(data["bed_compensation_path"]).name,
            "bed-error-compensation-2026-11-01-dense-v3-360mm-reach-extrapolated.json",
        )

    def test_scaled_ink_layers_share_the_page_frame(self):
        tab = self.make_tab(FakeHost(self.colour_path))
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.scale_pct.setValue(280)
        tab.registration_marks.setChecked(False)
        tab._ensure_layers()
        settings = tab._effective_settings()
        expected = (tab.page_w.value() / 2.0, tab.page_h.value() / 2.0)
        scaled_radii = {}
        for channel in converter.CHANNELS:
            contours = converter.read_svg(
                str(tab._layer_files[channel]), settings
            )
            plan = converter.plan_program(contours, settings)
            anchor = plan["source_center"]
            self.assertAlmostEqual(anchor[0], expected[0], places=6, msg=channel)
            self.assertAlmostEqual(anchor[1], expected[1], places=6, msg=channel)
            if plan["contours"]:
                scaled_radii[channel] = max(
                    math.hypot(x, y)
                    for contour in plan["contours"]
                    for x, y in contour
                )

        # The Artwork scale control still sizes the print: 280 % must draw
        # appreciably larger than 100 % while both stay in one frame.
        tab.scale_pct.setValue(100)
        tab._ensure_layers()
        settings = tab._effective_settings()
        plain_radii = []
        for channel in converter.CHANNELS:
            contours = converter.read_svg(
                str(tab._layer_files[channel]), settings
            )
            plan = converter.plan_program(contours, settings)
            if plan["contours"]:
                plain_radii.append(
                    max(
                        math.hypot(x, y)
                        for contour in plan["contours"]
                        for x, y in contour
                    )
                )
        self.assertTrue(scaled_radii)
        self.assertTrue(plain_radii)
        self.assertGreater(max(scaled_radii.values()), 2.0 * max(plain_radii))

    def test_save_writes_one_file_per_ink(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.scale_pct.setValue(260)
        tab._ensure_layers()
        results = {
            channel: {
                "marks": 1,
                "moves": 3,
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "x_count": 1,
                "y_count": 0,
                "x_mm": 1.0,
                "y_mm": 0.0,
                "draw_mm": 1.0,
                "seconds": 1.0,
            }
            for channel in converter.CHANNELS
        }
        tab._analysis = results
        tab._analysis_key = tab._control_key()
        tab._write_files(results)
        self.assertEqual(host.saved_labels, ["cyan", "magenta", "yellow", "black"])
        self.assertEqual(len(set(host.saved_paths.values())), 4)
        manifest = Path(host.saved_paths["cyan"]).with_name(
            "art-cmyk-set.json"
        )
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(
            data["screen"]["flow_guide"],
            "strength_gated_luminance_structure_tensor_"
            "per_ink_networks_continuous_tone",
        )
        self.assertEqual(
            data["screen"]["edge_flow_path_network"],
            "per_ink",
        )
        for channel in converter.CHANNELS:
            self.assertTrue(
                Path(host.saved_paths[converter.CHANNEL_LABELS[channel].lower()]).exists()
            )

    def test_preview_loads_every_layer_and_filters_live(self):
        tab = self.make_tab()
        tab.build_svg()
        # Every layer is loaded; the checkboxes only drive the live filter.
        self.assertEqual(
            [ink for ink, _path in tab.preview_layers()], list(converter.CHANNELS)
        )
        tab.preview_boxes["m"].setChecked(False)
        tab.build_svg()
        self.assertEqual(
            [ink for ink, _path in tab.preview_layers()], list(converter.CHANNELS)
        )
        self.assertEqual(tab.preview_visible_inks(), ["c", "y", "k"])

    def test_preview_toggle_notifies_the_host_live(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab.preview_boxes["m"].setChecked(False)
        self.assertEqual(host.visibility_updates, 1)
        tab.preview_boxes["m"].setChecked(True)
        self.assertEqual(host.visibility_updates, 2)

    def test_shipped_defaults_suit_a_photo(self):
        tab = self.CmykTab(FakeHost(self.image_path))
        self.addCleanup(tab.deleteLater)
        self.assertFalse(tab.auto_levels.isChecked())
        self.assertFalse(tab.solid_dots.isChecked())
        self.assertEqual(tab.style.currentData(), "edge_flow")
        self.assertEqual(tab.levels.value(), 8)
        self.assertAlmostEqual(tab.pitch.value(), 0.45, places=3)
        self.assertAlmostEqual(tab.flow_smoothing.value(), 2.5, places=3)
        self.assertEqual(tab.flow_layers.value(), 3)
        self.assertFalse(tab.flow_keylines.isChecked())
        self.assertAlmostEqual(tab.path_tolerance.value(), 0.10, places=3)
        self.assertAlmostEqual(tab.gcr.value(), 75.0, places=3)
        self.assertAlmostEqual(tab.saturation.value(), 115.0, places=3)
        self.assertAlmostEqual(tab.contrast.value(), 150.0, places=3)
        self.assertAlmostEqual(tab.brightness.value(), 115.0, places=3)
        self.assertTrue(tab.sharpen.isChecked())
        self.assertAlmostEqual(tab.sharpen_amount.value(), 60.0, places=3)
        self.assertAlmostEqual(tab.sharpen_radius.value(), 1.5, places=3)
        self.assertAlmostEqual(tab.gamma.value(), 1.10, places=2)
        self.assertAlmostEqual(tab.dot_size.value(), 100.0, places=3)
        self.assertEqual(tab.max_marks.value(), 200000)
        self.assertEqual(tab.resolution.value(), 10000)
        self.assertAlmostEqual(tab.scale_pct.value(), 280.0, places=3)
        self.assertAlmostEqual(tab.weight_c.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_m.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_y.value(), 100.0, places=3)
        self.assertAlmostEqual(tab.weight_k.value(), 100.0, places=3)

    def test_reference_pitch_targets_on_paper_spacing(self):
        from generator_tabs.cmyk_tab import reference_photo_pitch_mm

        self.assertAlmostEqual(
            reference_photo_pitch_mm(0.9, 200.0),
            0.90,
            places=3,
        )
        self.assertAlmostEqual(
            reference_photo_pitch_mm(2.0, 200.0),
            2.00,
            places=3,
        )

    def test_reference_pitch_keeps_open_hatching_for_large_pens(self):
        from generator_tabs.cmyk_tab import reference_photo_pitch_mm

        effective_pitch = reference_photo_pitch_mm(0.9, 200.0) * 2.0
        self.assertGreaterEqual(effective_pitch, 1.80)

    def test_reference_defaults_apply_the_complete_photo_recipe(self):
        host = FakeHost(self.image_path)
        tab = self.CmykTab(host)
        self.addCleanup(tab.deleteLater)
        tab.scale_pct.setValue(200)
        tab.pen_width.setValue(0.9)
        tab.page_w.setValue(180)
        tab.page_h.setValue(220)
        tab.offset_spins["c"][0].setValue(1.25)
        tab.offset_spins["c"][1].setValue(-2.5)
        tab.offset_spins["k"][0].setValue(3.0)
        tab.offset_spins["k"][1].setValue(4.0)
        tab.chain_gap.setValue(8.0)
        tab.theta_mode.set_value("fixed")
        values = {
            "auto_levels": False,
            "saturation": 115,
            "contrast": 150,
            "brightness": 115,
            "gamma": 1.1,
            "gcr": 75,
            "weights": {"c": 100, "m": 100, "y": 100, "k": 100},
            "sharpen": True,
            "sharpen_pct": 60,
            "sharpen_radius_mm": 1.5,
            "predicted_rgb_error": 52.8,
        }

        with mock.patch.object(
            converter,
            "auto_photo_settings",
            return_value=values,
        ):
            tab.apply_reference_defaults()

        self.assertEqual(tab.style.currentData(), "edge_flow")
        self.assertAlmostEqual(tab.flow_smoothing.value(), 2.5, places=1)
        self.assertEqual(tab.flow_layers.value(), 3)
        self.assertFalse(tab.flow_keylines.isChecked())
        self.assertTrue(tab.chain_marks.isChecked())
        self.assertAlmostEqual(tab.chain_gap.value(), 1.0, places=3)
        self.assertAlmostEqual(tab.pitch.value(), 0.90, places=2)
        self.assertAlmostEqual(
            tab.pitch.value() * tab.scale_pct.value() / 100.0,
            1.8,
            places=2,
        )
        self.assertAlmostEqual(tab.path_tolerance.value(), 0.10, places=2)
        self.assertEqual(tab.max_marks.value(), 200000)
        self.assertEqual(tab.saturation.value(), 115)
        self.assertEqual(tab.contrast.value(), 150)
        self.assertEqual(tab.brightness.value(), 115)
        self.assertAlmostEqual(tab.gamma.value(), 1.10, places=2)
        self.assertEqual(tab.gcr.value(), 75)
        self.assertTrue(tab.sharpen.isChecked())
        self.assertEqual(tab.sharpen_amount.value(), 60)
        self.assertAlmostEqual(tab.sharpen_radius.value(), 1.5, places=2)
        self.assertEqual(tab.theta_mode.value(), "fixed")
        self.assertEqual(tab.page_w.value(), 180)
        self.assertEqual(tab.page_h.value(), 220)
        self.assertEqual(tab.scale_pct.value(), 200)
        self.assertAlmostEqual(tab.pen_width.value(), 0.9, places=2)
        self.assertEqual(
            [spin.value() for spin in tab.offset_spins["c"]],
            [1.25, -2.5],
        )
        self.assertEqual(
            [spin.value() for spin in tab.offset_spins["k"]],
            [3.0, 4.0],
        )
        self.assertIn("Recommended photo defaults ready", tab.status.text())
        self.assertIn("Press Preview", tab.status.text())

    def test_sharpening_settings_reach_preparation_and_invalidate_layers(self):
        tab = self.make_tab()
        tab.scale_pct.setValue(200)
        captured = []
        prepare = converter.prepare_image_tones

        def capture_prepare(*args, **kwargs):
            captured.append(dict(kwargs))
            return prepare(*args, **kwargs)

        before = tab._control_key()
        tab.sharpen_amount.setValue(95)
        tab.sharpen_radius.setValue(2.2)
        self.assertNotEqual(before, tab._control_key())
        with (
            mock.patch.object(
                converter,
                "prepare_image_tones",
                side_effect=capture_prepare,
            ),
            mock.patch.object(converter, "screen_channel", return_value=[]),
        ):
            tab._ensure_layers()
            tab.sharpen.setChecked(False)
            tab._ensure_layers()

        self.assertEqual(captured[0]["sharpen_pct"], 95.0)
        self.assertAlmostEqual(
            captured[0]["sharpen_radius_mm"],
            2.2 / 2.0,
            places=6,
        )
        self.assertEqual(captured[1]["sharpen_pct"], 0.0)
        self.assertFalse(tab.sharpen_amount.isEnabled())
        self.assertFalse(tab.sharpen_radius.isEnabled())
        tab.sharpen.setChecked(True)
        self.assertTrue(tab.sharpen_amount.isEnabled())
        self.assertTrue(tab.sharpen_radius.isEnabled())

    def test_resolution_is_not_capped_at_2000(self):
        tab = self.make_tab()
        tab.resolution.setValue(8192)
        self.assertEqual(tab.resolution.value(), 8192)

    def test_artwork_scale_scales_the_screened_marks(self):
        tab = self.make_tab()
        tab.scale_pct.setValue(100)
        tab._ensure_layers()
        full = [
            point
            for channel in converter.CHANNELS
            for line in tab._layers[channel]
            for point in line
        ]
        tab.scale_pct.setValue(50)
        tab._ensure_layers()
        half = [
            point
            for channel in converter.CHANNELS
            for line in tab._layers[channel]
            for point in line
        ]

        def bounds(points):
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            return min(xs), min(ys), max(xs), max(ys)

        full_box = bounds(full)
        half_box = bounds(half)
        self.assertAlmostEqual(
            half_box[2] - half_box[0],
            0.5 * (full_box[2] - full_box[0]),
            delta=0.10,
        )
        self.assertAlmostEqual(
            half_box[3] - half_box[1],
            0.5 * (full_box[3] - full_box[1]),
            delta=0.10,
        )
        self.assertAlmostEqual(
            (half_box[0] + half_box[2]) / 2.0,
            (full_box[0] + full_box[2]) / 2.0,
            delta=1.0,
        )

    def test_artwork_scale_keeps_wave_tolerance_in_paper_space(self):
        tab = self.make_tab(FakeHost(self.colour_path))
        tab.scale_pct.setValue(280)
        tab.path_tolerance.setValue(0.05)
        captured = []
        captured_depth = []
        screen_channel = converter.screen_channel

        def capture_tolerance(*args, **kwargs):
            captured.append(kwargs.get("path_tolerance_mm"))
            captured_depth.append(kwargs.get("depth_tone"))
            return screen_channel(*args, **kwargs)

        with mock.patch.object(
            converter, "screen_channel", side_effect=capture_tolerance
        ):
            tab._ensure_layers()

        self.assertEqual(len(captured), len(converter.CHANNELS))
        for tolerance in captured:
            self.assertAlmostEqual(tolerance, 0.05 / 2.8)
        self.assertTrue(all(depth is not None for depth in captured_depth))

    def test_artwork_scale_keeps_wave_clearance_in_paper_space(self):
        tab = self.make_tab(FakeHost(self.colour_path))
        tab.scale_pct.setValue(280)
        tab.pen_width.setValue(0.8)
        captured = []
        screen_channel = converter.screen_channel

        def capture_clearance(*args, **kwargs):
            captured.append(kwargs.get("row_clearance_mm"))
            return screen_channel(*args, **kwargs)

        with mock.patch.object(
            converter, "screen_channel", side_effect=capture_clearance
        ):
            tab._ensure_layers()

        self.assertEqual(len(captured), len(converter.CHANNELS))
        expected = (
            tab.pen_width.value() + converter.WAVE_MIN_EDGE_GAP_MM
        ) / 2.8
        for clearance in captured:
            self.assertAlmostEqual(clearance, expected)

    def test_hatch_levels_allow_more_families(self):
        tab = self.make_tab()
        tab.levels.setValue(9)
        self.assertEqual(tab.levels.value(), 9)

    def test_pitch_allows_solid_fill_spacing(self):
        tab = self.make_tab()
        tab.pitch.setValue(0.2)
        self.assertEqual(tab.pitch.value(), 0.2)

    def test_auto_button_applies_photo_settings(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab.saturation.setValue(100)
        tab.contrast.setValue(100)
        tab.brightness.setValue(100)
        tab.gamma.setValue(1.0)
        tab.gcr.setValue(100)
        tab.scale_pct.setValue(150)
        pitch_before = tab.pitch.value()
        tab.auto_button.click()
        values = converter.auto_photo_settings(
            self.image_path,
            pen_width_mm=tab.pen_width.value(),
            effective_pitch_mm=(
                tab.pitch.value() * tab.scale_pct.value() / 100.0
            ),
            style=tab.style.currentData(),
            dot_pitch_mm=tab.pitch.value(),
        )
        self.assertEqual(tab.saturation.value(), values["saturation"])
        self.assertEqual(tab.contrast.value(), values["contrast"])
        self.assertEqual(tab.brightness.value(), values["brightness"])
        self.assertEqual(tab.gcr.value(), values["gcr"])
        self.assertAlmostEqual(tab.gamma.value(), values["gamma"], places=2)
        self.assertEqual(tab.weight_y.value(), values["weights"]["y"])
        self.assertTrue(tab.auto_levels.isChecked())
        # Auto no longer touches Dot pitch: the operator's spacing choice
        # stands; the status line suggests what Match pen would set instead.
        self.assertAlmostEqual(tab.pitch.value(), pitch_before, places=3)
        self.assertIn("Auto:", tab.status.text())
        self.assertIn("coverage RGB error estimate", tab.status.text())
        self.assertIn("Dot pitch", tab.status.text())
        self.assertIn("Match pen would suggest", tab.status.text())

    def test_auto_button_applies_wave_photo_fidelity_settings(self):
        host = FakeHost(self.colour_path)
        tab = self.make_tab(host)
        tab.style.setCurrentIndex(tab.style.findData("waves_even"))
        tab.sharpen.setChecked(False)
        tab.sharpen_amount.setValue(70)
        tab.sharpen_radius.setValue(1.0)
        values = converter.auto_photo_settings(
            self.colour_path,
            pen_width_mm=tab.pen_width.value(),
            effective_pitch_mm=(
                tab.pitch.value() * tab.scale_pct.value() / 100.0
            ),
            style="waves_even",
            dot_pitch_mm=tab.pitch.value(),
        )

        tab.auto_button.click()

        self.assertEqual(tab.saturation.value(), values["saturation"])
        self.assertEqual(tab.contrast.value(), values["contrast"])
        self.assertEqual(tab.brightness.value(), values["brightness"])
        self.assertEqual(tab.gcr.value(), values["gcr"])
        self.assertAlmostEqual(tab.gamma.value(), values["gamma"], places=2)
        self.assertEqual(tab.weight_y.value(), values["weights"]["y"])
        self.assertTrue(tab.sharpen.isChecked())
        self.assertEqual(tab.sharpen_amount.value(), values["sharpen_pct"])
        self.assertEqual(
            tab.sharpen_radius.value(),
            values["sharpen_radius_mm"],
        )
        self.assertAlmostEqual(tab.pitch.value(), values["dot_pitch_mm"])

    def test_edge_flow_auto_preserves_the_physical_pitch(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.pitch.setValue(0.31)
        tab.scale_pct.setValue(260)
        tab.resolution.setValue(1600)
        captured = {}
        auto_settings = converter.auto_photo_settings

        def capture_settings(*args, **kwargs):
            captured["values"] = auto_settings(*args, **kwargs)
            captured["kwargs"] = kwargs
            return captured["values"]

        with mock.patch.object(
            converter,
            "auto_photo_settings",
            side_effect=capture_settings,
        ):
            tab.auto_button.click()
        values = captured["values"]

        self.assertEqual(tab.contrast.value(), values["contrast"])
        self.assertEqual(tab.brightness.value(), values["brightness"])
        self.assertAlmostEqual(tab.gamma.value(), values["gamma"], places=2)
        self.assertEqual(tab.weight_y.value(), values["weights"]["y"])
        self.assertAlmostEqual(tab.pitch.value(), 0.31, places=3)
        self.assertEqual(
            captured["kwargs"]["resolution_px"],
            1600,
        )
        self.assertEqual(
            captured["kwargs"]["flow_layers"],
            tab.flow_layers.value(),
        )
        self.assertIn("Dot pitch left at 0.31 mm", tab.status.text())

    def test_match_pen_pitch_uses_the_effective_scale(self):
        tab = self.make_tab()
        tab.scale_pct.setValue(200)
        tab.pen_width.setValue(0.3)
        tab.match_pen_pitch()
        self.assertAlmostEqual(tab.pitch.value(), 0.15, places=2)
        self.assertIn("matches", tab.status.text())

    def test_fine_detail_preset_scales_edge_flow_to_the_pen(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.pen_width.setValue(0.6)
        tab.scale_pct.setValue(260)
        tab.flow_smoothing.setValue(4.0)
        tab.flow_layers.setValue(5)
        tab.path_tolerance.setValue(0.15)
        self.assertFalse(tab.detail_button.isChecked())
        self.assertEqual(tab.detail_button.text(), "Fine detail")

        tab.detail_button.click()

        self.assertTrue(tab.detail_button.isChecked())
        self.assertIn("✓", tab.detail_button.text())
        self.assertAlmostEqual(tab.pitch.value(), 0.25, places=2)
        self.assertAlmostEqual(
            tab.pitch.value() * tab.scale_pct.value() / 100.0,
            0.65,
            places=2,
        )
        self.assertAlmostEqual(tab.flow_smoothing.value(), 1.2, places=1)
        self.assertEqual(tab.flow_layers.value(), 5)
        self.assertTrue(tab.flow_keylines.isChecked())
        self.assertTrue(tab.sharpen.isChecked())
        self.assertAlmostEqual(tab.sharpen_amount.value(), 60.0, places=1)
        self.assertAlmostEqual(tab.sharpen_radius.value(), 1.5, places=1)
        self.assertAlmostEqual(tab.path_tolerance.value(), 0.10, places=2)
        self.assertIn("Fine detail", tab.status.text())

        tab.pen_width.setValue(0.8)
        tab.scale_pct.setValue(150)
        self.assertFalse(tab.detail_button.isChecked())
        tab.detail_button.click()
        self.assertTrue(tab.detail_button.isChecked())
        self.assertAlmostEqual(tab.pitch.value(), 0.55, places=2)
        self.assertAlmostEqual(tab.flow_smoothing.value(), 1.5, places=1)
        self.assertEqual(tab.flow_layers.value(), 5)

    def test_fine_detail_indicator_clears_when_layout_is_edited(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.pen_width.setValue(0.6)
        tab.scale_pct.setValue(260)

        tab.detail_button.click()
        self.assertTrue(tab.detail_button.isChecked())
        self.assertIn("active", tab.detail_button.toolTip())

        tab.flow_smoothing.setValue(2.4)
        self.assertFalse(tab.detail_button.isChecked())
        self.assertEqual(tab.detail_button.text(), "Fine detail")
        self.assertIn("not active", tab.detail_button.toolTip())

        tab.detail_button.click()
        self.assertTrue(tab.detail_button.isChecked())
        tab.flow_keylines.setChecked(False)
        self.assertFalse(tab.detail_button.isChecked())

        tab.detail_button.click()
        self.assertTrue(tab.detail_button.isChecked())
        tab.sharpen_amount.setValue(40.0)
        self.assertFalse(tab.detail_button.isChecked())

    def test_fine_detail_toggle_restores_previous_controls(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.pen_width.setValue(0.6)
        tab.scale_pct.setValue(260)
        tab.pitch.setValue(0.65)
        tab.flow_smoothing.setValue(4.0)
        tab.flow_layers.setValue(5)
        tab.path_tolerance.setValue(0.15)
        tab.flow_keylines.setChecked(False)
        tab.sharpen.setChecked(False)

        tab.detail_button.click()
        self.assertTrue(tab.detail_button.isChecked())

        tab.detail_button.click()
        self.assertFalse(tab.detail_button.isChecked())
        self.assertEqual(tab.style.currentData(), "edge_flow")
        self.assertAlmostEqual(tab.pitch.value(), 0.65, places=2)
        self.assertAlmostEqual(tab.flow_smoothing.value(), 4.0, places=1)
        self.assertEqual(tab.flow_layers.value(), 5)
        self.assertAlmostEqual(tab.path_tolerance.value(), 0.15, places=2)
        self.assertFalse(tab.flow_keylines.isChecked())
        self.assertFalse(tab.sharpen.isChecked())
        self.assertIn("Fine detail off", tab.status.text())

    def test_fine_detail_toggle_snapshot_round_trips(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.pen_width.setValue(0.6)
        tab.scale_pct.setValue(260)
        tab.flow_smoothing.setValue(4.0)
        tab.flow_layers.setValue(5)
        tab.path_tolerance.setValue(0.15)
        tab.flow_keylines.setChecked(False)
        tab.sharpen.setChecked(False)
        tab.detail_button.click()

        state = tab.artwork_layout_state()
        self.assertIsNotNone(state["fine_detail_previous"])
        restored = self.make_tab()
        self.assertTrue(restored.restore_artwork_layout_state(state))
        self.assertTrue(restored.detail_button.isChecked())

        restored.detail_button.click()
        self.assertFalse(restored.detail_button.isChecked())
        self.assertAlmostEqual(restored.flow_smoothing.value(), 4.0, places=1)
        self.assertEqual(restored.flow_layers.value(), 5)
        self.assertFalse(restored.flow_keylines.isChecked())
        self.assertFalse(restored.sharpen.isChecked())

    def test_fine_detail_old_active_recipe_uses_off_fallback(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.pen_width.setValue(0.6)
        tab.scale_pct.setValue(260)
        tab.detail_button.click()
        state = tab.artwork_layout_state()
        state["fine_detail_previous"] = None

        restored = self.make_tab()
        self.assertTrue(restored.restore_artwork_layout_state(state))
        self.assertTrue(restored.detail_button.isChecked())
        restored.detail_button.click()

        self.assertFalse(restored.detail_button.isChecked())
        self.assertAlmostEqual(restored.flow_smoothing.value(), 2.5, places=1)
        self.assertEqual(restored.flow_layers.value(), 3)
        self.assertAlmostEqual(restored.path_tolerance.value(), 0.15, places=2)
        self.assertFalse(restored.flow_keylines.isChecked())
        self.assertFalse(restored.sharpen.isChecked())
        self.assertIn("standard Edge-flow defaults", restored.status.text())

    def test_old_fine_detail_snapshot_without_sharpen_fields_restores(self):
        tab = self.make_tab()
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.pen_width.setValue(0.6)
        tab.scale_pct.setValue(260)
        tab.sharpen.setChecked(False)
        tab.detail_button.click()
        state = tab.artwork_layout_state()
        previous = state["fine_detail_previous"]
        previous.pop("sharpen")
        previous.pop("sharpen_pct")
        previous.pop("sharpen_radius_mm")

        restored = self.make_tab()
        self.assertTrue(restored.restore_artwork_layout_state(state))
        restored.detail_button.click()

        self.assertFalse(restored.detail_button.isChecked())
        self.assertFalse(restored.sharpen.isChecked())
        self.assertNotIn("unavailable", restored.status.text())

    def test_registration_crosses_are_identical_on_every_ink(self):
        tab = self.make_tab()
        tab.registration_marks.setChecked(True)
        tab._ensure_layers()
        crosses = tab._registration_crosses()
        self.assertEqual(len(crosses), 8)
        for channel in converter.CHANNELS:
            self.assertEqual(tab._layers[channel][-8:], crosses, channel)
        tab.registration_marks.setChecked(False)
        tab._ensure_layers()
        for channel in converter.CHANNELS:
            self.assertNotEqual(tab._layers[channel][-8:], crosses, channel)

    def test_max_marks_is_not_capped_at_40000(self):
        tab = self.make_tab()
        tab.max_marks.setValue(80000)
        self.assertEqual(tab.max_marks.value(), 80000)

    def test_preview_defers_exact_planning_until_save(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        self.assertFalse(hasattr(tab, "analyze_button"))
        calls = []
        tab.start_analysis = lambda: calls.append("plan")
        tab.on_preview_finished()
        self.assertEqual(calls, [])
        self.assertIn("when you save", tab.cost_label.text())
        self.assertIn("when you save", host.status[-1])

    def test_save_starts_deferred_exact_planning(self):
        tab = self.make_tab()
        tab._write_channels = lambda: ["k"]
        calls = []
        tab.start_analysis = lambda: calls.append("plan")
        tab.save_all()
        self.assertEqual(calls, ["plan"])
        self.assertTrue(tab._pending_save)
        self.assertIn("before save", tab.status.text())

    def test_planning_state_reaches_the_shared_cancel_control(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab._set_planning_state(True)
        self.assertTrue(tab.cancel_button.isEnabled())
        self.assertFalse(tab.save_button.isEnabled())
        self.assertEqual(host.planning_states[-1], (tab, True))

        tab._set_planning_state(False)
        self.assertFalse(tab.cancel_button.isEnabled())
        self.assertTrue(tab.save_button.isEnabled())
        self.assertEqual(host.planning_states[-1], (tab, False))

    def test_calibration_sheet_mode_builds_and_saves_manifest(self):
        host = FakeHost(self.image_path)
        tab = self.make_tab(host)
        tab.calibration_mode.setChecked(True)
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        path = tab.build_svg()
        root = ET.parse(path).getroot()
        self.assertEqual(svg_groups(root), list(converter.CHANNELS))
        self.assertIsNotNone(tab._layers_manifest)
        self.assertGreater(len(tab._layers_manifest["patches"]), 80)
        results = {
            channel: {
                "marks": 1,
                "moves": 3,
                "gcode": f"; {channel}\nG1 X0 Y0\n",
                "lines": 2,
                "x_count": 1,
                "y_count": 0,
                "x_mm": 1.0,
                "y_mm": 0.0,
                "draw_mm": 1.0,
                "seconds": 1.0,
            }
            for channel in converter.CHANNELS
        }
        tab._analysis = results
        tab._analysis_key = tab._control_key()
        tab._write_files(results)
        manifest_path = Path(host.saved_paths["cyan"]).with_name(
            "art-cmyk-calibration.json"
        )
        self.assertTrue(manifest_path.exists())
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data["kind"], "cmyk-calibration-sheet")
        self.assertIn("Calibration manifest", tab.status.text())

    def test_calibration_sheet_mode_needs_no_artwork(self):
        tab = self.make_tab(FakeHost(""))
        tab.calibration_mode.setChecked(True)
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        path = tab.build_svg()
        self.assertTrue(Path(path).exists())

    def test_calibration_mode_changes_the_layer_key(self):
        tab = self.make_tab()
        before = tab._control_key()
        tab.calibration_mode.setChecked(True)
        self.assertNotEqual(before, tab._control_key())

    def test_calibration_sheet_reports_small_pages(self):
        tab = self.make_tab()
        tab.calibration_mode.setChecked(True)
        with self.assertRaises(ValueError):
            tab.build_svg()

    def test_calibration_sheet_follows_the_line_screen(self):
        tab = self.make_tab()
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        self.assertEqual(tab.calibration_screen.currentData(), "match")
        tab.style.setCurrentIndex(tab.style.findData("lines"))
        tab.calibration_mode.setChecked(True)
        tab.build_svg()
        self.assertEqual(
            tab._layers_manifest["sheet_settings"]["style"], "lines"
        )
        tab.calibration_screen.setCurrentIndex(
            tab.calibration_screen.findData("halftone")
        )
        tab.build_svg()
        self.assertEqual(
            tab._layers_manifest["sheet_settings"]["style"], "halftone"
        )

    def test_calibration_sheet_follows_the_rectilinear_fill(self):
        tab = self.make_tab()
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        tab.style.setCurrentIndex(tab.style.findData("rectilinear"))
        tab.calibration_mode.setChecked(True)
        tab.build_svg()
        self.assertEqual(
            tab._layers_manifest["sheet_settings"]["style"], "rectilinear"
        )

    def test_calibration_sheet_follows_edge_flow(self):
        tab = self.make_tab()
        tab.page_w.setValue(200)
        tab.page_h.setValue(200)
        tab.pitch.setValue(2.0)
        tab.style.setCurrentIndex(tab.style.findData("edge_flow"))
        tab.calibration_mode.setChecked(True)
        tab.build_svg()
        self.assertEqual(
            tab._layers_manifest["sheet_settings"]["style"], "edge_flow"
        )


class FakeHost:
    """Minimal host: analysis is synthetic, saving writes real temp files."""

    def __init__(self, artwork):
        self._artwork = artwork
        self.status = []
        self.log = []
        self.saved_labels = []
        self.saved_paths = {}
        self.visibility_updates = 0
        self.planning_states = []
        self._folder = tempfile.mkdtemp(prefix="cmyk-save-")

    def artwork_path(self):
        return self._artwork

    def generator_status(self, message):
        self.status.append(message)

    def generator_planning_changed(self, tab, running):
        self.planning_states.append((tab, running))

    def update_preview_visibility(self):
        self.visibility_updates += 1

    def settings_for_source(self, _tab):
        return converter.Settings()

    def motion_estimate_scale(self):
        return converter.DEFAULT_MOTION_ESTIMATE_SCALE

    def analyze_program(self, _path, _settings, cancel_check=None):
        moves = [
            {
                "type": "draw",
                "strategy": "x_theta",
                "motion_length": 2.0,
                "duration_ms": 1000.0,
            },
            {
                "type": "draw",
                "strategy": "x_theta",
                "motion_length": 2.0,
                "duration_ms": 1000.0,
            },
            {
                "type": "draw",
                "strategy": "y_theta",
                "motion_length": 1.0,
                "duration_ms": 500.0,
            },
            {"type": "pen_down", "duration_ms": 600.0},
        ]
        return {
            "contours": [[(0.0, 0.0), (1.0, 1.0)], [(1.0, 1.0), (2.0, 2.0)]],
            "moves": moves,
            "gcode": "; synthetic\nG1 X0 Y0\n",
            "stats": {},
        }

    def export_program_set(self, entries, base_path=None, default_base=""):
        del base_path, default_base
        written = []
        for label, gcode in entries:
            path = str(Path(self._folder) / f"art-cmyk-{label}.gcode")
            Path(path).write_text(gcode, encoding="utf-8")
            self.saved_labels.append(label)
            self.saved_paths[label] = path
            written.append(path)
        return written


if __name__ == "__main__":
    unittest.main()
