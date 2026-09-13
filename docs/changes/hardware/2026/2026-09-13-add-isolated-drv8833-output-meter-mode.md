---
id: HW-20260913-003
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
  - toolhead
  - diagnostics
  - e-14c
related:
  - HW-20260913-002
  - docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md
---

# Add isolated DRV8833 output meter mode

## Summary

E07B now has an `o` command that holds both DRV8833 output polarities for a
slow multimeter after the N20 leads are removed from OUT1 and OUT2.

## Reason

E07B `v` mode proved the controller-side levels at the installed harness:
GP4=3.3 V, GP5=0 V, and GP6/EEP=3.3 V relative to driver ground. Repeated
energized 100 ms pulses still produced no actuator response. The output stage
therefore needs an isolated measurement, but holding a connected 1000 RPM N20
would be unsafe.

## Implementation

With an explicit warning, `o` enables the driver and holds IN1/IN2 forward for
30 seconds, then reverse for 30 seconds, before sleeping the driver. It checks
ULT before and between the two stages. It is forbidden while either motor lead
is attached.

## Verification

- N20 leads were reported disconnected before this command was added.
- Compile and hardware voltage evidence remain pending.

## Struggles and rejected approaches

Testing the bridge output while the N20 remained connected was rejected because
the motor could travel or stall while the slow meter settles.

## Risks and follow-up

Reflash E07B. During the first stage expect OUT1≈VM and OUT2≈0 V; during the
second expect OUT1≈0 V and OUT2≈VM, all relative to driver ground. A different
result isolates a DRV8833 board/output or input-landing failure.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: adds guarded `o` output meter mode.
- `firmware/pen_pressure/README.md`: documents its motor-disconnected boundary.
