---
id: HW-20260909-001
date: 2026-09-09
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: partial
components:
  - toolhead carriage
  - LIFT_HOME microswitch
  - N20 actuator
tags:
  - toolhead
  - lift-home
  - t-01g
  - commissioning
related:
  - HW-20260908-004
  - RPSW-20260909-001
---

# Verify guarded lift-home repeatability

## Summary

The installed GP2 LIFT_HOME switch passed ten guarded powered retract/release
cycles using bounded, self-sleeping actuator pulses.

## Reason

T-01G requires observed switch polarity and repeatability before GP2 can serve
as a position reference.

## Implementation

At 6.0 V with a 0.20 A supply limit and 20 ms pulses, every observed cycle
released after six down pulses and first asserted after nine up/retract pulses.
The carriage flag visibly pressed the switch at `lift_home=1`; three stationary
pressed reads remained asserted.

## Verification

See `docs/report/lab-notes/2026-09-09-t-01g-guarded-retract-cycles.md` and
T-01G in `docs/testing/TEST_PLAN.md`.

## Struggles and rejected approaches

The native-USB-only motor bench sketch was unsuitable for normal 6 V toolhead
power plus COM8 service-UART. GP2 status was added to the existing bounded
pulse sketch rather than using continuous movement near the switch.

## Risks and follow-up

This does not establish LIFT spring position, switch-to-backstop margin,
released-state debounce for every cycle, or a missing-trigger timeout/fault.
GP2 remains telemetry-only.

## Files

- `docs/report/lab-notes/2026-09-09-t-01g-guarded-retract-cycles.md`: primary bench evidence.
- `docs/testing/TEST_PLAN.md`: T-01G current state.
