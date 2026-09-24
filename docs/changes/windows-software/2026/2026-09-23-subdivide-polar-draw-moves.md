---
id: WSW-20260923-002
date: 2026-09-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core
tags:
  - gcode
  - theta
  - polar
  - geometry
related:
  - WSW-20260923-001
---

# Subdivide draw moves so bed rotation traces straight lines

## Summary

The converter now splits each draw move into short sub-moves so that the polar
bed rotation produces the intended bed-frame path. Straight SVG lines no longer
come out as arcs when the bed rotates during the move.

## Reason

grblHAL interpolates X, Y and A linearly across one G-code move, and the
converter was emitting one move per SVG segment. Because the bed rotates during
that move, the pen's actual path across the paper bows away from the intended
bed-frame line. A first real plot showed it clearly: the house's straight roof
and walls came out as a dome. Measured on the house-and-sun, single moves
spanned up to 106° of bed rotation and bowed the pen up to 25 mm off the
straight line.

## Implementation

- `kinematics.py`: added `polar_segment_steps`, which measures a move's
  bed-frame bow from the linear X/Y/A interpolation and returns the number of
  sub-moves needed to hold each sub-chord within the `tolerance` setting.
- `gcode.py`: `contours_to_gcode` now emits those sub-moves, computing each
  sub-point's machine X/Y/A from the straight bed point and the interpolated
  bed angle.

The feed plan is still computed once per SVG segment; only the emitted move
count changes.

## Verification

- Bed-frame deviation of the drawn path from a straight line, house-and-sun,
  within a single pen-down stroke: optimized `0.24 mm`, min-rotation `0.24 mm`,
  tangent `0.25 mm` — all within the `0.25 mm` tolerance, versus about `25 mm`
  before the change.
- The sample still emits 20 contours and 20 `M3`, with 284 draw moves.
- `test_coordinate_frames.py` (3 tests) and `test_theta_feed.py` (19 tests)
  pass.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

The first bow measurement was wrong: it paired consecutive `G1` lines blindly,
so it also compared the last move of one contour with the first move of the
next across a `G0` pen-up travel, reporting meaningless 25–113 mm bows at
contour boundaries. That made the split look ineffective and nearly sent the
fix in the wrong direction. The measurement now only compares moves within one
pen-down stroke.

The first split sizing assumed the bow falls as `1/steps^2` (arc sagitta); for
this geometry it falls more slowly, around `1/steps^1.35`, so the initial step
count undershot the tolerance. The sizing now uses that measured exponent.

Using `Theta mode = fixed` (no bed rotation) also produced straight lines, but
abandons the polar bed motion, so it is a workaround rather than a fix.

## Risks and follow-up

Draw moves are more numerous (about 264 versus 59 for the house-and-sun), so the
G-code is longer; grblHAL's look-ahead blends the collinear sub-moves, so
runtime should be close. The preview still shows one move per SVG segment, so
its move count and G-code listing do not match the emitted file exactly.

## Files

- `software/converter_core/kinematics.py`: `polar_segment_steps` and the bow measurement.
- `software/converter_core/gcode.py`: sub-divided draw-move emission.
