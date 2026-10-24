# Lab Note: 2026-10-23 - CMYK yellow wave-screen feed sensitivity

## Objective

Determine whether the striations remaining in the compensated CMYK yellow
wave-screen print are sensitive to drawing feed rate and therefore caused by
bed/A motion dynamics rather than incorrect compensation coordinates.

## Configuration

- Hardware revisions: current installed XY + rotating-bed machine; the operator
  reports that a replacement motor is arriving for the bed/A drive, intended to
  match the motor already installed on Y. The replacement was not installed for
  this observation.
- Wiring/pin map: unchanged.
- Firmware commit/build: the exact toolhead and controller builds active during
  the print were not captured. The converter G-code was generated before the
  130 ms M5-clearance source change in `98251f8`.
- grblHAL settings: the saved program assumes `$113=30000` motor deg/min and
  `$123=6000` motor deg/s2.
- Converter settings/sample: `samples/gcode/Ben1/IMG_0514-cmyk-yellow.gcode`;
  `feed 700 mm/min`, `travel 3000 mm/min`, `tolerance 0.050 mm`, centre hold
  `64 mm`, Xθ/Yθ bed motion, and bed-compensation profile
  `4c8270de8a74` / coverage `171.450 mm`.
- Instruments: direct visual inspection by the operator. No calibrated photo of
  the completed comparison region and no controller feed-override log were
  captured.

## Code, commands, and configuration used

```powershell
py tools\check_gcode_motion.py --strict samples\gcode\Ben1\IMG_0514-cmyk-yellow.gcode
```

The saved program reports:

```text
moves: 35136 drawing, 626 travel (14313 parked-bed moves)
largest bed rotation in one drawing move: 6.18 deg (cap 15.0)
largest A rate demanded: 254 motor deg/s (limit 500)
strategies: hold 14313, travel 627, x_theta 6636, y_theta 14187
bed re-registrations: 43
```

The operator reduced the controller feed override to **65 %** of the programmed
700 mm/min, or **455 mm/min**. The exact ioSender action and transition line
were not recorded.

## Procedure

1. Run the compensated yellow program at its programmed 700 mm/min draw feed.
2. Observe the recurring striations.
3. Continue the print with the controller feed override reduced to 65 %.
4. Compare the slowed region visually with the prior region.

## Results

- The operator reports that the striation appears to be eliminated in the
  455 mm/min region.
- Assuming a uniform feed override across X/Y/A, the file's largest A rate falls
  from about `254` to `165 motor deg/s`, still well below the `500 motor deg/s`
  limit.
- No fixed-feed repeat, calibrated image, or post-run measurement was captured,
  so this is partial bench evidence rather than a formal M-13 pass.

## Difficulties and corrective actions

- The exact feed-override transition point and resulting photo were not
  captured. A repeat should use separate files or an instrumented override
  transition so the 700 and 455 regions are directly comparable.
- Changing the converter's Feed rate alone would not necessarily reproduce this
  test because the bed tangential-speed setting is independent. To generate an
  equivalent whole-program rate reduction, scale both Feed rate and Theta
  tangential speed to 455 mm/min, or use a uniform controller feed override.

## Interpretation

The compensation coordinates remain unchanged when feed rate changes. A clean
print at 65 % therefore indicates rate-dependent motion error, not a static
bed-compensation or G-code-coordinate error. The leading boundary is the
rotating-bed/A drivetrain and its response under load; the accepted
compensation profile still has a measured `0.338 mm` RMS / `0.752 mm` maximum
static residual but does not explain a defect that disappears with speed alone.

## Decisions and next action

- Keep 700 mm/min as the nominal requested feed for now and use a 65 % override
  for quality-critical Xθ/Yθ CMYK work until the drivetrain is improved.
- After installing the planned replacement bed/A motor, first repeat this same
  yellow layer at 700 mm/min. If clean, the 65 % workaround can be retired. If
  striation returns, run a controlled speed ladder at 65 / 75 / 85 / 100 % and
  retain the highest fully clean setting.
- The repeat must also confirm A direction, current, temperature, bed-ratio
  repeatability, and first-try M3 contact after the motor change.
