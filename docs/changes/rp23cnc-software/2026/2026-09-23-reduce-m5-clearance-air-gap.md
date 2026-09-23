---
id: RPSW-20260923-011
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - m5
  - clearance
  - performance
related:
  - RPSW-20260923-009
---

# Reduce the M5 clearance air gap to about 1 mm

## Summary

`PEN_CLEAR_EXTRA_LIFT_MS` drops from 100 ms to 57 ms, targeting about 1 mm of
clearance instead of about 1.75 mm, so the next M3 has less empty travel to
close.

## Reason

E-09F measured about 1.75 mm of gap per 100 ms of UP drive. That gap is the
largest share of the warm-seek travel, so shortening it cuts the number of
transit pulses each M3 needs. The warm-seek moving average absorbs the change
automatically: the first warm M3 after flashing re-measures the shorter travel
and later cycles use it.

## Implementation

`toolhead_config.h`: `PEN_CLEAR_EXTRA_LIFT_MS` 100 -> 57, with the 1.75 mm per
100 ms conversion recorded in the comment.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 81784 bytes program storage and 16220 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- A 2026-09-23 eight-cycle bench run on this build completed with no faults. The
  first warm M3 re-measured 22 pulses and `warm_ema` then converged to about 13;
  steady-state warm seek dropped from 13-16 pulses to 7-9, about 2.2-2.8 s. See
  [`2026-09-23-t-02-one-mm-clearance-run`](../../../report/lab-notes/2026-09-23-t-02-one-mm-clearance-run.md).

## Struggles and rejected approaches

The 1 mm figure is still a candidate. It is derived from a single E-09F
measurement rather than a direct measurement of the installed clearance, which
is T-01H's job.

## Risks and follow-up

The clearance must stay larger than paper and bed height variation or the pen
drags during pen-up travel. One millimetre is a smaller margin than before, so
T-01H's 30-cycle no-drag check matters more, not less. The 1.75 mm per 100 ms
ratio is a single observation and the motor is not servo-controlled, so the
actual gap can vary.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: clearance lift constant.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: align the documented clearance.
