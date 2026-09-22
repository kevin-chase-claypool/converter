# Lab Note: 2026-09-22 - E-09E installed-pen kitchen-scale direction check

## Objective

Confirm the sign of the CS1238 response under the actual upward pen-tip reaction before assigning any production force-control direction or threshold. This is the first data point in the installed-pen force-path check, not a new transfer calibration.

## Configuration and procedure

- Test: E-09E installed-pen kitchen-scale pulse check, with the installed 300 g load cell, CS1238 channel A/gain 128/640 SPS, and kitchen scale under the installed pen.
- Controller: SparkFun Pro Micro RP2350 running `e09e_cs1238_pen_scale_pulse.ino` through GP20/GP21 3.3 V service UART, using Arduino IDE Serial Monitor at 115200 baud.
- Calibration relationship: accepted E-09C applies downward mass to the motor mount; this test measures the opposite, upward pen-tip reaction.
- The operator manually issued bounded single N20 pulses and allowed the scale to settle before reading CS1238. Exact pulse count and selected duration were not recorded in this first observation.

## Measurement

```text
PULSE_READING,time_us=145916961,raw=-59087,tare_delta=-312723,tare_valid=1
kitchen_scale_g=40.7
```

The implied clear-state tare is `253,636 raw` (`-59,087 - -312,723`).

## Outcome

The raw response is negative relative to tare while the scale measures a positive upward pen reaction. This confirms the **opposite** force direction selected for the E-09C downward-mass projection. One installed-pen point cannot establish linearity, hysteresis, repeatability, or the safe pulse/control envelope, so it does not replace the accepted known-mass slope or alter the production profile.

The observed magnitude is `312,723 raw / 40.7 g = 7,684 raw/g`, materially different from the downward motor-mount calibration's `5,038.77 raw/g`. That may indicate the force paths are mechanically different, but it requires repeats before interpretation.

## Difficulties and next action

The optional Windows application did not complete its adapter-COM connection, so Arduino IDE Serial Monitor provided explicit one-pulse commands and readable raw results. Repeat at stable 20, 40, 50, and 60 g scale values with the same pen, retaining pulse duration/count and the complete `READING` line. Do not enable `PRESSURE_CALIBRATION_VALID`, actuator control, M3/M5 force control, or GP27 normal status from this observation.

## References

- [E-09C test plan](../../testing/TEST_PLAN.md)
- [E-09C cap-free known-mass result](2026-09-22-e-09c-cap-free-repeat.md)
- [E-09E serial monitor change](../../changes/rp23cnc-software/2026/2026-09-22-add-e09e-serial-monitor-shortcuts.md)
