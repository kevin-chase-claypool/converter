---
id: RPSW-20260922-024
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
  - docs/testing/TEST_PLAN.md
tags:
  - cs1238
  - force-hold
  - n20
  - safety
related:
  - RPSW-20260922-022
  - RPSW-20260922-023
---

# Bound Moving-Average Hold Pulses

## Summary

The integrated toolhead's moving-average force hold now uses individual 5 ms
motor corrections, rather than leaving a proportional PWM output energized
between 250 ms decisions.

## Reason

The post-home-tare home seek correctly reached the 35 g target at 177,917 raw,
then exceeded the unchanged 60 g hard limit by only 294 raw. The operator
reported physically appropriate paper contact at the hold transition. That
isolated the unsafe excess motion to the previous continuous hold command.

## Implementation

`HOLD_FORCE` sleeps in the calibrated 30–40 g band. Above band it applies one
5 ms UP relief pulse immediately. Below band it applies one 5 ms DOWN pulse no
more often than every 250 ms. Each correction stops and sleeps before another
filtered decision. The independent 60 g hard-force guard remains active.

## Verification

- Arduino CLI compile passed for
  `firmware/pen_pressure/pro_micro_rp2350_toolhead` with the SparkFun Pro
  Micro RP2350 target.
- Bench evidence records valid clear-home tare, GP2 release, target contact,
  and the retained hard-force fault in
  `docs/report/lab-notes/2026-09-22-t-02-home-contact-seek-setup.md`.

## Struggles and rejected approaches

Keeping the original continuous proportional PWM was rejected because its
effective drive duration was controlled by the 250 ms sampling cadence, not a
mechanical motion bound. Lowering the calibrated target or increasing the
hard-force limit would hide that defect rather than constrain it.

## Risks and follow-up

The new pulse sizes and bands are supervised bench values. Run stationary
T-02/T-03 with physical cutoff access, then test motion disturbances before
connecting the production M3/M5 harness or claiming drawing readiness.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  bounded hold state behavior.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`:
  bounded hold pulse state.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  hold pulse constants.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: current control contract.
