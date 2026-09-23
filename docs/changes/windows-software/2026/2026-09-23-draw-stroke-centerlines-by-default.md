---
id: WSW-20260923-001
date: 2026-09-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core
tags:
  - gcode
  - pen-plot
  - performance
related:
  - RPSW-20260923-016
---

# Draw stroke centerlines by default instead of outlining the stroke width

## Summary

The converter now draws each stroked SVG path as a single centerline by
default, instead of expanding every stroke into filled outlines of its width.
A new opt-in "Expand strokes to outlines" setting restores the old behavior.

## Reason

For a pen plotter the pen already marks its own width, so the stroke width does
not need to be traced as a filled outline. The previous hard-coded stroke
expansion split each 0.7 mm polyline into a rectangle per segment, turning the
20-polyline house-and-sun into ~150 contours and ~150 M3/M5 cycles. Every one
of those cycles is a full pen re-approach, which slows the job and gives the
force loop no time to settle.

## Implementation

- `settings.py`: added `expand_strokes` (default `False`) and a matching
  "Expand strokes to outlines" checkbox.
- `geometry.py`: `read_svg` now passes the setting into `parse_svg_geometry`
  instead of hard-coding `True`.
- `qt_svg_to_gcode.pyw`: exposed the checkbox in the Geometry group and included
  it in the settings round-trip.

## Verification

- The house-and-sun sample now emits 20 contours, 20 `M3`, and 21 `M5` (the
  extra `M5` is the program-opening lift), down from 150 contours and 150 `M3`.
- `test_coordinate_frames.py` (3 tests) and `test_theta_feed.py` (19 tests)
  still pass.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

Merging the expanded outline rectangles was rejected: they do not form a
contiguous path, so merging would not reliably remove pen lifts. Drawing the
centerline directly is both simpler and the correct geometry for a pen.

## Risks and follow-up

This changes emitted geometry for any user who relied on the outline/fill look;
it is opt-in for them. Pen-width compensation remains a separate, still-enabled
setting. The pen-up/pen-down dwell defaults are still machine-specific and
should be reviewed in a separate change.

## Files

- `software/converter_core/settings.py`, `software/converter_core/geometry.py`, `software/qt_svg_to_gcode.pyw`: new setting and wiring.
- `software/README.md`: documented the new checkbox.
