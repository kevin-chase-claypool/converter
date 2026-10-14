---
id: WSW-20261013-014
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_a_center_test.py
  - samples/gcode/a-center-test.gcode
tags:
  - a-axis
  - centre-of-rotation
  - registration
  - diagnostic
related:
  - WSW-20261013-013
  - WSW-20261013-012
---

# Bed-rotation-centre test

## Summary

New generator `tools/make_a_center_test.py` and sample
`samples/gcode/a-center-test.gcode`: one paper point is visited at eight bed
angles (0..315 deg, 45 deg steps) drawing a paper-aligned tick each time,
plus a four-pass control at a single angle. If the registered centre
(G54 X0 Y0) sits exactly on the physical bed axis, all ticks coincide; a
centre offset C spreads them into a ring of radius |C|, with opposite ticks
separated by exactly 2|C|.

## Reason

With pen seating ruled out (the carriage nests every pen against the same
inner cylinder) and the ratio, directional deadband, cumulative reversal
loss, arc gaps and rotation all measured clean, the rotation-centre offset
is the last mechanism standing that fits every observation: a bed-turning
plot rotates the paper about the registered point, so an axis/registration
mismatch C displaces every mark drawn at bed angle theta by
`e(theta) = C - R(-theta) C`. That error is invisible to fixed-bed plots
(constant theta), to round-trip and single-angle diagnostics, and it is
rate-independent. In the two-pen tests the two copies' strokes were drawn
~600 deg apart in bed angle, where the same C produces inter-copy offsets of
up to 1.7|C| - matching the measured 0.5-1.5 mm divergences.

## Implementation

- Control: four ticks at theta = 0 (must overlap exactly - machine
  repeatability baseline).
- Station: ticks at theta = 0/45/90/135/180/225/270/315, each drawn from the
  same paper point with the paper-frame tick direction, so any displacement
  pattern reads directly in paper X/Y.
- Generator asserts paren balance on every line and reports the tick count
  and A range.

## Verification

- Self-check: 103 lines, 12 ticks, A range 0..3790.5 motor deg
  (315 deg x 12.03324), balanced parentheses.
- Bench reading: all nine marks in one tight group = centre correct; the
  0 deg vs 180 deg tick separation = 2|C| exactly, and the pattern centre
  gives the direction of C. If confirmed, the fix is a G54 origin
  correction by -C (registration change, no rewiring), and it would
  retro-explain the heraldic outline defects (features drawn at different
  bed angles displaced differently -> "outline not a constant distance").

## Files

- `tools/make_a_center_test.py`: generator and self-check.
- `samples/gcode/a-center-test.gcode`: the test program.
