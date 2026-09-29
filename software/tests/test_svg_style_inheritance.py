"""Regression tests for SVG presentation-attribute inheritance and line-art fill.

The converter used to read presentation values from the element alone. A
wrapper such as ``<g fill="none" stroke="#000" stroke-width="0.7">`` therefore
did not reach its children, every child fell back to the SVG initial fill of
black, and outline paths were treated as solid filled regions whose interiors
were hatched. These tests pin the inherited behaviour.

Fill for stroke-only artwork is deliberately narrower than that phantom fill:
an element that declares no visible fill contributes only the regions its
*closed* outlines enclose (see `closed_outline_regions`). Open subpaths have no
bounded interior, so they stay line only and no fill can leak across them.
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
        # An open subpath has no bounded interior, so an inherited fill="none"
        # must not turn it into a filled region.
        contours = _read_svg(
            '<g fill="none" stroke="#000000" stroke-width="0.7">'
            '<path d="M 10 10 L 90 10 L 90 90"/>'
            "</g>"
        )

        self.assertTrue(contours, "the stroked outline must still be drawn")
        self.assertEqual(
            _hatch_lines(contours),
            [],
            "an open outline has no interior, so it must not be hatched",
        )

    def test_closed_outline_fills_its_own_interior(self):
        """Stroke-only line art fills inside its own closed outlines."""
        square = [(10.0, 10.0), (90.0, 10.0), (90.0, 90.0), (10.0, 90.0)]
        contours = _read_svg(
            '<g fill="none" stroke="#000000" stroke-width="0.7">'
            '<polyline points="10,10 90,10 90,90 10,90 10,10"/>'
            "</g>"
        )

        hatch = _hatch_lines(contours)
        self.assertTrue(hatch, "a closed outline must be hatched inside")
        for start, end in hatch:
            for point in (start, end):
                self.assertTrue(
                    converter.point_in_polygon(point, square),
                    f"fill must stay inside the closed outline, got {point}",
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

    def test_repo_line_art_sample_fills_only_closed_outlines(self):
        """Fill follows the enclosed outlines instead of the artwork silhouette.

        The sample's house body, door, windows, and sun are closed polylines and
        are hatched inside their own outlines. The roof, chimney, sun rays, and
        grass are open strokes, so they stay line only. The earlier reported
        regression was fill leaking over the whole silhouette; this pins the
        narrower rule that replaced it.
        """
        sample = SAMPLES / "kindergarten-house-sun.svg"
        if not sample.exists():
            self.skipTest("sample artwork is not present")

        settings = _settings(hatch_angle_deg=45.0, hatch_pattern="crosshatch")
        hatched = converter.read_svg(str(sample), settings)
        unshaded = converter.read_svg(
            str(sample), _settings(hatch_spacing_mm=0.0, hatch_pattern="crosshatch")
        )

        self.assertTrue(hatched, "the sample must still produce geometry")
        before = {tuple(map(tuple, contour)) for contour in _hatch_lines(unshaded)}
        added = [
            contour
            for contour in _hatch_lines(hatched)
            if tuple(map(tuple, contour)) not in before
        ]
        self.assertTrue(added, "closed outlines must gain interior fill")
        closed_outlines = (
            [(42, 165), (42, 103), (101, 54), (160, 103), (160, 165)],
            [(85, 165), (85, 123), (112, 123), (112, 165)],
            [(56, 117), (76, 117), (76, 139), (56, 139)],
            [(126, 117), (146, 117), (146, 139), (126, 139)],
            [
                (177, 28), (184, 30), (189, 36), (191, 44), (189, 52), (184, 58),
                (177, 60), (169, 58), (164, 52), (162, 44), (164, 36), (169, 30),
            ],
        )
        for start, end in added:
            for point in (start, end):
                inside = any(
                    converter.point_in_polygon(point, polygon)
                    for polygon in closed_outlines
                )
                self.assertTrue(
                    inside,
                    f"fill left the closed outlines of the artwork, got {point}",
                )


if __name__ == "__main__":
    unittest.main()
