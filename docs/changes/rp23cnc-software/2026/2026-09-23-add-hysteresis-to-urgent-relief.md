---
id: RPSW-20260923-004
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
  - hunting
related:
  - RPSW-20260923-002
  - RPSW-20260923-003
---

# Add hysteresis to the urgent over-force relief

## Summary

The urgent over-force relief no longer triggers at the band edge, and it now
stops at the band edge instead of at target. It engages only above 10 g of
excess force and leaves 5 g of hysteresis.

## Reason

The first form of the relief (`RPSW-20260923-002`) set
`HOLD_URGENT_RELIEF_RAW` to 25,194 raw, which is exactly
`CONTACT_READY_TOLERANCE_RAW`. Its trigger was therefore the band edge itself,
and its stop condition was the target a full band below it. Any excursion past
the band started a continuous retract with no trend confirmation and no
hysteresis, retracting a full band-width, after which the loop had to rebuild
force with a 5 ms pulse per ~325 ms. That is a retract/rebuild limit cycle, and
it matches the operator report that the pen "keeps poking over and over and
over and never holds" - the same hunting behaviour `RPSW-20260922-031` added
the trend gate to suppress.

## Implementation

- `toolhead_config.h`: `HOLD_URGENT_RELIEF_RAW` raised from 25,194 to 50,388
  raw, so the trigger sits 5 g beyond the band edge rather than exactly on it.
  `HOLD_URGENT_RELIEF_MAX_MS` is unchanged at 200 ms.
- `pressure_controller.cpp`: the relief stop condition changed from
  `force <= target` to `force <= target + CONTACT_READY_TOLERANCE_RAW`, so
  relief ends at the band edge and 5 g of hysteresis separate the trigger and
  the stop.

The target clamp keeps the band top 10 g below the hard limit, so a trigger at
band edge plus 5 g still leaves about 5 g before the 60 g trip.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 82448 bytes program storage and 16236 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- A 2026-09-23 nine-cycle bench run on this build completed with no faults. The
  relief engaged nine bounded times in the cold-start cycle (199 ms total) to
  recover a hold entry 13.3 g above target, then stayed flat across the eight
  following cycles. See
  [`2026-09-23-t-02-hysteresis-relief-nine-cycle-run`](../../../report/lab-notes/2026-09-23-t-02-hysteresis-relief-nine-cycle-run.md).
- The relief stopping and restarting nine times in that cycle shows the
  stop-at-band-edge condition can re-trigger while the mechanism is still
  rising. It converged, but a single retract would be preferable.

## Struggles and rejected approaches

Removing the relief entirely was considered, since its first form caused the
hunting it was meant to prevent. It was kept because the underlying problem -
two hard-limit trips from post-hold force rise - is real and the bounded
retract is the only mechanism available to answer it. Raising the trigger
alone was rejected: without also moving the stop condition to the band edge
there would still be no hysteresis.

## Risks and follow-up

The 10 g trigger is a supervised bench candidate derived from the observed
held-force spread of about 2.6 g across five cycles; it needs repeat evidence.
If the pen still hunts, the next step is to require the excursion to persist
for a short confirmation interval before relief engages, rather than lowering
the trigger again. If the force now runs away without relief engaging, the
trigger is too high and the mechanical stored-energy release is the limiting
factor.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: raise the relief trigger clear of the band.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: stop relief at the band edge.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: document the trigger and hysteresis.
