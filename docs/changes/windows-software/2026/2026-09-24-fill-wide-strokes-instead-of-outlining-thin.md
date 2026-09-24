---
id: WSW-20260924-014
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/geometry.py
  - software/qt_svg_to_gcode.pyw
tags:
  - converter
  - stroke
  - fill
  - pen-width
---

# Fill wide strokes instead of outlining thin ones

## Summary

Added **Fill wide strokes** (`fill_wide_strokes`, default off) and
**Stroke fill ratio** (`stroke_fill_ratio`, default 2.0). When enabled, a
stroked path is drawn as a single centerline unless its width is at least the
ratio times the pen diameter; a stroke that wide is rendered as parallel passes
spaced one pen diameter apart, so its interior is solid.

## Reason

A pen already marks its own width, so turning a thin stroke into an outline
draws both edges for no visual gain and roughly doubles the path length — and
far worse, `stroke_expanded_contours` emits one closed rectangle per segment,
so a single polyline becomes many separate contours and a pen-down/pen-up
cycle each, which is what exploded print time. The operator wanted the software
to keep thin strokes as one pass and only spend extra passes where the pen
cannot render the stroke width in a single line.

Outlining is the wrong operation for a pen regardless: it traces the two edges
and leaves the interior empty, which is a cutter workflow, not line-weight
rendering. The correct alternatives are a single centerline for thin strokes
and solid fill for thick ones.

## Implementation

- `settings.py`: `fill_wide_strokes` checkbox and `stroke_fill_ratio` field in
  the Geometry group; `stroke_fill_ratio` added to nonnegative validation.
- `geometry.py`: new `offset_polyline` (per-vertex perpendicular offset) and
  `stroke_fill_contours` (parallel passes spaced `pen_diameter` apart).
  `element_contours` now, when `fill_wide_strokes` is on and the stroke width
  reaches the threshold, replaces the stroke with fill passes; otherwise it
  keeps the centerline. `expand_strokes` still applies when `fill_wide_strokes`
  is off. Threaded through `parse_svg_geometry` and `read_svg`.
- `qt_svg_to_gcode.pyw`: checkbox and field wiring, the ratio field hidden
  until the checkbox is on, and the raw-geometry cache key updated.

The pass count is `ceil(width / pen_diameter)`, so a 0.5 mm stroke with a
0.3 mm pen stays one pass (below the 0.6 mm threshold at ratio 2.0), while a
2 mm stroke becomes 7 passes.

## Verification

- `python -m unittest discover -s software\tests` — 23 tests pass (one new).
- A thin (0.5 mm) stroked path yields 1 contour with the feature on; a wide
  (2 mm) path yields 7 parallel passes; with the feature off the wide path
  stays 1 contour.

## Struggles and rejected approaches

An outline-vs-centerline ratio was considered and rejected: outlining is never
the right output for a pen, since it leaves the stroke interior empty. Filling
with parallel centerline passes reuses the normal stroke path and follows the
stroke's curves rather than clipping a hatch grid to a synthesized band.

The `fill_wide_strokes` checkbox was initially not included in the UI's
collected boolean settings, so it silently stayed off no matter how the box was
set; it was added to the settings dict in the follow-up fix.

The first implementation only took precedence over `expand_strokes` for strokes
that were wide enough to fill, so a thin stroke still fell through and was
outlined whenever `expand_strokes` was also checked — the exact penalty this
mode exists to avoid. `fill_wide_strokes` now owns stroke rendering outright and
`expand_strokes` is only consulted when it is off.

## Risks and follow-up

- `offset_polyline` is a per-vertex offset with no miter limit; sharp corners
  in a very wide stroke can round or self-intersect slightly. Acceptable for
  text and drawing strokes, not a robust general polygon offset.
- Passes are spaced at the full pen diameter, which is solid for a round tip
  but may show faint scallops on highly absorbent paper; a future setting could
  overlap passes slightly.
- The comparison assumes the converter's 1 SVG unit = 1 mm convention, the same
  as every other length in the converter.

## Files

- `software/converter_core/settings.py`
- `software/converter_core/geometry.py`
- `software/qt_svg_to_gcode.pyw`
- `software/tests/test_coordinate_frames.py`
- `software/README.md`
