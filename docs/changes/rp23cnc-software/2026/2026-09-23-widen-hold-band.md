---
id: RPSW-20260923-016
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
  - hold
  - force-band
  - reliability
related:
  - RPSW-20260923-004
---

# Widen the force-hold band to ±10 g and move relief to 15 g

## Summary

The target-ready band is widened from ±5 g (30–40 g) to ±10 g (25–45 g), and
the over-force relief trigger moves from 10 g to 15 g above target so it still
sits 5 g beyond the wider band top.

## Reason

The first-print run showed the ±5 g band was too tight for the mechanism's
friction and sensor noise. Long strokes drifted out of band, started a 5 ms
correction, overshot, and entered the retract/re-approach limit cycle; short
strokes never settled before the next M5. The wider band lets the hold tolerate
that drift before correcting, which is appropriate for a non-precision pen
plotter.

## Implementation

- `toolhead_config.h`: `CONTACT_READY_TOLERANCE_RAW` 25,194 -> 50,388 (5 g ->
  10 g) and `HOLD_URGENT_RELIEF_RAW` 50,388 -> 75,582 (10 g -> 15 g). The
  relief still triggers 5 g beyond the band top and stops at the band edge,
  leaving 10 g before the 60 g hard limit. The `activeTargetForceRaw` clamp and
  the hard-limit static assertion still pass.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed (81960 bytes program, 16220 bytes dynamic).
- `python tools\docs_index.py --write` and `--check` pass.
- Bench verification is required: long strokes should stop entering the
  retract/re-approach cycle, and the wider band should reduce spurious
  corrections. T-03 still must record the loop's formal error statistics.

## Struggles and rejected approaches

Widening the band without moving the relief trigger was rejected: with a ±10 g
band the trigger would sit exactly on the band top and fight the normal
correction. Lowering the hard limit for more margin was not considered; it is
an absolute safety ceiling.

## Risks and follow-up

This widens the accepted hold range and moves relief to 50 g, 10 g below the
60 g hard limit. It is a supervised bench choice, not a production qualification;
T-03 is still open. The deeper fixes remain the gentle-landing seek (a bounded
low-PWM creep) and the per-tool force profile.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: band and relief constants.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`, `firmware/pen_pressure/README.md`, `firmware/README.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: document the 25–45 g band and 15 g relief.
