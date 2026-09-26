---
id: WSW-20260926-002
date: 2026-09-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/gcode.py
tags:
  - converter
  - clipping
  - soft-limit
  - reachable-area
  - bed
---

# Cap the drawable radius at the gantry's reach

## Summary

Added a `Gantry reach radius mm` setting (default 191.4) that caps the artwork
clipping radius at the gantry's reachable distance from the registered bed
center, instead of allowing artwork out to the full bed rim.

## Reason

The bed is 457 mm across, but the gantry can only reach 191.4 mm from the bed
center in its tightest direction (the +Y edge, given the installed 455 x 446 mm
envelope and the bed-center offset). Artwork clipped only to the bed circle
could therefore emit machine coordinates past the soft-limit envelope and trip
`Alarm:2 - Soft limit` on the controller.

## Implementation

- `settings.py`: new `machine_reach_radius_mm` (default 191.4) plus a UI field,
  and it is added to the non-negative validation.
- `gcode.py`: `plan_program` now clips at
  `min(bed_diameter/2 - bed_margin, machine_reach_radius_mm)`.

## Verification

- `python -m unittest discover -s software/tests` passes (25 tests), including a
  new test that a 200 mm stroke is clipped to a 50 mm configured reach.
- The Constitution preamble (max radius 184 mm) is unchanged: 184 mm < 191.4 mm,
  so it stays intact while the rim is now excluded.

## Struggles and rejected approaches

The reachable area is a circle, not the rectangular envelope intersection,
because the bed rotates freely and the pen can therefore point in any direction;
clipping to the envelope rectangle would still allow rotated artwork to leave
the rectangle. A theta-aware envelope check was noted as future work but not
needed for the current safe default.

## Risks and follow-up

- The 191.4 mm default assumes the current bed-center registration. If the
  magnetic registration shifts the bed center, the value should be recomputed as
  the gantry's tightest reach in that new frame.
- A future theta-aware pass could reclaim the asymmetric reach (232.6 mm on +X)
  for strokes whose bed angle keeps the pen in the long directions.

## Files

- `software/converter_core/settings.py`
- `software/converter_core/gcode.py`
- `software/tests/test_theta_feed.py`
- `software/README.md`
