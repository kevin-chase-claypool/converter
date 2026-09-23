---
id: RPSW-20260923-008
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - t02
  - contact-seek
  - performance
  - simplification
related:
  - RPSW-20260923-006
---

# Replace the two-touch seek with a single descend

## Summary

M3 no longer performs the light-touch detection, 10 ms back-off, and force
retune. It is now one bounded descend from the fresh clear-state tare to the
absolute 35 g target band.

## Reason

The two-touch existed to cancel the load cell's position-dependent mechanism
preload by measuring force relative to a per-stroke first-touch reference. That
work became unnecessary once the controller gained a clear-state tare after
every M5, a measured 300 ms settle, and an absolute target with a band-headroom
clamp. The two-touch was also the dominant per-stroke latency cost, requiring
22-30 pulses per warm M3.

## Implementation

- `HOME_RETRACT_AFTER_TOUCH` and `HOME_TUNE_FORCE` states removed, along with
  the contact-reference bookkeeping, the surface-confirm trend logic, and the
  two-touch configuration constants.
- `HOME_SEEK_CONTACT` now steps DOWN with 25 ms coarse pulses while far from the
  paper and 5 ms fine pulses once force rises above about 1 g, then enters
  `HOLD_FORCE` when the settled force crosses
  `activeTargetForceRaw() - CONTACT_READY_TOLERANCE_RAW`.
- `activeTargetForceRaw()` is now a plain clamped absolute target instead of a
  reference-plus-target sum.
- Telemetry drops `home_tune_pulses`, `contact_ref_raw`, and
  `contact_ref_valid`; `home_seek_pulses` remains as the seek progress counter.

The coarse cold-start phase, the GP2 release tare, the hold loop, the urgent
relief, the band-headroom clamp, the hard-force guard, and the CS1238 rejection
are unchanged.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 81584 bytes program storage and 16212 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- A 2026-09-23 ten-cycle bench run on this build completed with no faults. The
  cold start dropped from 74 to 56 pulses, but warm M3 stayed at 22-26 pulses
  because the M5 clearance gap, not the tune, dominates. Held force spread was
  27,143 raw (5.4 g), wider than the two-touch's 2.7 g, because the seek
  overshoots its threshold and the hold loop and relief correct it down. See
  [`2026-09-23-t-02-single-descend-ten-cycle-run`](../../../report/lab-notes/2026-09-23-t-02-single-descend-ten-cycle-run.md).

## Struggles and rejected approaches

A compile-time switch between the two strategies was rejected. Keeping both
paths would preserve dead machinery the change is meant to remove, and the
previous version is recoverable from git history (commit `1915188`) if the
clearance proves non-repeatable.

## Risks and follow-up

This depends on M5 leaving a repeatable clearance, which T-01H has not yet
proven. If the clearance wanders, the bounded descend will land at a different
force each stroke. The absolute 35 g target is lighter than the previous
reference-plus-35 g result and may need to be raised for acceptable line
weight. The 100-pulse budget and 60 second timeout remain in place, so a
non-contacting descend still fails safely.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`: remove the two-touch states, reference, and confirm members.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: single-descend seek and absolute target.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: remove the two-touch constants and tune assertion.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: telemetry without tune and reference fields.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: describe the single descend.
