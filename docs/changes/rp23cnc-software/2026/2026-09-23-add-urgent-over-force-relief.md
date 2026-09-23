---
id: RPSW-20260923-002
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - t03
  - force-control
  - hold
  - hard-limit
related:
  - RPSW-20260923-001
---

# Add bounded urgent over-force relief to the hold loop

## Summary

`HOLD_FORCE` now answers a large over-force with a bounded continuous retract
instead of waiting out the trend gate and the 250 ms correction cadence.

## Reason

The 2026-09-23 T-02 follow-up run reached `HOLD_FORCE` in band
(`force_norm_raw=203297`, `contact_ref_raw=49314`, `ready=[contact:1 ...]`)
and then faulted with `hard force limit exceeded` at 302,536 raw. The force
rose 99,239 raw, about 20 g, after hold had been established.

The existing hold loop can only issue one 5 ms full-drive pulse per trend
window plus a 250 ms cadence, which is roughly 15 ms of drive authority per
second. That is far too little to retract against a mechanism releasing stored
energy, which is consistent with the observed long low-gain tune (79 pulses)
immediately preceding the run-away. The band-position clamp added in
`RPSW-20260923-001` did not apply to this cycle: its 49,314 raw reference sits
below the 50,387 raw clamp threshold.

## Implementation

- `toolhead_config.h`: added `HOLD_URGENT_RELIEF_RAW` (25,194 raw, about 5 g of
  excess) and `HOLD_URGENT_RELIEF_MAX_MS` (200 ms).
- `pressure_controller.cpp`: in `HOLD_FORCE`, when the held force exceeds the
  target by more than the urgent threshold, the controller drives UP
  continuously and stops as soon as the force is back at target or the bound
  expires. The relief bypasses the trend gate and the correction cadence.
- `pressure_controller.h`: added the relief state and its start timestamp, both
  cleared when leaving `HOLD_FORCE`.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 82344 bytes program storage and 16228 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- A 2026-09-23 five-cycle bench run on this build completed with no faults and
  no hard-force trip: first-touch reference spread 12,290 raw (about 2.4 g) and
  held-force spread 12,943 raw (about 2.6 g). See
  [`2026-09-23-t-02-five-cycle-clean-pass`](../../../report/lab-notes/2026-09-23-t-02-five-cycle-clean-pass.md).
- That run does not confirm the relief itself. It emits no state event, all
  five snapshots sat below target, and the relief was therefore never observed
  activating. Direct bench verification of the relief remains open.

## Struggles and rejected approaches

Raising the correction cadence or lengthening the bounded 5 ms pulse was
rejected as a first step. Both scale the same pulse mechanism and cap out at
low authority, while a continuous move is what actually retracts the
mechanism. Widening the hold band was also rejected because it would accept a
larger force error without improving recovery.

## Risks and follow-up

The relief is retract-only, so it can only reduce force, but 200 ms of
continuous full-drive UP is a new motion mode in `HOLD_FORCE` and must be
verified for overshoot and hunting on the bench. The stop condition is the
target force rather than the band edge, which deliberately leaves 5 g of
hysteresis against re-triggering. The underlying cause — a mechanism that
stores and releases energy over a long low-gain contact approach — remains
open, and is also the reason the linear-rail carriage replacement is under
consideration.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: add the relief threshold and bound.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`: add relief state.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: urgent relief in `HOLD_FORCE`.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: document the relief path.
