---
id: HW-20260913-008
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/e05_legacy_manual_steps
tags:
  - n20
  - drv8833
  - e-05
  - pulse-duration
  - diagnostics
related:
  - HW-20260913-007
  - HW-20260913-006
---

# Add manual historical E-05 step test

## Summary

The historical E-05 electrical roles are now available through a manual
service-UART sketch with 100 ms through 1000 ms one-direction-at-a-time steps.

## Reason

The owner requested manual duration control for the historical code path before
considering a DRV8833 or perfboard rebuild. The exact automatic historical
source remains available separately for a strict reproduction.

## Implementation

`e05_legacy_manual_steps` preserves the historical `GP4`/`GP5` direction
outputs, `GP6` `INPUT_PULLUP`, and `GP7` high-enable roles. It uses the normal
3.3 V `Serial2` service interface: `u` sends the historical first direction,
`d` the reverse, `[` reduces duration, and `]` increases it. The duration is
clamped to 100--1000 ms in 100 ms increments; there is no automatic reverse
motion. The historical `e05_historical_03f6c00` source is unchanged.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\\pen_pressure\\e05_legacy_manual_steps` passed.
- Physical A/B result remains pending. With clear travel, start at 100 ms and
  increase only one step at a time.

## Struggles and rejected approaches

An exact historical automatic reproduction cannot provide manual duration
control. It is retained unchanged instead of being modified; the manual sketch
is explicitly a separate derivative.

## Risks and follow-up

This historical-role derivative is diagnostic-only. Its `GP6 INPUT_PULLUP` may
also hold the confirmed EEP sleep input high, so a movement result does not
prove that historical `GP7` was the physical sleep signal. It also does not use
the LIFT_HOME switch as a motion stop; keep clear travel and use one pulse at a
time. Compare its result with the corrected E07B test before hardware changes.

## Files

- `firmware/pen_pressure/e05_legacy_manual_steps/e05_legacy_manual_steps.ino`: manual historical-role pulse test.
- `firmware/pen_pressure/README.md`: documents the new staging sketch.
- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`: records the pending differential test.
