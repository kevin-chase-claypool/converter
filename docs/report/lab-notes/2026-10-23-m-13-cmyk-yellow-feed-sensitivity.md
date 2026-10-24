# Lab Note: 2026-10-23 - CMYK wave-screen feed sensitivity

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

### 2026-10-24 magenta follow-up

- The same Ben1 set's magenta layer was run at a 60 % controller feed override,
  or `420 mm/min`. The operator reports that striations remained very visible,
  especially on the subject's right side of the face.
- `IMG_0514-cmyk-magenta.gcode` normally demands a maximum A rate of
  `254 motor deg/s`; at 60 % this falls to about `152 motor deg/s`. The file
  has 996 A-direction reversals, fewer than the yellow layer's 2,777.
- Magenta uses 893 planned contours and 26,850 drawing moves, versus yellow's
  627 contours and 34,509 drawing moves. The remaining magenta defect is
  therefore not explained by a larger file-wide reversal count or a higher
  command-rate demand alone.

## Difficulties and corrective actions

- The exact feed-override transition point and resulting photo were not
  captured. A repeat should use separate files or an instrumented override
  transition so the 700 and 455 regions are directly comparable.
- Changing the converter's Feed rate alone would not necessarily reproduce this
  test because the bed tangential-speed setting is independent. To generate an
  equivalent whole-program rate reduction, scale both Feed rate and Theta
  tangential speed to 455 mm/min, or use a uniform controller feed override.
- The magenta follow-up had no accompanying photograph, so the stripe
  orientation, pitch, and exact location could not be measured.

## Interpretation

The compensation coordinates remain unchanged when feed rate changes. The clean
yellow print at 65 % therefore indicates rate-dependent motion error, not a
static bed-compensation or G-code-coordinate error. The leading boundary for
yellow is the rotating-bed/A drivetrain and its response under load.

Magenta remains defective at an even lower speed and has fewer A reversals, so
the yellow result cannot yet be generalized. Magenta-specific ink flow,
overlap of its 75-degree wave screen, pen seating/contact, paper deformation
after earlier passes, or a different X/Y motion allocation remain candidates.
The accepted compensation profile's `0.338 mm` RMS / `0.752 mm` maximum static
residual is common to all channels and does not by itself explain a
magenta-only difference.

## Decisions and next action

- Keep 700 mm/min as the nominal requested feed for now and use a 65 % override
  for quality-critical Xθ/Yθ yellow work until the drivetrain is improved.
- Repeat magenta alone in **Bed motion = XY only** at the same 420 mm/min. If it
  is clean, the remaining defect is rotary/A motion; if it persists, move to
  pen/ink/screen isolation.
- Photograph the completed magenta sheet from directly above, ideally with the
  four registration crosses enabled or with fixed sheet fiducials, so the
  striation pitch and direction can be measured.
- After installing the planned replacement bed/A motor, first repeat this same
  yellow and magenta layers at 700 mm/min. If clean, the 65 % workaround can be
  retired. If striation returns, run a controlled speed ladder at
  45 / 60 / 70 / 80 / 100 % and retain the highest fully clean setting per ink.
- The repeat must also confirm A direction, current, temperature, bed-ratio
  repeatability, and first-try M3 contact after the motor change.
