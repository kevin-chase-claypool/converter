---
id: HW-20260913-005
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/e07b_hx711_actuator_steps
tags:
  - drv8833
  - fault
  - diagnostics
  - toolhead
related:
  - HW-20260913-004
  - docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md
---

# Add DRV8833 loaded-fault telemetry

## Summary

E07B now samples the active-low ULT fault line after enabling the driver and
again while a `u` or `d` pulse is active.

## Reason

The controller-side logic and unloaded driver outputs passed, but the connected
N20 still did not move. The earlier sketch checked ULT only before enabling the
bridge, so a protection trip occurring after the motor load was applied could
be hidden when the sketch immediately returned the driver to sleep.

## Implementation

Each manual pulse now cancels with an explicit message if ULT is active after
the enable delay. After the commanded pulse it prints
`fault_during_drive=<0|1> raw=<0|1>` before sleeping the driver.

## Verification

- Compile pending for the updated E07B sketch.
- Hardware result pending one 20 ms `u` pulse with the N20 connected.

## Struggles and rejected approaches

The unloaded output-voltage test cannot establish current capability. A long
loaded pulse was rejected because it could damage the mechanism; the existing
20 ms pulse plus synchronous fault sampling is the safer discriminator.

## Risks and follow-up

If `fault_during_drive=1`, investigate motor load/current limit or replace the
driver. If it remains zero, the next focus is a high-resistance board-side
motor connection or bridge current capability under load.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: samples and reports ULT during loaded pulse.
