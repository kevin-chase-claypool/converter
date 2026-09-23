# Lab Note: 2026-09-22 - E-09C CS1238 known-mass calibration

## Objective

Characterize the installed 300 g toolhead load cell and CS1238 using available
precision masses before any N20/DRV8833 force-control test.

## Configuration

- Controller: SparkFun Pro Micro RP2350 with
  `e07d_cs1238_known_mass_calibration.ino` flashed through Arduino IDE.
- ADC: CS1238 channel A, gain 128, configured/reported at 640 SPS.
- Host: one native USB COM connection to the E-07D Windows application.
- Fixture: masses placed downward on the motor mount. The application retained
  an explicitly approximate **Opposite: upward pen-tip reaction** projection.
- Actuator: 6 V rail disconnected; no N20/DRV8833 command was issued.

## Procedure

One 1,000 ms raw capture was taken at every available cumulative mass while
loading and then unloading. Initially entered loading points were `0, 5, 10,
15, 20, 30, 40, 50, 70, 90 g`; unloading points were `70, 50, 40, 30, 20, 15,
10, 5, 0 g`. A later review found that a 2.5 g pen cap was physically present
for every capture. The physical labels therefore require a recorded **+2.5 g**
fixture correction (`2.5, 7.5, …, 92.5 g`), not subtraction. Raw files are
unchanged.
Each capture retained approximately 650 raw samples; the application used only
the final-half mean as a representative fit point while retaining every raw
sample CSV.

## Results

The saved run is retained in the repository at:

```text
firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/
results/run_2026-09-22_08-29-03/
```

The first saved fit, before the fixture-label correction, was:

```text
downward_weight_g = 0.000200466998 * raw - 52.8549927
```

- Raw sensitivity: `4,988.35 raw/g`; a constant-label correction does not
  change this slope, residuals, or R².
- Fit quality: `R² = 0.999231`; RMS residual `0.705 g`.
- The loading/unloading graph is near-linear. The observed zero-load final-half
  means were `262,289 raw` loading and `264,849 raw` unloading; this is about
  0.51 g equivalent shift, appropriate only for the initial non-precision
  profile.
- After the +2.5 g correction, the recorded no-load extrapolation is
  `251,188 raw` (the first summary reported `263,659 raw`). Using the selected
  opposite-direction assumption, source stages raw-force
  deltas of 174,592 (35 g contact), 249,418 (50 g target), and 349,185 (70 g
  hard limit). The sign is `-1` because upward pen force is expected to make
  raw counts fall.

## Interpretation

This is adequate evidence to replace the integrated source's zero placeholders
with a candidate profile. It does not prove that the downward motor-mount
fixture is mechanically identical to upward paper reaction at the installed
pen tip. It also does not establish N20 direction, actuator response, normal
M5 release, actual air gap, or closed-loop stability.

## Next action

With an installed pen, use the application's Pen-scale check at approximately
50 g to make a guarded raw-direction observation and confirm
that increasing paper reaction makes raw CS1238 counts decrease. Then complete
the actuator-direction/response and M5-clearance tests before any commissioning
gate is enabled.
