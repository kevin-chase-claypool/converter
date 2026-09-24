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
- `geometry.py`: the shared `read_svg` now passes the setting into
  `parse_svg_geometry` instead of hard-coding `True`.
- `qt_svg_to_gcode.pyw`: the desktop app has its **own** contour loader,
  `MainWindow.load_contours`, which called `parse_svg_geometry` directly with
  `expand_strokes` hard-coded `True`. That is the call the app actually uses, so
  it now reads the setting. The checkbox is exposed in the Geometry group,
  included in the settings round-trip, and added to `raw_geometry_key` so
  toggling it invalidates the cached contours.

## Verification

- The house-and-sun sample now emits 20 contours, 20 `M3`, and 21 `M5` (the
  extra `M5` is the program-opening lift), down from 150 contours and 150 `M3`.
- `test_coordinate_frames.py` (3 tests) and `test_theta_feed.py` (19 tests)
  still pass.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

The first version of this fix only changed the shared `read_svg`, which the
desktop app never calls. The app's `load_contours` bypasses it and passed
`expand_strokes=True` by hand, so the preview and export kept producing outlines
even after the core looked fixed — a live session was spent chasing that. The
lesson: the desktop app has its own contour-loading path, and both must be
changed together.

Merging the expanded outline rectangles was rejected: they do not form a
contiguous path, so merging would not reliably remove pen lifts. Drawing the
centerline directly is both simpler and the correct geometry for a pen.

## Risks and follow-up

This changes emitted geometry for any user who relied on the outline/fill look;
it is opt-in for them. Pen-width compensation remains a separate, still-enabled
setting. The pen-up/pen-down dwell defaults were machine-specific and are now
set for the installed toolhead in `WSW-20260923-003`.

## Files

- `software/converter_core/settings.py`, `software/converter_core/geometry.py`, `software/qt_svg_to_gcode.pyw`: new setting and wiring.
- `software/README.md`: documented the new checkbox.
