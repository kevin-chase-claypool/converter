---
id: WSW-20261013-008
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - software/converter_core/settings.py
  - samples/gcode/a-repeatability-test.gcode
tags:
  - a-axis
  - rate-limit
  - theta
  - outline
  - verification
related:
  - RPSW-20261001-001
  - 2026-10-01-theta-a-rate-limit-lowering
---

# Converter A limits raised to 30000 / 6000; controller set to match

## Summary

The converter's assumed A-axis limits move from 15000/3000 to **30000 motor
deg/min / 6000 motor deg/s^2**, matching the controller (`$113=30000`,
`$123=6000`). The a-repeatability sample is regenerated at F30000 for the
paper verification.

## Reason

Profiling contour 2 (the outer silhouette) showed the tight stretches - the
tail bend, the run to the butt, and the leg - demand up to **~42 motor degrees
of bed rotation per mm of pen travel**. At the 700 mm/min tangential target
that is ~29,400 motor deg/min, twice the old 15,000 cap, so the planner was
throttling exactly the stretches the operator reports as wobbly (and the
stalls seen before the planner caps existed came from the same kind of spot).
The converter's limits are not exposed in the UI; they live in
`ThetaControllerLimits` and must be changed in code.

## Implementation

- `settings.py`: `max_rate_deg_min` 15000 -> 30000,
  `max_acceleration_deg_s2` 3000 -> 6000, with the rationale and the
  verification note in the comment. Every emitted preamble now prints the new
  numbers, so a `$$` comparison stays meaningful.
- `samples/gcode/a-repeatability-test.gcode` regenerated with
  `python tools\\make_a_repeatability_test.py --feed 30000` (8.7 s per bed
  revolution, 69.3 s of plotted rotation).
- `software/tests/test_theta_feed.py`: preamble expectation updated.

## Verification

- Code: 40 tests pass across `test_theta_feed`, `test_theta_wrap`,
  `test_kaleidoscope`.
- **Hardware: partial pass (2026-10-13).** The regenerated a-repeatability
  program ran on paper; the operator reports the **r=100 mm station drew a
  perfect circle** - the pen retraced its own line through two revolutions out
  and two back at F30000, which is the same acceptance condition the 20,000
  value met. The r=160 station could not be run in the same session: only
  8.5 x 11 in paper was on hand (the station needs roughly a 12.6 in sheet).
  Re-run the full program on a larger sheet when available; the bed load that
  risks step loss is radius-independent, so the r=100 pass is the primary
  gate and r=160 is confirmation.

## Struggles and rejected approaches

Considered leaving the converter at 15000 and only raising `$113`; rejected
because the emitted F values themselves cap the A rate, so the machine would
never be asked to use the new headroom.

## Risks and follow-up

- 30000 motor deg/min is 1.5x the highest value verified on paper (20000,
  2026-10-01). Until the mark test passes, treat 30000 as unverified and keep
  the 20000 fallback in mind.
- The tangential speed still paces the bed; raising limits does not change the
  commanded geometry, only how quickly the tight stretches may run.

## Files

- `software/converter_core/settings.py`: limits and rationale.
- `samples/gcode/a-repeatability-test.gcode`: F30000 acceptance sample.
- `software/tests/test_theta_feed.py`: preamble expectation.
- `docs/project/ENGINEERING_LOG.md`: session entry.
