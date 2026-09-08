# Lab Note: 2026-09-08 - T-01G LIFT_HOME switch installation

## Objective

Install and safely expose the toolhead's fully-retracted-carriage reference
switch before any automatic retract behavior is enabled.

## Evidence

With power removed, the selected normally-open microswitch contact read open
(no continuity beep) when released and closed (continuity beep) when pressed.
The owner then installed the dry contact between the Pro Micro RP2350 `GP2`
pin and its adjacent local `TOOL_GND` pin.

## Firmware boundary

The integrated toolhead firmware configures GP2 as `INPUT_PULLUP` and reports
the active-low switch state as `lift_home` in both native-USB and GP20/GP21
service-UART telemetry. It does not yet use this input to start, stop, or
otherwise control the DRV8833/motor. This keeps the initial post-installation
check motor-safe.

## Remaining T-01G verification

With motor power disabled, flash the firmware and confirm native-USB or service
UART telemetry reads `lift_home=0` released and `lift_home=1` pressed. Then,
only after that input test passes, run ten guarded slow retract cycles and
document repeatability, release position, debounce behavior, and timeout/fault
behavior. The switch is a position reference, not a mechanical hard stop and
not a spring-force sensor.
