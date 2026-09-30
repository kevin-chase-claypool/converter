---
id: RPSW-20260929-004
date: 2026-09-29
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: superseded
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp
  - firmware/pen_pressure/README.md
  - docs/testing/TEST_PLAN.md
tags:
  - toolhead
  - force-control
  - pen-force
  - calibration
  - safety
related:
  - docs/integration/INTERFACES.md
  - docs/testing/TEST_PLAN.md
---

# Lower the pen force target to 38 g with a ±10 g band

## Summary

The integrated toolhead's drawing-force target drops from 45 g to 38 g, and its
target-ready band narrows from ±15 g to ±10 g. The pen now seeks to the lower
edge of a 28-48 g band around 38 g instead of a 30-60 g band around 45 g. The
75 g hard-force limit and the relief trigger 20 g above target are unchanged, so
the relief now trips at 58 g.

## Reason

The operator judged the marking force slightly too heavy and asked for a lower
target plus a narrower tolerance. The old band's 60 g top allowed the loop to
hold a press well above the intended force.

## Implementation

In `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:

- `TARGET_FORCE_RAW_DELTA` and `CONTACT_RAW_DELTA`: `226745` (45 g) to
  `191473` (38 g) at the E-09C scale of 5,038.77 raw/g.
- `CONTACT_READY_TOLERANCE_RAW`: `75582` (±15 g) to `50388` (±10 g).
- `HARD_FORCE_RAW_DELTA` stays `377908` (75 g) and `HOLD_URGENT_RELIEF_RAW`
  stays `100775` (20 g above target), so the relief trigger is now 58 g with
  17 g before the hard limit. The 10 g `HOLD_BAND_HEADROOM_RAW` clamp still
  satisfies its `static_assert` (75 g > 10 g band + 10 g headroom).

The same pass corrected force, pulse-width, and pulse-ratio values that had gone
stale in the current-state documents relative to the code: `firmware/README.md`,
`firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`,
`docs/integration/INTERFACES.md`, and `docs/testing/TEST_PLAN.md` (T-02, T-03)
now describe a 38 g target, a 28-48 g band, a 75 g hard limit, the 10 ms coarse
pulse, and the 2:1 coarse-pulse credit. The old 35 g / 60 g / 25-45 g / 13:1
figures were superseded settings that no longer matched the code. The
`firmware/README.md` sentence that still described the retired two-touch seek
was rewritten to the current single bounded descend.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` succeeded
  for `firmware/pen_pressure/pro_micro_rp2350_toolhead` (82,600 bytes program,
  16,236 bytes globals). The force-envelope `static_assert` is evaluated at
  compile time, so the new constants are accepted.
- `python tools\docs_index.py --write` and `--check` passed.
- No bench test was run. The installed toolhead must be re-flashed with this
  build and re-qualified on T-02/T-03 before any plotting run.

## Struggles and rejected approaches

The request said to lower the target and "drop the ±" without naming a band, so
±10 g was chosen as the assumption. It is the narrowest band with prior bench
history: ±5 g was rejected on 2026-09-23 because friction and noise drifted
long strokes out of band into retract/re-approach cycles, and ±10 g was widened
to ±15 g on 2026-09-25 after high-speed friction lifted the pen. Returning to
±10 g deliberately re-enters that failure mode; if the pen lifts again, adjust
the band or the hold cadence rather than raising the target back to 45 g.

## Risks and follow-up

- Superseded on 2026-09-29 by `RPSW-20260929-005`: a print run rejected the
  38 g / ±10 g setting, and the 45 g / ±15 g values were restored.
- The narrower band and lower target are unverified on the installed pen. The
  hold may lift the pen on fast strokes (the 2026-09-25 failure), or 38 g may
  mark too lightly for some tools.
- Both values are compile-time constants: the change has no effect until the
  Pro Micro is re-flashed.
- The 40-60 g figures in the E-09C/E-09F calibration records and test rows are
  left unchanged because they describe that staged bench profile, not the
  integrated build.
- Per-tool preflight (T-01J) still governs the installed pen, marker, or pencil
  before plotting.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  38 g target and ±10 g band, with the reasoning comments updated.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  corrected the stale 60 g comment on the hard-force guard.
- `firmware/pen_pressure/README.md`: current force, band, pulse, and hard-limit
  values.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: band and limit values.
- `firmware/README.md`: current single-descend seek and hold band.
- `docs/integration/INTERFACES.md`: toolhead force numbers.
- `docs/testing/TEST_PLAN.md`: T-02 and T-03 acceptance values.
- `docs/project/ENGINEERING_LOG.md`: dated entry for this session.
