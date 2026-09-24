---
id: WSW-20260924-008
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/kinematics.py
tags:
  - polar
  - subdivision
  - straightness
  - a-axis
---

# Subdivide polar moves linearly so A-axis-dominant lines stay straight

## Summary

The polar-bow subdivision now splits a coordinated X/Y/A move proportionally to
its measured bow (`steps = deviation / tolerance`) instead of
`(deviation / tolerance)^0.75`. A-axis-dominant lines were being under-split
because their bow grows linearly with bed rotation, so the old exponent left a
residual bow several times the tolerance.

## Reason

A single coordinated X/Y/A move interpolates the bed rotation linearly, so its
bed-frame path bows off the straight SVG chord. Measured bow is linear in the
rotation (`deviation ~= L * dtheta / 4`), so subdividing N ways leaves
`deviation / N`. The prior `0.75` exponent was based on a quadratic falloff that
does not hold here and left A-axis lines visibly bowed.

## Implementation

- `kinematics.py`: `polar_segment_steps` now uses a linear split and its
  docstring/comment reflect the measured linear relationship.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- A 100 mm chord rotating 120 deg now splits into 179 sub-moves with ~0.29 mm
  residual bow (previously 49 sub-moves and ~0.91 mm). Across 10-120 deg the
  residual stays at or near the 0.25 mm tolerance.

## Struggles and rejected approaches

The previous quadratic assumption was kept for a long time; re-measuring the
deviation-vs-rotation curve showed it is linear, which is the only correct basis
for the split exponent.

## Risks and follow-up

More sub-moves mean a longer G-code program (the SFA logo at 0.2 scale is ~30k
lines). The `600` sub-move cap remains; extremely long, high-rotation segments
could still exceed tolerance, which is acceptable for a non-precision machine.

## Files

- `software/converter_core/kinematics.py`: linear polar subdivision.
