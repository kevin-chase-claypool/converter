---
id: HW-20260913-010
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - firmware/pen_pressure/e07b_hx711_actuator_steps
tags:
  - n20
  - drv8833
  - direction
  - e-07b
related:
  - HW-20260913-009
---

# Calibrate E07B N20 direction

## Summary

Corrected E07B now makes `u` physically lift the pen carriage and `d`
physically lower it without changing the installed motor wiring.

## Reason

After the DRV8833 solder repair restored powered motion, the owner verified
that the prior E07B `u` command moved downward and `d` moved upward.

## Implementation

The two E07B IN1 polarity constants were swapped: `IN1 LOW` is now declared
the lift direction and `IN1 HIGH` the lower direction. The automatic approach
continues to use the lower-direction constant, so its physical direction is
corrected too. The source command comments now describe the selected duration
rather than the obsolete 20 ms value.

## Verification

- Owner physical observation before correction: `u` moved down; `d` moved up.
- Source compile passed for the SparkFun Pro Micro RP2350 target.
- Reflash and one guarded physical confirmation of corrected `u`/`d` naming
  remain required before scale-contact testing.

## Struggles and rejected approaches

Swapping the motor wires was rejected; the owner requested a code-only polarity
correction and the wiring is otherwise verified.

## Risks and follow-up

This establishes command naming only. It does not establish LIFT_HOME,
mechanical travel limits, safe preload, force sign, or force limits.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: corrected command polarity.
- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`: records installed direction evidence.
