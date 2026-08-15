---
id: HW-20260815-001
date: 2026-08-15
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/BOM.md
  - docs/testing/TEST_PLAN.md
tags:
  - tb6600
  - stepper-driver
  - microstepping
  - current-limit
related:
  - docs/report/lab-notes/2026-08-15-e-02-tb6600-factory-switch-observation.md
---

# Record TB6600 factory switch state

## Summary

Recorded the reported TB6600 factory six-switch state as SW2/SW4 ON and all
other switches OFF.

## Reason

Factory switch states must be recorded before selecting safe motor current and
motion calibration values.

## Implementation

The received driver's printed table maps the reported state to 8 microsteps and
2.0 A.
The selected motors are rated 1.5 A per phase, so the documented target is the
printed 1.5 A row, SW4 ON/SW5 ON/SW6 OFF, after each received unit's table is
confirmed.

## Verification

This is a project-owner observation only. E-02 remains partial pending visual
confirmation of all three units; E-04 remains required before motor power.

## Struggles and rejected approaches

The initial transcription used a blurry earlier image and incorrectly mapped
the factory microstep setting and 1.5 A row. A clear photograph of the received
label corrected both entries before any switch setting was changed.

## Risks and follow-up

Clone TB6600 drivers can use different switch tables. Confirm the table printed
on each received unit before applying the 1.5 A setting.

## Files

- `docs/hardware/BOM.md`: received driver-state record and next action.
- `docs/testing/TEST_PLAN.md`: E-02 partial evidence.
- `docs/report/lab-notes/2026-08-15-e-02-tb6600-factory-switch-observation.md`: observation record.
