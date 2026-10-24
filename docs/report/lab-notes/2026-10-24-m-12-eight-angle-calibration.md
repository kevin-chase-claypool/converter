# Lab Note: 2026-10-24 - Eight-angle full-field bed calibration

## Objective

Measure the expanded one-sheet full-field calibration at eight bed angles and
determine whether the resulting profile is acceptable as the new default.

## Configuration

- Hardware revisions: current installed XY + rotating-bed machine.
- Wiring/pin map: unchanged.
- Firmware commit/build: the toolhead/controller builds active during the print
  were not captured.
- grblHAL settings: `G65 P113` registration preceded the sheet; no settings
  changed during the sequence.
- Converter settings/sample: `samples\gcode\bed-error-map.gcode`, calibration v3,
  37 stations, angles `0/45/90/135/180/225/270/315`, feed `420 mm/min`, one
  0.20 mm pen, and eight drying pauses.
- Instruments: portrait-angle phone photo
  `samples\gcode\bed-error-map-2026-10-24-photo.jpg`.

## Code, commands, and configuration used

```powershell
py tools\measure_bed_error_photo.py `
  samples\gcode\bed-error-map-2026-10-24-photo.jpg `
  --measurement-out samples\gcode\bed-error-map-2026-10-24-measured.csv `
  --diagnostic-out samples\gcode\bed-error-map-2026-10-24-photo.json `
  --overlay-out samples\gcode\bed-error-map-2026-10-24-overlay.jpg

py tools\analyze_bed_error_calibration.py `
  --measurements samples\gcode\bed-error-map-2026-10-24-measured.csv `
  --bed-mesh samples\gcode\bed-mesh-2026-10-11.csv `
  --coverage-radius-mm 171.45 `
  --allow-high-residual `
  --profile-out samples\gcode\bed-error-compensation-2026-10-24-eight-angle-candidate.json `
  --report-out samples\gcode\bed-error-analysis-2026-10-24-eight-angle.json
```

## Procedure

1. Run `G65 P113`.
2. Plot the nine-pass calibration on one secured sheet, waiting at all eight
   `M0` pauses.
3. Photograph the complete sheet from above.
4. Extract all four fiducials and 333 station marks with the photo tool.
5. Fit the eight-angle profile with a declared `171.45 mm` coverage radius.
6. Review leave-one-station-out, A0 control, per-angle, and bed-mesh reports.

## Results

- Photo extraction found four fiducials, 336 L-shaped candidates, and 109 small
  label-like components. All 333 required stations were assigned with
  `4.262 / 7.565 / 12.365 px` minimum / median / maximum assignment error.
- A0 spatial error: `0.306 mm` RMS / `0.540 mm` maximum.
- A0 control residual after the complete rotation sweep: `0.684 mm` RMS /
  `0.901 mm` maximum.
- Leave-one-station-out prediction: `0.297 mm` RMS / `1.032 mm` maximum, a
  `58.0 %` improvement over raw error.
- Per-angle RMS / maximum:
  - A45: `0.646 / 1.016 mm`
  - A90: `1.043 / 1.375 mm`
  - A135: `0.839 / 1.189 mm`
  - A180: `0.638 / 0.838 mm`
  - A225: `0.520 / 0.889 mm`
  - A270: `0.523 / 1.050 mm`
  - A315: `0.625 / 1.034 mm`
- The profiler rejected the map because maximum leave-one-out error exceeded
  the `0.90 mm` gate. A candidate profile was written only after explicitly
  allowing a high residual: fingerprint `eda33445701f`, coverage `171.45 mm`,
  maximum correction `1.391 mm`.

## Difficulties and corrective actions

- The initial matcher required exactly 185 components and the previous image
  orientation. It rejected the new sheet at 336 candidates and then assigned
  the wrong L-corner ends.
- The photo tool now selects the best non-mirrored fiducial rotation, tolerates
  a small number of extra components, and measures V/L corners in sheet
  coordinates. The corrected overlay puts every green measurement point on the
  shared L corner.
- The A0 control and A90 stage remain poor even with correct extraction. The
  maximum leave-one-out error is a control-pass station at 95 mm radius,
  A=330 degrees; the other largest failures are also control/A90 stations.

## Interpretation

The eight-angle data are complete enough to fit, and the lower RMS plus
`58.0 %` cross-validation improvement indicate real predictive value. The map
does not meet the current acceptance envelope, however.

The concentration of failures in A90 and the post-rotation A0 control suggests
repeatable rotary-position or carriage/height coupling rather than a global
centre offset. The A0 reference field itself is similar in quality to the
previous four-angle calibration (`0.306 mm` versus approximately `0.292 mm`
RMS), so the new failure is dominated by angular/control behavior.

## Decisions and next action

- Do not change the default profile to `eda33445701f`.
- Keep it as an explicitly named candidate.
- Print the independent compensated verification sheet generated at
  `samples\gcode\bed-error-verify-2026-10-24-eight-angle.gcode`.
- Measure and compare it with the original sheet using
  `--compare-to samples\gcode\bed-error-map-2026-10-24-measured.csv`.
- The follow-up verification failed; see
  `2026-10-24-m-12-eight-angle-compensated-verification.md`. Repeat the
  A0/A270/A315 rotary behavior before accepting another full-field map.
