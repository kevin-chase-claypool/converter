---
id: RPSW-20260908-001
date: 2026-09-08
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - t01g_lift_home_uart
  - GP2 LIFT_HOME
  - GP20/GP21 service UART
tags:
  - toolhead
  - lift-home
  - uart
  - diagnostics
  - t-01g
related:
  - HW-20260908-004
---

# Add LIFT_HOME UART diagnostic sketch

## Summary

Added a minimal, motor-safe sketch to isolate the installed GP2 LIFT_HOME
switch and GP20/GP21 service-UART path from the integrated dual-core firmware.

## Reason

The integrated sketch produced unreadable/absent service output during the
first installed UART check. A minimal deterministic signal is needed before
attributing the problem to the switch, UART wiring, adapter configuration, or
the integrated firmware.

## Implementation

`t01g_lift_home_uart` configures GP2 with `INPUT_PULLUP`, maps Arduino-Pico
`Serial2` (hardware UART1) TX/RX to GP20/GP21, and writes `T01G lift_home=0`
or `T01G lift_home=1` every 500 ms at 115200 baud. It initializes no DRV8833,
motor, HX711, TMAG5273, PC817C, or machine-control pin.

## Verification

`arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\\pen_pressure\\t01g_lift_home_uart`
passed. Installed UART output remains pending.

## Struggles and rejected approaches

Using the integrated sketch as the first UART proof was rejected because its
dual-core safety, watchdog, sensor, and motor-driver initialization complicate
an otherwise simple physical communications check. The initial diagnostic also
incorrectly used `Serial1` (UART0), which cannot route to GP20/GP21; it was
corrected to `Serial2` (UART1).

## Risks and follow-up

Upload through USB-C/UF2 with motor power disabled. The UART monitor must show
the fixed line cleanly at 115200 baud and toggle with the switch before
returning to the integrated firmware or allowing T-01G powered motion.

## Files

- `firmware/pen_pressure/t01g_lift_home_uart/t01g_lift_home_uart.ino`: isolated UART diagnostic.
- `firmware/pen_pressure/README.md`: bench-sketch index.
- `docs/testing/TEST_PLAN.md`: T-01G diagnostic procedure.
