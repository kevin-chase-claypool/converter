---
id: RPSW-20260909-002
date: 2026-09-09
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - Pro Micro RP2350 toolhead diagnostic
  - P100 commissioning
tags:
  - p100
  - magnetic-homing
  - f-08
  - e-18
  - safety
related:
  - RPSW-20260822-003
  - HW-20260909-002
---

# Add motor-inert P100 handshake diagnostic

## Summary

Added a dedicated Pro Micro RP2350 diagnostic that exercises P100's real
GP28-to-GP27 two-phase readiness and magnetic-threshold protocol without
configuring or writing any actuator-related pin.

## Reason

F-08 and the isolated GP27/U3 E-18 path need live controller/probe evidence
before the replacement N20 actuator is selected and characterized. The
production firmware correctly rejects a magnetic arm while safe lift is
uncommissioned, so bypassing that gate would be unsafe and would blur test
evidence.

## Implementation

`p100_handshake_test.ino` initializes only GP27, GP28, the service UART, and
the TMAG5273. After it records a far-field baseline, the first active-low GP28
assertion produces a GP27 ACK after the existing 20 ms inactive interval; its
release clears the ACK; the second assertion maps GP27 to the debounced TMAG
threshold state. It has a bounded scan timeout and fails GP27 inactive.

## Verification

Static review confirms the diagnostic has no DRV8833 (`GP4`–`GP7`), M3/M5
(`GP29`), HX711 (`GP0`/`GP1`), or LIFT_HOME (`GP2`) pin configuration or write.
`python tools/validate_homing_macro.py` remains the structural/numerical check
for the unchanged production P100 macro. Hardware flashing, F-08, and E-18
remain pending.

## Risks and follow-up

This diagnostic can establish only the controller-facing protocol. It cannot
establish a safe lift, center raster, outer-index registration, force control,
or permission to unlock P100 Q3/Q4. Reflash the production integrated firmware
and complete its lift/actuator gates before those tests.

## Files

- `firmware/pen_pressure/p100_handshake_test/p100_handshake_test.ino`
- `firmware/pen_pressure/README.md`
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`
- `docs/testing/TEST_PLAN.md`
