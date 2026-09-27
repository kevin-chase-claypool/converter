---
id: WSW-20260927-006
date: 2026-09-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/converter_core/gcode.py
tags:
  - converter
  - preview
  - infill
  - serpentine
  - pen-cycle
related:
  - WSW-20260927-005
---

# Show keep-down connectors in the preview

## Summary

The preview now draws the keep-down connectors, so chained infill reads as one
continuous serpentine instead of a set of separate strokes.

## Reason

Line-family infill started chaining passes (WSW-20260927-005), but the preview
still showed disconnected lines. The connector *was* already emitted as a draw
move with `strategy: "keep_down_bridge"`, so the overlay for the pen-down path
had it. The gap was that the move carried no usable bed coordinates:

```python
"bed_start": path[0],
"bed_end": path[0],
```

Both endpoints were the destination, so the connector was a zero-length segment
in the bed frame. The blue base layer and the drawn-path layer are both built
from bed coordinates, so neither could show it, and the passes stayed visually
separate even though the program joins them.

## Implementation

- `software/converter_core/gcode.py`: the bridge move's `bed_start` is now the
  previous path's last point, which is where the connector actually starts.
  `bed_end` was already correct at the next path's first point.
- `software/qt_svg_to_gcode.pyw`: `GLPreview.rebuild_cache` appends each
  keep-down connector to the base `artwork` layer. The connectors are not part of
  the clipped contour set, so without this the base layer showed only the
  contours. The drawn-path layer needed no change - it already reads
  `bed_start`/`bed_end` from each draw move.

## Verification

Dense linear fill, 20 x 20 mm square, 0.3 mm spacing, 0.3 mm pen:

- 86 bridge moves, **0** of them with a zero-length bed segment;
- 179 draw moves drawn as **6 strokes**, with 5 pen lifts and **0**
  discontinuities inside a down-stroke - i.e. the preview now follows one
  continuous serpentine and lifts only where the gap guard refused a connector;
- the base `artwork` layer gained exactly 86 segments (358 vertices against 186
  for the contour-only build), matching the bridge count.

- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 43
  tests. Two new cases assert that a bridge move has a non-zero bed segment and
  that a dense fill previews as continuous strokes.
- `python -m py_compile software\qt_svg_to_gcode.pyw software\converter_core\gcode.py`
  passes.

## Struggles and rejected approaches

The first look at this concluded the preview did not implement bridging at all,
because `build_preview_moves` reads as a separate implementation from
`contours_to_gcode`. Reading the bridge branch showed it does - the defect was
the zero-length bed segment, one line away from being right.

Rebuilding the base layer from the draw moves was rejected. It would include the
connectors for free, but the moves are subdivided into sub-millimetre steps, so
the base layer would grow by an order of magnitude in vertex count for no visual
gain. Appending only the connectors keeps the layer the same size.

## Risks and follow-up

- The base layer grows by one segment per bridge. That is 86 segments for the
  fixture and about 1,033 for the spirit-logo sample, which is negligible
  against the contour geometry.
- The red pen-down overlay already showed the connectors and remains unchanged;
  it is drawn in the machine frame while the base layer is in the bed frame, so
  the two still diverge when the bed is rotated. That difference is by design and
  is documented in Preview settings.

## Files

- `software/converter_core/gcode.py`: real bed endpoints for bridge moves.
- `software/qt_svg_to_gcode.pyw`: connectors added to the base layer.
- `software/tests/test_infill_bridging.py`: coverage for both.
- `software/README.md`: notes that the preview shows the connectors.
