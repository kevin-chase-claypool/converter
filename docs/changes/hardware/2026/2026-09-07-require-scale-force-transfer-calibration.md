---
id: HW-20260907-001
date: 2026-09-07
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - HX711/load cell
  - pen-pressure toolhead
  - digital scale fixture
tags:
  - force-calibration
  - hx711
  - grams-force
  - toolhead
  - testing
related:
  - E-07
  - T-01B
  - T-01I
---

# Require scale-force transfer calibration

## Summary

Made the scale-to-filtered-HX711 conversion an explicit E-07 commissioning
requirement. It establishes the measured relationship between pen-tip force in
grams-force and the load-cell signal used by the pressure controller.

## Reason

Raw HX711 counts alone cannot establish a safe writing-force, release, or hard
limit. A physical scale is required to select those thresholds meaningfully.
The measurement must remain distinct from the spring and actuator response,
which may be nonlinear and hysteretic.

## Implementation

E-07 now requires a capped or rigid non-marking dummy tool clamped as a real
pen, at least five gentle scale-force points across the intended operating
range, and at least three load/unload cycles. It requires recording raw and
filtered readings, the signed conversion, residual error, and hysteresis.
T-01B consumes that calibration while characterizing the installed spring.

The force-control current-state document now states that this is a service
calibration and profile-verification step, not a physical-scale procedure for
every print.

## Verification

- Documentation review confirmed that the current integrated firmware uses raw
  HX711 deltas for contact, target, release, and hard-force decisions.
- No firmware constants or commissioning gates were changed; the required
  physical E-07 procedure remains open.

## Struggles and rejected approaches

Treating a motor PWM or actuator-travel value as a force calibration was
rejected. Friction, spring behavior, and hysteresis make that relationship
unsuitable as the force authority.

## Risks and follow-up

The current toolhead firmware still stores provisional raw thresholds and is
commissioning-locked. Perform E-07 with the installed mechanism, then use the
measured conversion to define and validate the profile required by T-01I.

## Files

- `docs/testing/TEST_PLAN.md`: explicit E-07 transfer-calibration procedure
  and T-01B dependency.
- `firmware/pen_pressure/README.md`: current calibration requirement.
