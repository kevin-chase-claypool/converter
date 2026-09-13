---
id: HW-20260913-002
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
  - HW-20260913-001
  - docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md
---

# Add non-motion DRV8833 meter mode

## Summary

E07B now has a `v` command that exposes the actual controller logic levels to
a slow multimeter without commanding N20 movement.

## Reason

The corrected GP6/EEP and GP7/ULT mapping still produced no audible motion
from repeated 100 ms UP pulses, despite continuity from each relevant GPIO and
the shared ground. The existing pulses were too short for the available meter
to capture.

## Implementation

`v` runs two thirty-second stages:

1. GP4 HIGH and GP5 LOW while GP6 keeps the bridge asleep.
2. GP6/EEP HIGH while GP4 and GP5 are both LOW.

The motor bridge cannot receive a drive command in either stage. The sketch
reports the start and end of each measurement window and returns to sleep.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\\pen_pressure\\e07b_hx711_actuator_steps` passed.
- Hardware measurement remains pending after a single E07B reflash.

## Struggles and rejected approaches

Longer energized motor pulses were rejected because the 1000 RPM actuator can
move too far before a slow multimeter has settled. This mode separates logic
measurement from motor output.

## Risks and follow-up

The next required evidence is GP4≈3.3 V / GP5≈0 V during stage 1 and
GP6/EEP≈3.3 V during stage 2, each relative to local driver ground. Those
results determine whether to inspect the driver board or the remaining output
path.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: adds the safe `v` command.
- `firmware/pen_pressure/README.md`: documents the command and its non-motion guarantee.
