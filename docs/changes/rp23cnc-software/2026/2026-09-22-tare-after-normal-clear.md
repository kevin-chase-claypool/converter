---
id: RPSW-20260922-032
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - cs1238
  - tare
  - pen-clear
  - m3-m5
related:
  - RPSW-20260922-031
---

# Refresh Tare after Normal Pen Clear

## Summary

Normal M5 now establishes a new unloaded CS1238 baseline before the next
normal M3 approach.

## Reason

Repeated clear/recontact testing showed that the 100 ms clearance motion shifts
the unloaded raw value. Persistent raw movement after that shift can look like
paper contact even when the pen is physically clear.

## Implementation

After the normal 100 ms UP clearance pulse, the motor sleeps for 50 ms and the
controller collects 64 CS1238 samples into a fresh tare. It then reports
`LIFTED`. The following M3 still discards the prior contact reference and uses
fine-pulse, trend-confirmed contact; it now compares that response with the
new clear-state baseline. Full GP2 home is intentionally excluded and retains
the longer tare-after-GP2-release sequence.

## Verification

- Compiled `firmware/pen_pressure/pro_micro_rp2350_toolhead` for
  `rp2040:rp2040:sparkfun_promicrorp2350` successfully.
- Repeat normal M3/M5 hardware cycles are still required for T-01H/T-02.

## Struggles and rejected approaches

The trend filter was not removed or loosened: the observed change persisted
long enough to satisfy it. Reusing the prior tare was rejected because it
turns a real clearance-induced baseline shift into a false but plausible
contact trend.

## Risks and follow-up

The 50 ms settle and 64-sample count are supervised candidates. Validate that
30 normal non-GP2 M3/M5 cycles complete with visible clearance, a valid clear
tare, and no false contact or hard-force fault before enabling drawing gates.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: add the clear-state tare state.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`: declare the new state and sampling flag.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: define the settle interval.
- `firmware/pen_pressure/README.md`: describe normal-M5 tare behavior.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: record clear-state tare ownership.
- `docs/integration/INTERFACES.md`: update M3/M5 service behavior.
- `docs/testing/TEST_PLAN.md`: add clear-tare acceptance to T-01H/T-02.
