---
id: RPSW-20260909-001
date: 2026-09-09
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - e07b_hx711_actuator_steps
  - GP2
  - GP20/GP21 service UART
tags:
  - toolhead
  - t-01g
  - lift-home
  - uart
  - commissioning
related:
  - HW-20260908-004
---

# Add lift-home status to bounded actuator test

## Summary

The 6 V-compatible bounded actuator sketch now reports the active-low GP2
`LIFT_HOME` switch state through the installed GP20/GP21 service UART.

## Reason

`bench_motor_command` uses native USB `Serial`, which is unavailable at COM8
while the normal 6 V rail powers the toolhead. T-01G requires observing GP2
while making guarded retract motions, and E-07B already provides single,
self-sleeping pulses on the COM8 path.

## Implementation

`e07b_hx711_actuator_steps` configures GP2 with `INPUT_PULLUP`, writes
`lift_home=0` or `lift_home=1` at startup and after every manual actuator
pulse, and accepts `h` for an on-demand switch-state report. It does not add
automatic retract stopping or continuous motor operation: each `u`/`d` command
still ends by sleeping the DRV8833.

## Verification

Source compilation and hardware T-01G switch/retract-cycle evidence remain
required. The prior GP2-to-COM8 input-only diagnostic passed; this change has
not yet been flashed or bench-verified.

## Struggles and rejected approaches

Converting every sketch to `Serial2` would be incorrect: USB-powered,
motor-inactive sketches intentionally use native USB. The defect was limited
to the motor-capable `bench_motor_command` path; E-07B is the appropriate
normal-6-V service test because it already uses `Serial2` and bounded pulses.

## Risks and follow-up

`lift_home=1` is telemetry only. The operator must stop before the mechanical
backstop and use fine manual pulses near the switch. Complete ten guarded
retract/release cycles before enabling GP2-controlled motor behavior.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: GP2 input and bounded-pulse status reports.
- `firmware/pen_pressure/README.md`: staged-sketch service-UART contract.
