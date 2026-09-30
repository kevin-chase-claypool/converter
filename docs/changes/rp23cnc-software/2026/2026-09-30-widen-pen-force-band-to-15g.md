---
id: RPSW-20260930-002
date: 2026-09-30
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - firmware/pen_pressure/README.md
  - docs/testing/TEST_PLAN.md
tags:
  - toolhead
  - force-control
  - pen-force
  - calibration
  - safety
related:
  - RPSW-20260930-001
  - RPSW-20260929-005
  - docs/integration/INTERFACES.md
---

# Widen the 40 g pen-force band back to ±15 g

## Summary

With the drawing-force target left at 40 g, the target-ready band returns from
±10 g to ±15 g, so the hold band is 25-55 g instead of 30-50 g. The 75 g hard
limit is unchanged, and the urgent-relief trigger stays at 60 g.

## Reason

The ±10 g band was set with the 40 g target earlier the same day
(`RPSW-20260930-001`), but ±10 g is the tolerance that was widened to ±15 g on
2026-09-25 after high-speed friction lifted the pen, and a 2026-09-29 ±10 g
trial had already been rejected. The operator chose to keep the lighter 40 g
target and accept the wider band instead.

## Implementation

In `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:

- `CONTACT_READY_TOLERANCE_RAW`: `50388` (±10 g) to `75582` (±15 g), giving
  25-55 g around the 40 g target (`TARGET_FORCE_RAW_DELTA` and
  `CONTACT_RAW_DELTA` stay `201551`).
- `HARD_FORCE_RAW_DELTA` stays `377908` (75 g) and `HOLD_URGENT_RELIEF_RAW`
  stays `100775`, so relief still trips at 60 g - now exactly 5 g beyond the
  band top, as the mechanism's original hysteresis rule intended, and 15 g
  below the hard limit. The `HOLD_BAND_HEADROOM_RAW` clamp still satisfies its
  `static_assert` (75 g > 15 g band + 10 g headroom).

Current-state documents were updated: `firmware/pen_pressure/README.md`,
`firmware/pen_pressure/CONTROL_STRATEGY.md`, `firmware/README.md`,
`docs/integration/INTERFACES.md`, and `docs/testing/TEST_PLAN.md` (T-02, T-03).

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` succeeded
  for `firmware/pen_pressure/pro_micro_rp2350_toolhead`, so the force-envelope
  `static_assert` accepts the restored band.
- `python tools\docs_index.py --write` and `--check` pass.
- No bench test. The toolhead must be re-flashed, and the setting is not
  verified until T-02 and T-03 run on the installed pen.

## Struggles and rejected approaches

Keeping the ±10 g band with the lower 40 g target was rejected: the band's top
was never the part that failed on 2026-09-25, the whole tolerance was, and a
third narrow-band attempt would repeat experiments that have already failed
twice.

## Risks and follow-up

- The light edge moves to 25 g, 5 g below the previously validated 30 g bottom,
  so light marking is new ground; T-02/T-03 must confirm the pen still marks
  acceptably when the hold settles near the bottom of the band.
- The band is 30 g wide, so the pen may hold anywhere in 25-55 g; that is the
  tolerance the mechanism's friction needs, not a precision setting.
- The constants are compile-time: nothing changes until the Pro Micro is
  re-flashed.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: ±15 g
  band with the decision recorded in the comments.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`,
  `firmware/README.md`: band and relief values.
- `docs/integration/INTERFACES.md`: toolhead force values.
- `docs/testing/TEST_PLAN.md`: T-02 and T-03 acceptance values.
- `docs/project/ENGINEERING_LOG.md`: dated entry for this session.
