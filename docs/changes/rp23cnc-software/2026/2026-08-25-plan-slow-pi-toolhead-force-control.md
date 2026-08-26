---
id: RPSW-20260825-001
date: 2026-08-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: planned
components:
  - firmware/pen_pressure
  - docs/testing/TEST_PLAN.md
tags:
  - toolhead
  - load-cell
  - n20
  - force-control
  - pi
related:
  - E-05
  - E-06
  - E-07
  - E-08
  - T-01
  - T-03
---

# Plan Slow PI Toolhead Force Control

## Summary

Defined the planned toolhead pressure controller as a bounded, pulse-based P/PI
trim loop. It uses mechanical compliance for fast vibration and the slow force
loop for uneven-bed compensation.

## Reason

The 18-inch printed rotating bed may have repeatable and non-repeatable height
variation, while the N20 gearbox/lead screw has friction and backlash. E-08
measured only 11.93 HX711 samples per second, so a high-bandwidth PID cannot
reliably reject pen vibration.

## Implementation

The current-state toolhead document now specifies normalized force units,
deadband, bounded direction pulses, a leaky integral term with anti-windup, and
post-pulse settling. Derivative control is excluded from the initial design.
It also defines stationary, translation, and rotating-bed characterization,
plus a later optional angle/radius feed-forward map only after PI behavior is
proven.

## Verification

Documentation-only planning change. No firmware constant was enabled and no
motor, driver, or force test was performed. `T-03` now names the required
profiles and evidence.

## Struggles and rejected approaches

A conventional fast PID was rejected for the initial implementation because
the measured sensor/filter/correction cadence cannot support vibration
rejection, and derivative action would amplify the relevant noise.

## Risks and follow-up

E-06, E-07, T-01, and T-02 must establish safe electrical limits, force
calibration, pulse response, and stiction before any production gain is
selected. The known Z-dependent preload prohibits reusing an old tare after
travel.

## Files

- `firmware/pen_pressure/README.md`: planned control architecture and tuning sequence.
- `docs/testing/TEST_PLAN.md`: expanded T-03 pass condition and evidence.
