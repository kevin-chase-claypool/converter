---
id: WSW-20260924-009
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
tags:
  - infill
  - pen-cycle
  - sliver
  - performance
---

# Drop sub-pen-width infill fragments

## Summary

Contours shorter than 1 mm on paper are now removed after scaling. These are
clipped infill slivers and trace specks that draw an M3/M5 "dot" with no visible
contribution, and each one cost a full pen-up/pen-down cycle.

## Reason

Triangular infill clipped to a polygon boundary leaves sub-pen-width fragments.
Each became its own contour with an M3/M5 pair, which the user reported as
"tiny dots" that inflate print time without changing the result.

## Implementation

- `geometry.py`: added `MIN_FILL_SEGMENT_LENGTH = 1.0` and filtered contours by
  total length inside `apply_geometry_settings`, i.e. in on-paper coordinates
  after the scale is applied (a segment filter in SVG space would not match the
  on-paper dot size).

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- SFA logo at 0.2 scale: contours dropped 304 -> 222, contours under 1 mm fell
  to 0, and pen-up commands fell 201 -> 112.

## Struggles and rejected approaches

A segment-length filter inside the SVG-space lattice chaining was tried first,
but it measured the wrong coordinate space and removed almost nothing at
reduced scale; the on-paper contour filter is the correct location.

## Risks and follow-up

Any deliberate design feature under 1 mm on paper is also dropped. For this
single-pen plotter that is negligible; `MIN_FILL_SEGMENT_LENGTH` is the single
constant to tune if a different threshold is wanted.

## Files

- `software/converter_core/geometry.py`: on-paper minimum-contour-length filter.
