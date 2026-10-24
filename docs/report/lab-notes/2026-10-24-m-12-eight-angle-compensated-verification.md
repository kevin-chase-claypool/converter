# Lab Note: 2026-10-24 - Eight-angle compensated verification

## Objective

Determine whether candidate bed profile `eda33445701f` reduced the
position- and angle-dependent paper error when printed as an independent
compensated sheet.

## Configuration

- Hardware revisions: current installed XY + rotating-bed machine.
- Wiring/pin map: unchanged.
- Firmware commit/build: the toolhead/controller builds active during the print
  were not captured.
- grblHAL settings: `G65 P113` registration preceded the sheet; no settings
  changed during the sequence.
- Converter settings/sample:
  `samples\gcode\bed-error-verify-2026-10-24-eight-angle.gcode`, generated from
  candidate `eda33445701f`, with angular interpolation in the rotating bed
  frame.
- Instruments: portrait-angle phone photo
  `samples\gcode\bed-error-verify-2026-10-24-eight-angle-photo.jpg`, threshold
  `20`, blur radius `18`, working centre fraction `0.49,0.47`, and working
  radius fraction `0.5`.

## Code, commands, and configuration used

```powershell
py tools\measure_bed_error_photo.py `
  samples\gcode\bed-error-verify-2026-10-24-eight-angle-photo.jpg `
  --measurement-out samples\gcode\bed-error-verify-2026-10-24-eight-angle-measured.csv `
  --diagnostic-out samples\gcode\bed-error-verify-2026-10-24-eight-angle-photo.json `
  --overlay-out samples\gcode\bed-error-verify-2026-10-24-eight-angle-overlay.jpg `
  --threshold 20 --blur-radius 18 `
  --mask-center-fraction 0.49,0.47 --mask-radius-fraction 0.5

py tools\analyze_bed_error_calibration.py `
  --measurements samples\gcode\bed-error-verify-2026-10-24-eight-angle-measured.csv `
  --compare-to samples\gcode\bed-error-map-2026-10-24-measured.csv `
  --report-out samples\gcode\bed-error-verify-2026-10-24-eight-angle-analysis.json
```

## Procedure

1. Run `G65 P113` and leave the registered G54 frame unchanged.
2. Plot the compensated nine-pass verification sheet with one 0.20 mm pen,
   waiting at all eight `M0` pauses.
3. Photograph the complete sheet from above.
4. Extract all four fiducials and 333 station marks.
5. Compare the independently normalized verification errors with the original
   uncompensated calibration sheet.
6. Repeat extraction at lower and higher image thresholds to rule out a
   measurement-only failure.

## Results

- Photo extraction found four fiducials, 334 station-L candidates, and 74 label
  glyphs. All 333 required stations assigned with `0.865 / 5.961 / 11.891 px`
  minimum / median / maximum assignment error.
- Overall station RMS changed from `0.708 mm` before compensation to `0.639 mm`
  after compensation, a `9.8 %` improvement. Maximum error increased from
  `1.453 mm` to `1.574 mm`.
- The verification failed every required aggregate gate:
  `0.35 mm` RMS, `0.90 mm` maximum, and `30 %` minimum improvement.
- RMS / maximum by pass before -> after:

| Pass | Before (mm) | After (mm) | Result |
|---|---:|---:|---|
| A0 reference | `0.306 / 0.540` | `0.343 / 0.715` | worse |
| A45 | `0.633 / 0.967` | `0.409 / 0.846` | improved |
| A90 | `1.081 / 1.453` | `0.670 / 1.301` | improved |
| A135 | `0.903 / 1.217` | `0.814 / 1.150` | improved |
| A180 | `0.727 / 1.070` | `0.622 / 1.015` | improved |
| A225 | `0.609 / 1.103` | `0.546 / 0.900` | improved |
| A270 | `0.540 / 0.884` | `0.684 / 1.161` | worse |
| A315 | `0.607 / 1.023` | `0.963 / 1.574` | worse |
| A0 control | `0.690 / 1.083` | `0.416 / 0.770` | improved |

- Threshold/blur sensitivity runs at `10/10`, `15/15`, and `20/18` all failed:
  after RMS was `0.65 / 0.64 / 0.64 mm`, maximum was
  `1.62 / 1.58 / 1.57 mm`, and improvement was `7.8 / 9.6 / 9.8 %`.
- The generated verification program identifies profile `eda33445701f` and
  `angular interpolation bed-frame` in its header. Its strict motion check
  passes, with no bare rotating `G0` travel.

## Difficulties and corrective actions

- The verification photo contains large dark paper-edge components in addition
  to the four printed V fiducials. The photo tool now filters fiducials by both
  component size and bounding-box dimension instead of accepting every
  component wider than 40 px.
- The working circle is offset from the image centre, so the default mask
  missed much of the right and lower sheet. The documented command uses the
  measured working centre and radius.
- A compensated verification sheet must be analyzed with `--compare-to`. Fitting
  it as though it were an uncompensated calibration would treat the correction
  deliberately applied by the previous profile as new machine error.

## Interpretation

Compensation is active and materially improves A45-A225, A90, and the final A0
control. It is not a usable map for the full bed because A0 reference, A270,
and A315 now have more error, and the new worst station is A315.

The failure is consistent with the calibration's own marginal validation:
its `1.032 mm` leave-one-station-out maximum already exceeded the `0.90 mm`
gate. The independent sheet therefore confirms that the eight-angle map is not
repeatable enough to promote.

## Decisions and next action

- Reject candidate `eda33445701f` as the default.
- Keep the verified four-angle profile `4c8270de8a74` as the default.
- Do not promote a profile fitted from this compensated verification sheet.
- Before another full-map fit, isolate the changed A0/A270/A315 behavior with a
  smaller repeated-axis test. At minimum, repeat those passes with the same
  profile and a fixed-position A0 control to separate profile error from
  run-to-run rotary/carriage repeatability.
