"""The tool shell: dashboard navigation, layout, scale, and failure isolation."""

import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover - the app needs Qt, the core does not
    HAVE_QT = False


def _load_app_module():
    path = Path(__file__).resolve().parents[1] / "qt_svg_to_gcode.pyw"
    spec = importlib.util.spec_from_file_location("qt_svg_to_gcode_app", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EXPECTED_TOOLS = [
    "Flow Field",
    "Line Draw",
    "CMYK",
    "3D Wireframe",
    "Harmonograph",
    "Snowflake",
    "Truchet",
    "Text",
    "Substitution",
    "Postcard",
    "SquiggleCam",
    "Pixel Art",
    "Wobble",
    "Plotterfun",
    "Voronoi",
    "Path Prep",
    "Layers",
    "Stipple / TSP",
    "Reaction-Diffusion",
    "Vector Trace",
]


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class ToolShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()

    def test_convert_is_the_default_tool(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        self.assertIs(window.stack.currentWidget(), window.convert_root)
        self.assertEqual(window.current_tool, "Convert")
        self.assertTrue(window.tool_actions["Convert"].isChecked())
        self.assertIs(window.stack.widget(0), window.dashboard)

    def test_menu_bar_has_the_standard_menus(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        titles = [
            action.text().replace("&", "")
            for action in window.menuBar().actions()
        ]
        self.assertEqual(titles, ["File", "Tools", "View", "Help"])

    def test_dashboard_tool_order(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        titles = [title for title, _widget, _group, _desc in window.generator_tools]
        self.assertEqual(titles, EXPECTED_TOOLS)
        self.assertEqual(window.tool_index["Convert"], window.stack.indexOf(window.convert_root))
        for title in EXPECTED_TOOLS:
            self.assertIn(title, window.tool_index)

    def test_tools_are_grouped_by_input_type(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        groups = {}
        for title, _widget, group, _description in window.generator_tools:
            groups.setdefault(group, []).append(title)
        self.assertEqual(
            groups["Photo-based"],
            [
                "Line Draw",
                "CMYK",
                "SquiggleCam",
                "Pixel Art",
                "Plotterfun",
                "Layers",
                "Stipple / TSP",
                "Vector Trace",
            ],
        )
        self.assertEqual(
            groups["Algorithm only"],
            [
                "Flow Field",
                "3D Wireframe",
                "Harmonograph",
                "Snowflake",
                "Truchet",
                "Text",
                "Substitution",
                "Postcard",
                "Wobble",
                "Voronoi",
                "Path Prep",
                "Reaction-Diffusion",
            ],
        )
        submenus = [
            action.text()
            for action in window.tools_menu.actions()
            if action.menu() is not None
        ]
        self.assertEqual(submenus, ["Photo-based", "Algorithm only"])

    def test_tools_menu_switches_pages(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.tool_actions["Flow Field"].trigger()
        self.assertEqual(window.current_tool, "Flow Field")
        self.assertTrue(window.tool_actions["Flow Field"].isChecked())
        flow = dict(
            (title, widget)
            for title, widget, _group, _desc in window.generator_tools
        )["Flow Field"]
        self.assertIs(window.stack.currentWidget(), flow)
        window.all_tools_action.trigger()
        self.assertIs(window.stack.currentWidget(), window.dashboard)
        window.tool_actions["Convert"].trigger()
        self.assertIs(window.stack.currentWidget(), window.convert_root)

    def test_status_bar_shows_the_file_paths(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.svg_path.setText("C:/art/example.svg")
        window.gcode_path.setText("C:/art/example.gcode")
        self.assertIn("example.svg", window.file_status.text())
        self.assertIn("example.gcode", window.file_status.text())

    def test_dashboard_requires_a_tool_for_preview(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.show_tool("All tools")
        with self.assertRaises(ValueError):
            window.resolve_active_source()

    def test_settings_pane_has_no_dead_strip(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.resize(1500, 950)
        window.show()
        self.app.processEvents()
        self.assertLessEqual(
            window.stack.width() - window.sidebar_scroll.width(), 4
        )

    def test_generator_controls_fill_the_settings_pane(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.resize(630, 1000)
        window.show()
        window.show_tool("Flow Field")
        self.app.processEvents()
        tab = window.stack.currentWidget()
        self.assertGreaterEqual(tab.width(), 280)
        # The 6 px margins on each side are the only width the controls leave.
        self.assertLessEqual(tab.width() - tab.controls_scroll.width(), 16)
        self.assertGreaterEqual(
            tab.status.y(), tab.controls_scroll.y() + tab.controls_scroll.height()
        )

    def test_every_generator_tool_has_an_artwork_scale(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        for title, page, _group, _desc in window.generator_tools:
            if title in ("Plotterfun", "Layers"):
                # Plotterfun's controls live inside the embedded page; Layers
                # preserves the source SVG's own dimensions.
                continue
            self.assertTrue(hasattr(page, "scale_pct"), title)
            self.assertEqual(page.scale_pct.value(), 100, title)
            self.assertEqual(page.scale_pct.maximum(), 1000, title)

    def test_every_tool_builds_with_shipped_defaults(self):
        from PIL import Image

        window = self.module.MainWindow()
        self.addCleanup(window.close)
        folder = tempfile.mkdtemp(prefix="tool-defaults-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        image_path = str(Path(folder) / "art.png")
        image = Image.new("RGB", (64, 64), (255, 255, 255))
        for x in range(16, 48):
            for y in range(16, 48):
                image.putpixel((x, y), (0, 0, 0))
        image.save(image_path)
        window.svg_path.setText(image_path)
        svg_path = str(Path(folder) / "art.svg")
        Path(svg_path).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" '
            'viewBox="0 0 64 64"><path d="M8,8 L56,56" stroke="#000000" '
            'fill="none"/></svg>',
            encoding="utf-8",
        )
        window.contours = [
            [(10.0, 10.0), (70.0, 10.0), (70.0, 70.0), (10.0, 70.0), (10.0, 10.0)]
        ]
        for title, page, _group, _desc in window.generator_tools:
            if title == "Plotterfun":
                # Embedded web app; verified by its own vendor/fallback tests.
                continue
            if title == "Reaction-Diffusion":
                page.grid.setValue(48)
                page.steps.setValue(300)
            window.svg_path.setText(svg_path if title == "Layers" else image_path)
            window.show_tool(title)
            # Keep the suite quick; the recommended-settings table documents
            # the full 200 x 200 mm pages.
            for attribute in ("page_w", "page_h"):
                widget = getattr(page, attribute, None)
                if widget is not None:
                    widget.setValue(80)
            try:
                path = page.build_svg()
            except Exception as exc:  # noqa: BLE001 - report which tool failed
                self.fail(f"{title} shipped defaults failed: {exc}")
            ET.parse(path)

    def test_generator_sources_plot_at_manual_1to1(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.show_tool("Flow Field")
        flow = window.stack.currentWidget()
        generator_settings = window.settings_for_source(flow)
        self.assertEqual(generator_settings.fit_mode, "manual")
        self.assertEqual(generator_settings.scale, 1.0)
        convert_settings = window.settings_for_source(window.convert_root)
        self.assertEqual(convert_settings.fit_mode, window.settings().fit_mode)

    def test_self_screened_tools_stop_the_fill_pass(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.show_tool("CMYK")
        tab = window.stack.currentWidget()
        self.assertTrue(getattr(tab, "SELF_SCREENED", False))
        settings = window.settings_for_source(tab)
        self.assertEqual(settings.hatch_spacing_mm, 0.0)
        # The Convert tab keeps its own fill setting untouched.
        window.fields["hatch_spacing_mm"].setText("3")
        self.assertGreater(window.settings_for_source(window.convert_root).hatch_spacing_mm, 0.0)

    def test_export_program_set_writes_one_file_per_entry(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        folder = tempfile.mkdtemp(prefix="export-set-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        base = str(Path(folder) / "art-cmyk.gcode")
        written = window.export_program_set(
            [("cyan", "G1 X0\n"), ("black", "G1 X1\n")], base_path=base
        )
        self.assertEqual(
            [Path(path).name for path in written],
            ["art-cmyk-cyan.gcode", "art-cmyk-black.gcode"],
        )
        self.assertEqual(Path(written[0]).read_text(encoding="utf-8"), "G1 X0\n")

    def test_ink_vertex_colors_follow_contour_tags(self):
        import converter_core as converter

        undrawn = self.module.ink_color_floats(
            converter.CHANNEL_COLORS["c"], undrawn_mix=0.55
        )
        full = self.module.ink_color_floats(converter.CHANNEL_COLORS["c"])
        contours = converter.tag_ink([[(0.0, 0.0), (1.0, 0.0)]], "c")
        moves = [
            {
                "type": "draw",
                "strategy": "x_theta",
                "contour": 0,
                "bed_start": (0.0, 0.0),
                "bed_end": (1.0, 0.0),
            }
        ]
        artwork_colors, drawn_colors = self.module.ink_vertex_colors(contours, moves)
        self.assertEqual(len(artwork_colors), 8)  # 2 vertices x RGBA
        self.assertEqual(len(drawn_colors), 8)
        self.assertEqual(artwork_colors[:4], list(undrawn))
        self.assertEqual(drawn_colors[:4], list(full))
        self.assertNotEqual(artwork_colors[:4], drawn_colors[:4])
        # Untagged artwork keeps the single-colour preview.
        self.assertEqual(
            self.module.ink_vertex_colors([[(0.0, 0.0), (1.0, 0.0)]], moves),
            (None, None),
        )

    def test_cmyk_preview_contours_carry_ink_tags(self):
        import converter_core as converter
        from PIL import Image

        window = self.module.MainWindow()
        self.addCleanup(window.close)
        folder = tempfile.mkdtemp(prefix="cmyk-preview-tags-")
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        image_path = str(Path(folder) / "inks.png")
        image = Image.new("RGB", (40, 40), (255, 255, 255))
        for x in range(0, 20):
            for y in range(0, 20):
                image.putpixel((x, y), (0, 255, 255))      # cyan
            for y in range(20, 40):
                image.putpixel((x, y), (255, 0, 255))      # magenta
        for x in range(20, 40):
            for y in range(0, 20):
                image.putpixel((x, y), (255, 255, 0))      # yellow
            for y in range(20, 40):
                image.putpixel((x, y), (0, 0, 0))          # black
        image.save(image_path)
        window.svg_path.setText(image_path)
        window.show_tool("CMYK")
        tab = window.stack.currentWidget()
        tab.page_w.setValue(40)
        tab.page_h.setValue(40)
        tab.margin.setValue(4)
        tab.pitch.setValue(4.0)
        tab.max_marks.setValue(300)
        path, source = window.resolve_active_source()
        self.assertIs(source, tab)
        window.pending_source_tab = tab
        contours = window.load_preview_contours(
            path, window.settings_for_source(tab)
        )
        self.assertEqual(
            {getattr(contour, "ink", None) for contour in contours},
            set(converter.CHANNELS),
        )

    def test_gl_preview_builds_buffers_for_ink_colors(self):
        import converter_core as converter

        window = self.module.MainWindow()
        self.addCleanup(window.close)
        contours = converter.tag_ink([[(0.0, 0.0), (1.0, 0.0)]], "c") + (
            converter.tag_ink([[(0.0, 1.0), (1.0, 1.0)]], "k")
        )
        moves = [
            {
                "type": "draw",
                "strategy": "y_theta",
                "contour": index,
                "bed_start": (0.0, float(index)),
                "bed_end": (1.0, float(index)),
                "duration_ms": 100.0,
            }
            for index in range(2)
        ]
        window.gl_preview.set_preview(
            contours, moves, converter.Settings(), center=(0.0, 0.0)
        )
        self.assertIn("artwork_color", window.gl_preview.vertex_arrays)
        self.assertEqual(window.gl_preview.color_vertex_counts["artwork"], 4)
        self.assertEqual(window.gl_preview.color_vertex_counts["drawn_path"], 4)
        # Untagged artwork keeps the uniform single-colour preview.
        window.gl_preview.set_preview(
            [[(0.0, 0.0), (1.0, 0.0)]], moves[:1], converter.Settings(), center=(0.0, 0.0)
        )
        self.assertNotIn("artwork_color", window.gl_preview.vertex_arrays)

    def test_preview_shaders_compile_when_gl_is_available(self):
        from PySide6.QtGui import QOffscreenSurface, QOpenGLContext
        from PySide6.QtOpenGL import QOpenGLShader, QOpenGLShaderProgram

        context = QOpenGLContext()
        if not context.create():
            self.skipTest("no OpenGL context on this platform")
        surface = QOffscreenSurface()
        surface.create()
        if not context.makeCurrent(surface):
            self.skipTest("offscreen OpenGL surface unavailable")
        program = QOpenGLShaderProgram()
        self.assertTrue(
            program.addShaderFromSourceCode(
                QOpenGLShader.Vertex, self.module.PREVIEW_VERTEX_SHADER
            )
        )
        self.assertTrue(
            program.addShaderFromSourceCode(
                QOpenGLShader.Fragment, self.module.PREVIEW_FRAGMENT_SHADER
            )
        )
        program.bindAttributeLocation("p", 0)
        program.bindAttributeLocation("ink_color", 1)
        self.assertTrue(program.link(), program.log())
        self.assertGreaterEqual(program.uniformLocation("use_vertex_color"), 0)

    def test_preview_finished_hook_runs_for_the_previewed_tab(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.show_tool("CMYK")
        tab = window.stack.currentWidget()
        calls = []
        tab.on_preview_finished = lambda: calls.append("planned")
        window.preview_tab = tab
        window.preview_succeeded = True
        window.preview_thread_finished()
        self.assertEqual(calls, ["planned"])
        # A failed or cancelled preview must not start background planning.
        window.preview_succeeded = False
        window.preview_thread_finished()
        self.assertEqual(calls, ["planned"])

    def test_artwork_scale_survives_the_generator_pipeline(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.show_tool("Flow Field")
        flow = window.stack.currentWidget()
        flow.page_w.setValue(120)
        flow.page_h.setValue(120)
        flow.spacing.setValue(8.0)
        flow.step.setValue(2.0)
        flow.max_steps.setValue(40)
        flow.scale.setValue(20)
        flow.margin.setValue(4)

        def drawn_width():
            path, _tab = window.resolve_active_source()
            contours = window.load_contours(
                path, window.settings_for_source(flow)
            )
            xs = [point[0] for contour in contours for point in contour]
            return max(xs) - min(xs)

        full = drawn_width()
        flow.scale_pct.setValue(50)
        half = drawn_width()
        self.assertAlmostEqual(half / full, 0.5, delta=0.05)

    def test_import_export_and_preview_stay_outside_the_tools(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        for widget in (
            window.preview_button,
            window.gl_preview,
            window.slider,
        ):
            self.assertFalse(
                window.stack.isAncestorOf(widget),
                f"{widget} is hidden with the tool page it lives in",
            )

    def test_preview_and_cancel_live_in_the_preview_panel(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        self.assertTrue(window.preview_panel.isAncestorOf(window.preview_button))
        self.assertTrue(
            window.preview_panel.isAncestorOf(window.cancel_preview_button)
        )
        self.assertTrue(hasattr(window, "save_action"))

    def test_command_list_is_removed_and_preview_fills_the_rest(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        self.assertFalse(hasattr(window, "command_list"))
        self.assertEqual(window.main_split.count(), 2)
        self.assertIs(window.main_split.widget(0), window.stack)
        self.assertIs(window.main_split.widget(1), window.preview_panel)
        window.resize(1500, 950)
        window.show()
        self.app.processEvents()
        tools_width, preview_width = window.main_split.sizes()
        self.assertLessEqual(tools_width, 420)
        self.assertGreater(preview_width, tools_width * 2)

    def test_resolve_active_source_returns_the_convert_artwork(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        handle = tempfile.NamedTemporaryFile(
            suffix=".svg", delete=False, mode="w", encoding="utf-8"
        )
        handle.write('<svg xmlns="http://www.w3.org/2000/svg"/>')
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        window.svg_path.setText(handle.name)
        path, tab = window.resolve_active_source()
        self.assertEqual(path, handle.name)
        self.assertIs(tab, window.convert_root)

    def test_switching_tools_marks_the_preview_stale(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.moves = [{"gcode": "G1"}]
        window.preview_tab = window.convert_root
        window.show_tool("Flow Field")
        self.assertTrue(window.tab_preview_stale)
        self.assertFalse(window.stale_warning.isHidden())
        window.show_tool("Convert")
        self.assertFalse(window.tab_preview_stale)
        self.assertTrue(window.stale_warning.isHidden())

    def test_generator_svg_runs_through_the_converter_pipeline(self):
        window = self.module.MainWindow()
        self.addCleanup(window.close)
        window.show_tool("Flow Field")
        flow = window.stack.currentWidget()
        flow.page_w.setValue(60)
        flow.page_h.setValue(60)
        flow.spacing.setValue(8.0)
        flow.step.setValue(2.0)
        flow.max_steps.setValue(40)
        flow.scale.setValue(20)
        flow.margin.setValue(4)
        path, tab = window.resolve_active_source()
        self.assertIs(tab, flow)
        contours = window.load_contours(path, window.settings())
        self.assertGreater(len(contours), 0)


if __name__ == "__main__":
    unittest.main()
