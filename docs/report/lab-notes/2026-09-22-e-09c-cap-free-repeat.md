# Lab Note: 2026-09-22 - E-09C cap-free CS1238 repeat

## Objective

Repeat the installed 300 g toolhead-load-cell known-mass calibration without
the accidental 2.5 g pen cap, so the staged raw zero and force profile refer to
the intended cap-free setup.

## Configuration

- Controller: SparkFun Pro Micro RP2350 with
  `e07d_cs1238_known_mass_calibration.ino` through Arduino IDE.
- ADC: CS1238 channel A, gain 128, configured/reported at 640 SPS.
- Host: one native-USB Pro Micro COM port using the E-07D Windows application.
- Fixture: cap removed; precision masses applied downward to the motor mount.
- Actuator: 6 V rail disconnected; no N20/DRV8833 command was issued.

## Procedure

At 1,000 ms per capture, one loading sequence and one unloading sequence were
recorded. Loading used `0, 5, 10, 15, 20, 30, 40, 50, 70, 90 g`; unloading
used `90, 70, 50, 40, 30, 20, 15, 10, 5, 0 g`. Each record retained roughly
650 raw samples and fit only its final-half mean while preserving every raw
CSV trace.

## Results

The accepted cap-free run is local at:

```text
firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/
results/run_2026-09-22_09-10-46/
```

```text
downward_weight_g = 0.000198461271 * raw - 49.3170074
```

- Sensitivity: `5,038.77 raw/g`.
- Fit quality: `R² = 0.9999778`; RMS residual `0.132 g`.
- The no-load extrapolation is `248,497 raw`.
- The selected opposite upward pen-reaction projection stages deltas of
  176,357 raw at 35 g contact, 251,938 raw at 50 g target, 352,714 raw at
  70 g hard limit, 25,194 raw for ±5 g target readiness, and 15,116 raw for
  the 3 g clear band.

This repeat supersedes the cap-included `08-29-03` run for staged profile
values. It does not remove the earlier raw evidence or assert that the
downward motor-mount fixture is mechanically identical to upward pen-tip
reaction.

## Next action

With the installed pen and the actuator rail still disconnected, use the
Windows application's **Pen-scale check** to capture a steady approximately
50 g kitchen-scale reaction. Confirm that raw counts move in the selected
opposite direction before guarded actuator direction/response and M5-clearance
tests. All force-control gates remain false.
