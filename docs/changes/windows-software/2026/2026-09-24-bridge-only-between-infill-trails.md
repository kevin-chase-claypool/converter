---
id: WSW-20260924-007
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/gcode.py
tags:
  - infill
  - pen-up
  - bridge
  - correctness
---

# Keep the pen down only between infill trails, never across shape outlines

## Summary

The keep-down bridge (pen stays down between nearby contours) now only applies
between two open infill trails. It no longer bridges when either contour is a
closed stroke outline, so the pen lifts between separate shapes instead of
dragging across them.

## Reason

On the SFA logo the triangular infill dragged the pen from the top-right of the
"A" into the star because `bridge_motion` treated any two contours within the
pattern gap as bridgeable. Stroke outlines (letters, star) are closed loops
while infill lattice trails are open polylines, so the two can be distinguished
without a full fill/stroke tag.

## Implementation

- `gcode.py`: added `_is_open_contour`; both `build_preview_moves` and
  `contours_to_gcode` now require the previous and current contours to both be
  open before calling `bridge_motion`.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- SFA logo at scale 0.2: keep-down bridges dropped 289 -> 104 (all open-open),
  and pen-up commands rose 16 -> 201. `build_preview_moves` and
  `contours_to_gcode` agree on the counts.

## Struggles and rejected approaches

A full fill/stroke tag through the parse/plan pipeline was considered but is
more invasive; the open-vs-closed contour distinction achieves the same result
because infill trails are open and stroke outlines are closed.

## Risks and follow-up

A chained infill trail that happens to close on itself would be treated as a
stroke and not bridged, costing one extra pen cycle; this is rare and safe. The
remaining known issues are separate: A-axis-dominant lines may still bow (polar
subdivision) and infill may still bleed into internal white cutouts, both to be
confirmed against the actual SVG/print.

## Files

- `software/converter_core/gcode.py`: gate keep-down bridge on open contours.
