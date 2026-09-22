# Lab Note: 2026-09-22 - T-01G lift-home switch transition check

## Objective

Verify that the installed GP2 `LIFT_HOME` switch changes state when the
actuator flag presses and releases it.

## Configuration

- Hardware revisions: Pro Micro RP2350 toolhead with installed normally-open
  GP2 switch.
- Wiring/pin map: dry contact between GP2 and local `TOOL_GND`; firmware uses
  `INPUT_PULLUP` (active-low when pressed).
- Firmware commit/build: `t01g_lift_home_uart` diagnostic, Arduino IDE,
  115200 baud.
- Instruments: Arduino IDE Serial Monitor.

## Code, commands, and configuration used

```text
Firmware: firmware/pen_pressure/t01g_lift_home_uart/t01g_lift_home_uart.ino
Serial: 115200 baud
Observed telemetry: T01G lift_home=0 / T01G lift_home=1
```

## Procedure

1. Flash the motor-safe T-01G diagnostic with the external actuator rail
   disconnected.
2. Open the serial monitor at 115200 baud.
3. Move the switch actuator flag through the switch window while observing the
   repeated `T01G lift_home` records.

## Results

The output changed from `lift_home=0` to `lift_home=1` and returned to `0`:

```text
12:22:07.869 -> T01G lift_home=1
12:22:08.389 -> T01G lift_home=1
12:22:08.863 -> T01G lift_home=1
12:22:09.360 -> T01G lift_home=1
12:22:09.856 -> T01G lift_home=0
12:22:10.356 -> T01G lift_home=0
12:22:10.850 -> T01G lift_home=0
12:22:11.362 -> T01G lift_home=0
```

The transition is electrically repeatable over several serial samples. This
run did not establish the ten slow powered retract cycles, trigger/release
positions, backstop margin, or missing-trigger timeout behavior required by
T-01G.

## Difficulties and corrective actions

None encountered during this transition check.

## Interpretation

GP2 polarity and the switch wiring are functioning as designed: `0` is the
pressed/home state and `1` is released. This supports continuing T-01G, but it
does not yet authorize `LIFT_REFERENCE_VALID` or motor-controlled homing.

## Decisions and next action

Keep `LIFT_REFERENCE_VALID = false`. Run ten slow, guarded powered retract
cycles with the actuator unloaded; record the pulse count and physical
trigger/release position relative to the mechanical backstop. Stop if the
switch is reached at the backstop or fails to change state.
