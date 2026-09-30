---
id: RPSW-20260930-001
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
  - RPSW-20260929-004
  - RPSW-20260929-005
  - docs/integration/INTERFACES.md
---

# Set the pen force target to 40 g with a ±10 g band

## Summary

The integrated toolhead's drawing-force target drops from 45 g to 40 g and its
target-ready band narrows from ±15 g to ±10 g, giving a 30-50 g hold band. The
75 g hard limit is unchanged; because the relief offset stays 20 g above target,
the urgent-relief trigger moves from 65 g to 60 g.

## Reason

The operator decided on 40 g ±10 g after the 2026-09-29 38 g / ±10 g trial was
rejected and the 45 g / ±15 g setting was restored. This keeps the lower band
edge where it was (30 g) and lowers the upper edge from 60 g to 50 g, so the
hold can no longer sit at the heavier end of the old band.

## Implementation

In `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`, at the
E-09C scale of 5,038.77 raw/g:

- `TARGET_FORCE_RAW_DELTA` and `CONTACT_RAW_DELTA`: `226745` (45 g) to
  `201551` (40 g). The same value appears in the supervised E-09F sketch's 40 g
  row, which uses the same calibration.
- `CONTACT_READY_TOLERANCE_RAW`: `75582` (±15 g) to `50388` (±10 g).
- `HARD_FORCE_RAW_DELTA` stays `377908` (75 g) and `HOLD_URGENT_RELIEF_RAW`
  stays `100775` (20 g above target), so relief now trips at 60 g - 10 g beyond
  the band top and 15 g below the hard limit. The `HOLD_BAND_HEADROOM_RAW`
  clamp still satisfies its `static_assert` (75 g > 10 g band + 10 g headroom).

Current-state documents were updated to the new numbers:
`firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`,
`firmware/README.md`, `docs/integration/INTERFACES.md`, and
`docs/testing/TEST_PLAN.md` (T-02, T-03).

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` succeeded
  for `firmware/pen_pressure/pro_micro_rp2350_toolhead`, so the force-envelope
  `static_assert` accepts the new values.
- `python tools\docs_index.py --write` and `--check` pass.
- No bench test. The toolhead must be re-flashed, and the setting is not
  verified until T-02 and T-03 run on the installed pen.

## Struggles and rejected approaches

Returning to a ±10 g band re-enters the tolerance that was widened to ±15 g on
2026-09-25 because high-speed friction spiked past the band top and lifted the
pen. The 2026-09-30 choice lowers the band top from 60 g to 50 g, which reduces
marking force but leaves that lift risk in place; it is accepted deliberately
and must be re-checked on the machine rather than assumed.

## Risks and follow-up

- The ±10 g band was widened back to ±15 g later the same day by
  `RPSW-20260930-002`; the 40 g target from this note stands.
- Unverified on hardware. Watch for the pen lifting on fast strokes (the
  2026-09-25 failure mode) and for light marking at 40 g; if either appears,
  adjust the band or the hold cadence rather than reverting silently.
- The urgent-relief trigger is now 60 g, 10 g above the band top. If relief
  should engage sooner, lower `HOLD_URGENT_RELIEF_RAW` toward 15 g of offset
  (55 g) as a separate, separately verified change.
- The constants are compile-time: nothing changes until the Pro Micro is
  re-flashed.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: 40 g
  target and ±10 g band, with the decision recorded in the comments.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`,
  `firmware/README.md`: band, target, and relief values.
- `docs/integration/INTERFACES.md`: toolhead force values.
- `docs/testing/TEST_PLAN.md`: T-02 and T-03 acceptance values.
- `docs/project/ENGINEERING_LOG.md`: dated entry for this session.
