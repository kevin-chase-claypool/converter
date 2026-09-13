---
id: HW-20260913-006
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/e07b_hx711_actuator_steps
tags:
  - n20
  - toolhead
  - pulse-duration
  - diagnostics
related:
  - HW-20260913-005
  - docs/testing/TEST_PLAN.md
---

# Extend E07B actuator pulse range

## Summary

E07B no longer caps manual `u`/`d` actuator pulses at 100 ms. The operator can
adjust from 100 ms to a guarded maximum of 1000 ms in 100 ms steps.

## Reason

The installed 1000 RPM N20 moves the carriage on sustained direct 6 V, but
repeated 100 ms controller pulses do not show motion. The earlier 100 ms cap
was an arbitrary service-test restriction, not a measured safe or effective
limit for the replacement motor.

## Implementation

`[` and `]` now change duration by 100 ms and clamp safely at 100 ms and 1000 ms.
The finite one-second ceiling remains because E07B reports LIFT_HOME but does
not use it to stop actuator motion. Its help text and source comments state
that the shortest effective pulse must be used with clear travel.

## Verification

- Compile pending for the adjusted E07B sketch.
- First hardware use: position the carriage safely away from the selected
  direction's endpoint, use the default 100 ms pulse, then use `]` for one
  200 ms manual `u` or `d` pulse and retain ULT telemetry.

## Struggles and rejected approaches

Removing every duration ceiling was rejected because the current service sketch
has no firmware-enforced motion stop at LIFT_HOME. The 1000 ms guard permits
meaningful breakaway testing without authorizing indefinite energization.

## Risks and follow-up

Do not run `a` during this characterization. If 245 ms moves the carriage,
bracket the shortest repeatable breakaway duration before force testing. If it
does not, compare loaded driver voltage/current against the direct-6-V result.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: expands and safely clamps manual pulse duration.
