---
id: HW-20260913-009
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - hardware/toolhead/DRV8833
  - firmware/pen_pressure/e07b_hx711_actuator_steps
tags:
  - drv8833
  - n20
  - solder-repair
  - e-14c
related:
  - HW-20260913-001
  - HW-20260913-008
---

# Repair DRV8833 output solder joint

## Summary

The toolhead DRV8833 output failure was traced to an unsoldered driver pin.
After reflowing that joint, the installed 1000 RPM N20 moved in both directions
under corrected E07B `u` and `d` commands.

## Reason

The controller and bridge had passed static logic and open-circuit output
tests, yet the connected motor received only a millivolt transient and did not
move even during one-second manual pulses.

## Implementation

With power removed, the owner repaired the identified DRV8833 pin-to-board
solder joint. No GP4--GP7 wiring or firmware mapping changed.

## Verification

- `e07b_hx711_actuator_steps` was flashed with the corrected GP6/EEP enable
  and GP7/ULT fault roles.
- Connected-motor `u` and `d` commands both produced physical N20 motion.

## Struggles and rejected approaches

The historical E-05 roles and longer pulses were exercised as an A/B test but
did not restore motion. Static output voltage alone was misleading because the
open output passed while the defective solder joint prevented loaded delivery.

## Risks and follow-up

Bidirectional motion proves the immediate output path but not safe travel,
direction naming, LIFT_HOME behavior, force calibration, or force limits.
Continue the T-01 actuator characterization with short manual pulses and clear
travel before mounting or pressing a pen onto a scale.

## Files

- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`: records root cause and result.
- `docs/project/ENGINEERING_LOG.md`: records the verified repair milestone.
