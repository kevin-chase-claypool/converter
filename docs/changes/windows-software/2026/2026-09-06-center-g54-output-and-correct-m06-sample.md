---
id: WINSW-20260906-001
date: 2026-09-06
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/gcode.py
  - software/converter_core/kinematics.py
  - samples/svg/m06-radius-sweep.svg
tags:
  - g54
  - coordinates
  - parking
  - m-06
  - a-axis
related:
  - HW-20260906-004
  - HW-20260906-006
---

# Center G54 output and correct the M-06 sample

## Summary

The converter now emits artwork around the bed-centered G54 origin instead of
the SVG document origin. The pen-free M-06 sample now traverses 20 mm, 50 mm,
and 80 mm radii and includes both A directions.

## Reason

Inspection of the original sample with a temporary pen-centered G54 showed a
document centered at `(100,100)` emitting X/Y near `(100,100)`, followed by an
out-of-bed diagonal park command. Its nominal radial strokes also resolved to
`A0`, so it did not test radius-aware A motion.

## Implementation

`plan_program()` clips around the SVG center and then normalizes the resulting
paths to `(0,0)` before all theta planning, preview construction, and G-code
emission. The NE park position uses the configured drawable radius divided
across X/Y, keeping it on the circular bed. The sample uses explicit polylines
because this SVG parser did not retain the prior arc commands.

## Verification

- `python -m unittest discover -s software/tests -v` passed 18 tests.
- Tests cover G54-centered G-code/preview coordinates, bounded parking, and
  sample radii with positive and negative A draw deltas.
- Static sample inspection produced centered X/Y bounds of approximately
  `-80..80` mm and a park target near `(157.15,157.15)` mm.

## Struggles and rejected approaches

The original SVG `A` arc commands collapsed to straight horizontal chords in
the current parser, producing no A movement. Replacing them with explicit
polylines preserves the intended test geometry without changing parser scope.

## Risks and follow-up

This corrects converter coordinates but does not establish machine references.
P100 remains the production registration authority; the temporary manual G54
is pen-free only. Before streaming M-06, establish a deliberate temporary A
reference and inspect the exact generated file.

## Files

- `software/converter_core/gcode.py`: normalizes the SVG frame to G54.
- `software/converter_core/kinematics.py`: constrains NE parking to the
  drawable circle.
- `software/tests/test_theta_feed.py`: regression coverage.
- `samples/svg/m06-radius-sweep.svg`: corrected M-06 input.
