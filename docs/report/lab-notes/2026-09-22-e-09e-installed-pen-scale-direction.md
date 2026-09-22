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

PULSE_READING,time_us=409351417,raw=5999,tare_delta=-247637,tare_valid=1
kitchen_scale_g=62.5

PULSE_DONE,direction=UP,ms=10,fault_during_drive=0,down_pulses_remaining=24
kitchen_scale_g_before_up_pulse=35.5

PULSE_READING,time_us=438954829,raw=187766,tare_delta=-65870,tare_valid=1
kitchen_scale_g_after_up_pulse=2.2
```

The implied clear-state tare is `253,636 raw` (`-59,087 - -312,723`).

## Outcome

The raw response is negative relative to tare while the scale measures a positive upward pen reaction. This confirms the **opposite** force direction selected for the E-09C downward-mass projection. One installed-pen point cannot establish linearity, hysteresis, repeatability, or the safe pulse/control envelope, so it does not replace the accepted known-mass slope or alter the production profile.

The observed magnitudes are not monotonic enough to construct an installed-pen transfer fit: the 40.7 g datum has a `-312,723 raw` delta while the later 62.5 g datum has a smaller `-247,637 raw` delta. This is evidence of a changing mechanism/settling state, not a valid linear calibration. The 10 ms up pulse then reduced the displayed scale reading from 35.5 g to 2.2 g without a fault, showing that 10 ms is too coarse near the 40–60 g target. E-09E therefore changes to 5–100 ms pulses in 5 ms steps. The original 40.7 g magnitude (`312,723 raw / 40.7 g = 7,684 raw/g`) remains materially different from the downward motor-mount calibration's `5,038.77 raw/g`.

## Difficulties and next action

The optional Windows application did not complete its adapter-COM connection, so Arduino IDE Serial Monitor provided explicit one-pulse commands and readable raw results. Repeat a controlled 5 ms-pulse sequence after a fresh tare, retaining pulse duration/count and the complete `READING` line. Do not enable `PRESSURE_CALIBRATION_VALID`, actuator control, M3/M5 force control, or GP27 normal status from this observation.

## References

- [E-09C test plan](../../testing/TEST_PLAN.md)
- [E-09C cap-free known-mass result](2026-09-22-e-09c-cap-free-repeat.md)
- [E-09E serial monitor change](../../changes/rp23cnc-software/2026/2026-09-22-add-e09e-serial-monitor-shortcuts.md)
