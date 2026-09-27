"""Regression tests for SVG presentation-attribute inheritance.

The converter used to read presentation values from the element alone. A
wrapper such as ``<g fill="none" stroke="#000" stroke-width="0.7">`` therefore
did not reach its children, every child fell back to the SVG initial fill of
black, and outline paths were treated as solid filled regions whose interiors
were hatched. These tests pin the inherited behaviour.
"""

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import converter_core as converter


SAMPLES = Path(__file__).resolve().parents[2] / "samples" / "svg"


def _settings(**overrides):
    values = dict(
        hatch_spacing_mm=4.0,
        hatch_angle_deg=0.0,
        hatch_pattern="linear",
        shade_levels=1,
        scale=1.0,
        flip_y=False,
        tolerance=0.25,
        pen_diameter_mm=0.3,
        compensate_pen_width=False,
    )
    values.update(overrides)
    return converter.Settings(**values)


def _read_svg(body, **overrides):
    """Parse a one-off SVG document body and return its contours."""
    document = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
        'viewBox="0 0 100 100">' + body + "</svg>"
    )
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "case.svg"
        path.write_text(document, encoding="utf-8")
        return converter.read_svg(str(path), _settings(**overrides))


def _hatch_lines(contours):
    """Contours emitted as straight lattice passes are two-point segments."""
    return [contour for contour in contours if len(contour) == 2]


class SvgStyleInheritanceTests(unittest.TestCase):
    def test_group_fill_none_reaches_its_children(self):
        contours = _read_svg(
            '<g fill="none" stroke="#000000" stroke-width="0.7">'
            '<polyline points="10,10 90,10 90,90 10,90 10,10"/>'
            "</g>"
        )

        self.assertTrue(contours, "the stroked outline must still be drawn")
        self.assertEqual(
            _hatch_lines(contours),
            [],
            "a group that declares fill=\"none\" must not be hatched",
        )

    def test_group_fill_black_still_hatches(self):
        contours = _read_svg(
            '<g fill="black"><rect x="10" y="10" width="80" height="80"/></g>'
        )

        self.assertTrue(
            _hatch_lines(contours),
            "a group that declares a visible fill must still be shaded",
        )

    def test_child_fill_overrides_the_group(self):
        contours = _read_svg(
            '<g fill="black"><rect x="10" y="10" width="80" height="80" fill="none"/></g>'
        )

        self.assertEqual(_hatch_lines(contours), [])

    def test_group_stroke_reaches_its_children(self):
        # Without inheritance the stroke is unresolved, the element has no fill
        # of its own, and the only reason it survived was the phantom fill.
        contours = _read_svg(
            '<g fill="none" stroke="#000000" stroke-width="0.7">'
            '<path d="M 10 10 L 90 10 L 90 90"/>'
            "</g>",
            hatch_spacing_mm=0.0,
        )

        self.assertTrue(contours, "an inherited stroke must keep the element visible")

    def test_display_none_removes_the_subtree(self):
        contours = _read_svg(
            '<g display="none"><rect x="10" y="10" width="80" height="80" fill="black"/></g>'
            '<rect x="10" y="10" width="20" height="20" fill="black"/>'
        )

        self.assertTrue(contours)
        xs = [x for contour in contours for x, _ in contour]
        self.assertLessEqual(
            max(xs),
            30.001,
            "only the visible rectangle should contribute geometry",
        )

    def test_repo_line_art_sample_is_not_hatched(self):
        """The reported regression: shading turned line art into solid fill."""
        sample = SAMPLES / "kindergarten-house-sun.svg"
        if not sample.exists():
            self.skipTest("sample artwork is not present")

        settings = _settings(hatch_angle_deg=45.0, hatch_pattern="crosshatch")
        hatched = converter.read_svg(str(sample), settings)
        unshaded = converter.read_svg(
            str(sample), _settings(hatch_spacing_mm=0.0, hatch_pattern="crosshatch")
        )

        self.assertTrue(hatched, "the sample must still produce geometry")
        self.assertEqual(
            _hatch_lines(hatched),
            _hatch_lines(unshaded),
            "enabling shading must not add hatch to artwork that declares fill=\"none\"",
        )


if __name__ == "__main__":
    unittest.main()
