---
id: RPSW-20260923-009
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
  - learning
related:
  - RPSW-20260923-008
---

# Learn warm-seek travel to traverse it with coarse pulses

## Summary

The first warm M3 after boot runs fine-only to measure the clearance distance;
later warm M3s traverse most of that learned distance with 25 ms coarse pulses,
keeping a fine reserve for the final approach. The learned distance is a moving
average, so it tracks clearance drift.

## Reason

The single-descend seek removed the tune but left warm M3 at 22-26 pulses,
because most of them close the roughly 1.75 mm M5 clearance gap with 5 ms
pulses. A 25 ms coarse pulse travels about five times as far, so replacing most
of the gap-closing fine pulses with coarse pulses reduces the per-stroke pulse
count without changing the physical clearance.

## Implementation

- `toolhead_config.h`: added `SEEK_WARM_COARSE_RATIO` (5), the number of fine
  pulses a 25 ms coarse pulse replaces; `SEEK_WARM_FINE_RESERVE` (8), the fine
  pulses kept for the final approach; and `SEEK_WARM_MAX_COARSE_PULSES` (8) as a
  hard cap. These are supervised bench candidates.
- `pressure_controller.h`: added the warm-seek flag, the travel moving average,
  and the per-seek coarse budget and usage counters.
- `pressure_controller.cpp`: the first warm M3 after boot is fine-only and
  measures the travel. On later warm M3s the controller computes a coarse budget
  from the average, uses coarse pulses while under budget and below the 1 g
  force threshold, and otherwise uses fine pulses. On a completed warm seek it
  folds the total travel (coarse pulses weighted by the ratio plus fine pulses)
  into a 1/4-alpha moving average.
- `pro_micro_rp2350_toolhead.ino`: added `warm_ema` to telemetry so the learned
  travel is visible.

The cold-start coarse phase is unchanged and remains force-threshold limited
rather than budget limited.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 81776 bytes program storage and 16220 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench verification is required. Expected: the first warm M3 stays fine-only,
  then `warm_ema` stabilises around the measured fine-pulse-equivalent travel
  and subsequent warm M3s use roughly that divided by five coarse pulses.

## Struggles and rejected approaches

A fixed coarse budget was rejected because the clearance drifts and a fixed
distance either overshoots when the gap shrinks or under-travels when it grows.
The moving average follows the drift. Automatically shrinking the learned
distance after a hard-force trip was deferred; it is a worthwhile safety
follow-up but not part of this first increment.

## Risks and follow-up

A coarse pulse that lands on paper can blow through the 60 g hard limit, so the
coarse phase is deliberately conservative: an 8-pulse fine reserve, a hard cap,
and the 1 g force-threshold early stop all end the coarse phase before contact.
The moving average resets on every boot, so the first warm cycle of each
session is always the measuring pass. It is not reset per pen; per-tool
re-learning belongs in the T-01J preflight.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: learning constants.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`: learning state.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: coarse budget and travel moving average.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: `warm_ema` telemetry.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`: describe the learned travel.
