---
id: WSW-20261013-013
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: verified
components:
  - tools/make_a_ratio_deadband_test.py
  - samples/gcode/a-ratio-deadband-test.gcode
tags:
  - a-axis
  - ratio
  - deadband
  - diagnostic
related:
  - WSW-20261013-012
  - WSW-20261001-001
---

# A-axis ratio / directional deadband test

## Summary

New generator `tools/make_a_ratio_deadband_test.py` and sample
`samples/gcode/a-ratio-deadband-test.gcode`: a plot that measures the
machine's **effective bed ratio** per quadrant and the **approach-direction
deadband** directly on paper, with ticks drawn before and after commanded
full bed revolutions and from both approach directions.

## Reason

The motor pulley is 60T and the bed ring is 720 teeth - a theoretical ratio
of exactly 12.000 - while the machine's calibrated effective ratio is
12.03324 (+0.28 %). If that calibration is wrong (or if the belt's seating
changes with tension direction), one commanded revolution (A += 4332 motor
degrees) lands 1.0 bed degree off = 1.75 mm at r=100, and each tension flip
adds an angular step. The existing reversal diagnostic could not see this:
its soak ticks were both approached from the same direction, so a
directional deadband cancels - a real blind spot.

## Implementation

- Part A, r=100 at psi 45/135/225/315: tick, A += 4332 (one commanded turn
  at the calibrated ratio) at F12000, tick, A -= 4332, tick. Tick spacing
  reads the ratio error (and its variation by quadrant = rim/belt ovality);
  tick1-vs-tick2 reads direction-dependent hysteresis.
- Part B, r=70 at psi=90: ticks drawn with A arriving at 0 from the + side,
  then from the - side, twice each. The offset between the tick families is
  the reverse deadband at that radius.
- The generator asserts paren balance on every line (learned from the
  earlier ioSender load failure) and reports the A range on generation.

## Verification

- Self-check: 151 lines, A range -24.1..4332.0 motor deg, balanced
  parentheses, standard preamble/pen/postamble.
- **Bench result (2026-10-13, photo PXL_20261013_234628019). All five tick
  groups are single marks**: lengths 4.40 / 4.52 / 4.47 / 4.63 / 4.68 mm at
  ~12.85 px/mm - a 4 mm tick plus the pen width. A wrong ratio (12.000 vs
  12.03324) would lengthen each turn group to ~6.4 mm; a deadband or
  hysteresis family would stretch them proportionally. Therefore:
  one commanded revolution (A += 4332) is exactly one physical revolution
  at all four quadrants; the calibrated 12.03324 is confirmed and constant
  (the +0.28 % over the tooth count is a stable ~0.6 mm belt ride-height
  offset, and constant offsets fold into calibration); no measurable
  hysteresis (<~0.06 bed deg) and no measurable directional deadband
  (<~0.08 bed deg at r=70). **The ratio/direction hypothesis is refuted** -
  what remains untested is the real program's streamed traffic
  (87 blocks at ~10 Hz with junction acceleration demands up to 240,000
  motor deg/s^2), for which `headback-test-bed-slow.gcode` exists.

## Risks and follow-up

- If the ratio test shows the pure tooth count, recalibrating the converter
  ratio is a one-line settings change - and it would also explain the
  residual ~0.5 deg errors that survive theta-wrap re-registration.

## Files

- `tools/make_a_ratio_deadband_test.py`: generator and self-check.
- `samples/gcode/a-ratio-deadband-test.gcode`: the test program.
