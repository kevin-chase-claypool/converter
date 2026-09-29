"""Fill defaults, fill-source resolution, and fill region reporting.

Fill is on by default and resolves its own source, so the user does not have to
know whether an SVG is better hatched from its vector shapes or from its
rendered pixels.
"""

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


def _write_svg(body):
    folder = tempfile.mkdtemp()
    path = Path(folder) / "case.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
        'viewBox="0 0 100 100">' + body + "</svg>",
        encoding="utf-8",
    )
    return path


class FillSourceTests(unittest.TestCase):
    def test_fill_is_on_by_default(self):
        settings = converter.Settings()
        self.assertGreater(
            settings.hatch_spacing_mm,
            0.0,
            "fill must be on out of the box; 0 is the explicit outline-only setting",
        )
        self.assertEqual(settings.fill_source, "auto")

    def test_auto_uses_shapes_for_filled_and_for_line_art(self):
        filled = _write_svg('<rect x="10" y="10" width="80" height="80" fill="black"/>')
        line_art = _write_svg(
            '<g fill="none" stroke="#000" stroke-width="0.7">'
            '<rect x="10" y="10" width="80" height="80"/></g>'
        )
        for path in (filled, line_art):
            self.assertEqual(
                converter.resolve_fill_source(converter.Settings(), str(path)),
                "shapes",
                f"{path.name} should hatch from its own shapes",
            )

    def test_auto_switches_to_tone_for_embedded_images_and_gradients(self):
        image = _write_svg(
            '<image x="0" y="0" width="100" height="100" '
            'href="data:image/png;base64,iVBORw0KGgo="/>'
        )
        gradient = _write_svg(
            '<defs><linearGradient id="g"><stop offset="0" stop-color="#fff"/>'
            '<stop offset="1" stop-color="#000"/></linearGradient></defs>'
            '<rect x="10" y="10" width="80" height="80" fill="url(#g)"/>'
        )
        for path in (image, gradient):
            self.assertEqual(
                converter.resolve_fill_source(converter.Settings(), str(path)),
                "tone",
                f"{path.name} carries tone the vector path cannot see",
            )

    def test_explicit_fill_source_overrides_auto(self):
        image = _write_svg(
            '<image x="0" y="0" width="100" height="100" '
            'href="data:image/png;base64,iVBORw0KGgo="/>'
        )
        forced = converter.Settings(fill_source="shapes")
        self.assertEqual(converter.resolve_fill_source(forced, str(image)), "shapes")

    def test_fill_source_must_be_known(self):
        with self.assertRaises(ValueError):
            converter.validate_settings(converter.Settings(fill_source="pixels"))

    def test_open_line_art_reports_no_fillable_region(self):
        # The plotter-ready exports are open segments: nothing bounds an
        # interior, so fill must not invent one.
        open_art = _write_svg(
            '<g fill="none" stroke="#000" stroke-width="0.05">'
            '<path d="M 10 10 L 90 10 M 10 10 L 10 90"/></g>'
        )
        sources = converter.svg_fill_sources(str(open_art))
        self.assertEqual(sources["filled"], 0)
        self.assertEqual(sources["outline"], 1)
        self.assertEqual(sources["image"], 0)

        settings = converter.Settings(
            hatch_spacing_mm=4.0,
            hatch_pattern="linear",
            compensate_pen_width=False,
            flip_y=False,
        )
        stats = {"fill_contours": 0}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "case.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
                'viewBox="0 0 100 100"><g fill="none" stroke="#000" stroke-width="0.05">'
                '<path d="M 10 10 L 90 10 M 10 10 L 10 90"/></g></svg>',
                encoding="utf-8",
            )
            converter.parse_svg_geometry(
                str(path),
                0.25,
                False,
                float(settings.hatch_spacing_mm),
                45.0,
                settings.hatch_pattern,
                int(settings.shade_levels),
                90.0,
                False,
                0.0,
                None,
                None,
                scale=1.0,
                pen_diameter=0.3,
                stats=stats,
            )
        self.assertEqual(stats["fill_contours"], 0)

    def test_closed_outline_reports_fill_contours(self):
        path = _write_svg(
            '<g fill="none" stroke="#000" stroke-width="0.05">'
            '<path d="M 10 10 L 90 10 L 90 90 L 10 90 Z"/></g>'
        )
        stats = {"fill_contours": 0}
        converter.parse_svg_geometry(
            str(path),
            0.25,
            False,
            4.0,
            45.0,
            "linear",
            1,
            90.0,
            False,
            0.0,
            None,
            None,
            scale=1.0,
            pen_diameter=0.3,
            stats=stats,
        )
        self.assertGreater(stats["fill_contours"], 0)


if __name__ == "__main__":
    unittest.main()
