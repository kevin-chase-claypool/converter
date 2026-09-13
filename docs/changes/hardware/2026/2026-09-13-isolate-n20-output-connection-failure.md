---
id: HW-20260913-004
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - firmware/pen_pressure/e07b_hx711_actuator_steps
  - hardware/toolhead-actuator
tags:
  - drv8833
  - n20
  - toolhead
  - diagnostics
related:
  - HW-20260913-003
  - docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md
---

# Isolate N20 output-connection failure

## Summary

The disconnected-N20 output test proved the DRV8833 switches both polarities.
The N20 direct-6-V result and failed installed pulses therefore isolate the
remaining defect to the physical OUT1/OUT2-to-N20 connection path.

## Reason

Correct GP4, GP5, and GP6 logic levels did not move the installed 1000 RPM
N20. The owner then removed both N20 leads and reported the expected output
voltages in both `o` meter-mode polarities.

## Implementation

No controller or GP4–GP7 wiring change is needed. With power removed, inspect,
re-terminate, or resolder only the two N20 motor leads and their OUT1/OUT2
connections, then repeat a guarded pulse.

## Verification

- Isolated driver stage: passed, owner reported the four expected output
  readings in the two 30-second meter windows.
- N20: previously ran when powered directly at 6 V.
- Installed driver-to-N20 path: failed, no response to repeated 100 ms UP
  pulses before the motor leads were removed.

## Struggles and rejected approaches

Repeated firmware pin-map corrections and longer pulses did not restore motion.
The isolated output test avoided needlessly replacing the healthy DRV8833.

## Risks and follow-up

Power off before rework. Do not touch GP4–GP7. After the two motor connections
are repaired, reconnect them and verify a single short `u` pulse before any
automatic force or scale test.

## Files

- `docs/hardware/WIRING_TABLE.md`: marks the motor-output branch for repair.
- `docs/testing/TEST_PLAN.md`: records the passed isolated driver test and
  remaining actuator-connection repair.
