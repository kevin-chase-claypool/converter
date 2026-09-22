---
id: RPSW-20260922-031
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
  - moving-average
  - force-control
  - stiction
related:
  - RPSW-20260922-030
---

# Trend-gate Force-hold Corrections

## Summary

The force-hold loop now waits for a persistent directional drift before making
one bounded correction in either direction.

## Reason

An immediate high-side correction let individual rolling-average deviations
repeatedly move the N20, making the pen visibly probe rather than settle.

## Implementation

Outside the 30–40 g deadband, three observations in the same direction and
25 ms apart are required. A qualifying trend may issue one 5 ms UP or DOWN
pulse only if 250 ms have elapsed since the previous hold correction. Each
pulse sleeps the driver and resets trend evidence.

## Verification

- Arduino CLI compile is required for the SparkFun Pro Micro RP2350 target.
- Supervised stationary T-03 must confirm the tip rests instead of hunting.

## Risks and follow-up

The approximately 75 ms trend delay and 250 ms cadence are deliberately
non-precision values selected for a coarse actuator. Revise only from observed
hold stability and visible line quality.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `firmware/pen_pressure/CONTROL_STRATEGY.md`
