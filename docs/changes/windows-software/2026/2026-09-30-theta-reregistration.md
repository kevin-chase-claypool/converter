---
id: WSW-20260930-023
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
tags:
  - theta
  - kinematics
  - drift
  - calibration
related:
  - WSW-20260930-021
  - software/README.md
---

# Keep the commanded A small: re-register the bed each contour

## Summary

The operator reported that the drift is worse where ioSender's A DRO is high
and "looks perfect" near A = 0. That is the signature of an A-axis scale error:
a feature's positional error is proportional to the *commanded* angle, so a
program that winds the bed 19 revolutions accumulates 19 revolutions' worth of
error. The planner now re-registers the bed at every contour - subtracting
whole revolutions from the bed angles - which leaves the drawing identical but
keeps |A| near zero. On a realistic kaleidoscope design the commanded A fell
from ±76,000 motor degrees (19.5 bed turns) to ±2,500 (1.16 turns), a 17x
reduction in the worst case.

## Reason

"i wonder if the drift has anything to do with the A degrees seen in DRO on
iosender. at higher values i see the drift is more pronounced, at values closer
to 0 it looks perfect. is there any way to keep that value from getting too
high in converter and kaleidoscope?"

The monotonic-theta ordering that keeps the bed from jerking back and forth
(`monotonic_theta`, on by default) deliberately accumulates rotation instead.
That is fine on a perfectly calibrated A axis and expensive on a real one.

## Implementation

- `converter_core/gcode.py`: `_reregister_thetas()` shifts a contour's bed
  angles by `-360 * round(first_theta / 360)`, and `plan_program` applies it to
  every contour before storing the plan, so the preview, the time estimate and
  the emitted program all agree. `previous_theta` becomes the re-registered
  value, so the travel move into the next contour carries the correction.
- `converter_core/settings.py`: new `theta_wrap` setting, default **on**, with
  a tooltip and a main-app checkbox
  ("Re-register the bed each contour (keep A small)"). The kaleidoscope app
  inherits it through the shared defaults.
- Physically the shift is neutral: a whole bed revolution leaves every point on
  the bed where it was, so X/Y in the program are unchanged and only A differs,
  by whole revolutions.

## Verification

- Realistic kaleidoscope design (334k moves) with and without the shift:
  A -2,486..2,519 (1.16 bed turns) versus -8,246..76,127 (19.48 turns);
  333,943 of 333,992 X/Y pairs identical, the rest differing only in the last
  printed decimal.
- Small deterministic case in `software/tests/test_theta_wrap.py`: a two-turn
  spiral followed by six radial marks - without re-registration the marks are
  commanded at ~8,800 motor degrees, with it at ~290.
- The same test asserts the drawing is unchanged (X/Y equal, A differences
  whole revolutions) and that the setting defaults on.
- All thirteen test modules pass; `docs_index --write/--check` pass.

## Struggles and rejected approaches

- Wrapping inside a contour was rejected: a mid-stroke jump of a whole
  revolution would corrupt the path. The shift is constant per contour.
- Turning `monotonic_theta` off instead was rejected: it reduces winding by
  making the bed reverse constantly, which trades drift for backlash.
- Reading the ratio out of the file by fitting A against the polar angle was
  tried and rejected earlier; the coordinates are machine-frame, so the
  relation does not hold.

## Risks and follow-up

- The correction is not free: the travel move into a re-registered contour can
  include up to a full bed revolution, so the plot may take slightly longer and
  the bed reverses direction once per contour at most. `theta_wrap` can be
  switched off if that proves worse.
- This bounds the *symptom*. If drift is proportional to travel rather than to
  the commanded angle (slip while rotating), this will not help - and if the
  spiral in `samples\gcode\theta-calibration.gcode` does not close, the
  underlying A calibration is still wrong.
- `theta_wrap` changes the emitted A values, so programs made before this
  change differ; the ratio/offset header now makes that visible.

## Files

- `software/converter_core/gcode.py`: `_reregister_thetas` and its use in
  `plan_program`.
- `software/converter_core/settings.py`: `theta_wrap`, checkbox and tooltip.
- `software/tests/test_theta_wrap.py`: bounding, no-wrap comparison, drawing
  invariance, default.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
