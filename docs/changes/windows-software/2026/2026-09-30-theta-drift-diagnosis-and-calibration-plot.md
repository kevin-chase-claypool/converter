---
id: WSW-20260930-021
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
tags:
  - theta
  - kinematics
  - calibration
  - diagnostics
related:
  - WSW-20260930-015
  - software/README.md
---

# Theta drift: record the ratio in the G-code and ship a calibration plot

## Summary

Two things came out of the report that the 12.03324 bed ratio "didn't work":

1. It *is* in effect. The ratio is applied everywhere through
   `settings.theta_drive_ratio`, no app overrides it, and the plotted file
   (`samples/gcode/kaleidoscope1.gcode`, written 17:53) postdates the ratio
   commit (04:47 the same day).
2. The ambiguity came from the file itself: nothing in a G-code program said
   which ratio produced it. The header now records the ratio, the theta offset,
   the feeds and the tolerance.

Because a wrong ratio and mechanical backlash look alike in a finished plot,
`tools/make_theta_calibration.py` now writes
`samples/gcode/theta-calibration.gcode`: eight radial ticks, one full circle
(one bed revolution) and a two-turn spiral (two more revolutions). A ratio
error grows with the turns, so the second lap shows twice the first lap's
offset; backlash does not behave that way.

## Reason

"it appears that the change to 12.033 didnt work. i'm seeing the same
artifacts/drift that i saw previous to the change." The ratio could not be
checked after the fact because the emitted program does not carry it, and the
nominal hardware ratio is exactly 12.0 (720 GT2 bed teeth over 60 GT2 motor
teeth), so 12.03324 measured means either the survey was contaminated or the
controller's A steps-per-degree is off by 0.28 %.

## Implementation

- `converter_core/gcode.py`: the preamble gained
  `(theta ratio 12.03324 motor deg per bed deg, offset 0.000)` and
  `(feed ..., travel ..., tolerance ...)` comments. Both apps share the
  emitter, so every saved program is now self-documenting.
- `tools/make_theta_calibration.py` (new): builds the calibration geometry in
  bed coordinates and writes it through the normal planner and emitter, so the
  pattern uses exactly the production code path. The header states the ratio
  and how to read the marks, and the tool reports the A span it produced.

## Verification

- `python tools\make_theta_calibration.py` writes the file and reports
  `A spans 13010.7 motor deg over 3.00 bed revolutions` - 3 x 4331.97, i.e. the
  circle plus the two-turn spiral really are commanded as three revolutions.
- The new preamble was checked on a two-point program and the existing preamble
  assertion in `software/tests/test_theta_feed.py` was updated to match.
- All eleven test modules pass.

## How to read the calibration plot

- Correct ratio: the circle closes and the spiral's outer end lines up with the
  radial tick at bed angle 0.
- Wrong ratio: the spiral's outer end is offset by `E` degrees where
  `E = 720 * (assumed / true - 1)`, i.e. twice the offset of the single circle.
  Measure the gap `s` at the spiral's radius `R` and use
  `E = degrees(atan(s / R))`, then
  `true_ratio = assumed_ratio * 360 / (360 + E / 2)`.
- If the single circle closes but the spiral does not, the error is not a ratio
  error and the machine is losing motion (belt slip or backlash).

## Struggles and rejected approaches

- Writing marks at bed angles 360 and 720 does nothing: the bed angle follows
  the direction of travel, so the planner picks the nearest wrap and the marks
  land on top of each other no matter what. Only a path that actually winds -
  a circle or spiral - accumulates rotation.
- Reading the effective ratio out of the G-code by regressing A against
  `atan2(Y, X)` was tried and rejected: X/Y are machine-frame coordinates, so
  that relation does not hold on this machine.

## Risks and follow-up

- The result is only as good as the operator's measurement of the spiral gap;
  the two-turn spiral doubles the signal for that reason.
- If the calibration shows the ratio is right after all, the next suspect is
  the controller's A steps-per-degree (hardware side), not the converter.

## Files

- `software/converter_core/gcode.py`: header comments.
- `tools/make_theta_calibration.py`, `samples/gcode/theta-calibration.gcode`.
- `software/tests/test_theta_feed.py`: preamble assertion.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
