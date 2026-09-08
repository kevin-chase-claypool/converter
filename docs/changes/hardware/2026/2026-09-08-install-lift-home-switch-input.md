---
id: HW-20260908-004
date: 2026-09-08
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - LIFT_HOME microswitch
  - SparkFun Pro Micro RP2350 GP2
  - toolhead firmware telemetry
tags:
  - toolhead
  - lift-home
  - t-01g
  - safety
related:
  - HW-20260908-003
---

# Install LIFT_HOME switch input diagnostics

## Summary

Installed the normally-open LIFT_HOME microswitch between local `GP2` and
`TOOL_GND`, and added active-low, input-only firmware telemetry.

## Reason

The retract reference must be electrically verified before it can safely stop
or reference any motor motion.

## Implementation

`PIN_LIFT_HOME` is GP2 and uses `INPUT_PULLUP`; `PressureController` exposes
the active-low state in the native-USB and GP20/GP21 **UART1** `lift_home`
telemetry field. The input does not alter motor state, motor enable, or driver
output in this milestone.

## Verification

Power-off meter test: the selected contact was open released and continuous
pressed. Owner reported the COM/NO pair installed on GP2 and adjacent local
TOOL_GND. Firmware compilation and live telemetry transition remain pending.

## Struggles and rejected approaches

Enabling switch-driven motor stopping before observing the installed input was
rejected. A wiring/polarity error must first be visible without energizing the
motor.

## Risks and follow-up

Flash with motor power disabled and confirm `lift_home=0` released and `1`
pressed. Then complete all ten guarded T-01G retract cycles before permitting
the input to control retract. The switch remains a position reference, not a
hard stop or force sensor.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/`: GP2 input and telemetry.
- `docs/hardware/WIRING_TABLE.md`: installed switch connection.
- `docs/testing/TEST_PLAN.md`: T-01G partial result and remaining gate.
- `docs/report/lab-notes/2026-09-08-t-01g-lift-home-switch-installation.md`: bench record.
