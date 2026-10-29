# Lab Note: 2026-10-29 - M-12/T-01H dense v3 pen-up drag

## Objective

Determine whether the photographed 91-station v3 calibration sheet with
five-second automatic pass dwells can produce a valid bed compensation profile,
and identify the source of faint marks between station clusters.

## Configuration

- Program: `samples\gcode\bed-error-map-dense-91-v3-auto.gcode`, SHA-256
  `421CAAC9AF15B67B2FB9B313B2D11521EFF738124CA8BB9716D43199DA97C13E`.
- Layout: `dense-91-v3`, 91 stations, nine passes, eight automatic `G4 P5`
  pass dwells, and no manual `M0` stops.
- Pen: one Sakura Pigma Micron 005 for all passes, as reported by the operator.
- Registration: the sheet was returned to A=0 between passes. The exact
  `G65 P113` output and deployed toolhead build were not captured.
- Photo: `samples\gcode\bed-error-map-dense-91-v3-auto-photo.jpg`,
  1684 x 2236 px, SHA-256
  `E2D30D5E010ACA4E7379194CE803EA5AC8F74CEF203ADD5004743E078DA0900A`.

## Code, commands, and configuration used

The compact photo needed the `WSW-20261029-004` fiducial-size change before it
could be evaluated. The primary extraction was:

```powershell
python tools\measure_bed_error_photo.py `
  samples\gcode\bed-error-map-dense-91-v3-auto-photo.jpg `
  --layout dense-91-v3 --threshold 55 --fiducial-threshold 25 `
  --blur-radius 6 `
  --seed-diagnostic samples\gcode\bed-error-map-dense-91-v3-auto-photo.json `
  --measurement-out samples\gcode\bed-error-map-dense-91-v3-auto-measured-t55.csv `
  --diagnostic-out samples\gcode\bed-error-map-dense-91-v3-auto-photo.json `
  --overlay-out samples\gcode\bed-error-map-dense-91-v3-auto-station-overlay-t55.jpg
```

The same extraction was repeated at station thresholds 70 and 80. Analysis of
the threshold-55 CSV reached profile construction, then stopped at:

```text
ValueError: correction exceeds the 5.0 mm safety bound
```

Pen-up drag was checked by projecting each same-angle `(travel)` segment from
the printed G-code into the photographed sheet coordinate frame. For each
12-50 mm segment, the image residual was:

```text
residual = GaussianBlur(gray, 5) - gray
```

The median maximum residual within `+/-3 px` of the commanded path was compared
with parallel controls at `8-13 px` on either side. Sampling covered `t=0.2`
through `t=0.8`. The reviewed result is preserved in
`samples\gcode\bed-error-map-dense-91-v3-auto-travel-overlay.jpg`.

## Procedure

1. Plot all nine dense passes in the automatic five-second mode.
2. Photograph the complete secured sheet from above.
3. Resolve the four fiducials and review the measured-station overlay.
4. Repeat extraction at thresholds 55, 70, and 80.
5. Project every same-angle pen-up travel segment back onto the photo.
6. Compare image contrast along the commanded travel path with parallel blank
   controls.
7. Inspect the generated G-code around every flagged travel line to confirm
   whether `M5` and its `P115` acknowledgement preceded the move.

## Results

- Four fiducials were resolved after the compact-image filter fix.
- At threshold 55, the dense matcher found 530 station-L candidates for 819
  expected marks. Counts fell to 356 at threshold 70 and 195 at threshold 80.
- Station coordinates moved by `2.469 mm` RMS / `11.083 mm` maximum between
  thresholds 55 and 70, and `3.169 mm` RMS / `11.108 mm` maximum between 55
  and 80. The field is not repeatable enough for a profile.
- Five long G-code pen-up travel commands, representing four visible path
  locations, had strong ink response on the commanded line: median center
  contrast `23-95` versus `2-5` on parallel blank controls.
- Every inspected flagged travel is preceded by the expected sequence:

  ```text
  M5
  G65 P115 Q1 A1 W2
  G1 X... Y... A... F3000 (travel)
  ```

  The converter did not omit the pen-clear command.
- The station overlay is otherwise recognizable across the field, but the
  drag-connected components and low-resolution ambiguity make the extracted
  coordinates unsuitable for compensation fitting.

## Difficulties and corrective actions

- The original fiducial-size floor assumed a 3072 x 4080 photo and rejected
  this smaller capture. The filter now accepts the measured 27 x 37 px F1
  component without admitting station marks.
- Lowering the station threshold recovers more components but also admits
  merged drag/label fragments. The resulting 2.5-3.2 mm threshold movement
  confirms that component assignment is not trustworthy on this sheet.
- The obvious faint traces are not planner paths: they lie exactly on
  commanded pen-up travel lines after a successful `M5`/`P115` sequence.

## Interpretation

This sheet is invalid for bed-compensation fitting. The first blocker is
physical pen clearance during some pen-up travels; improving the image filter
cannot recover a clean geometric field from merged and missing components.

The evidence favors an intermittent lift/clearance problem over a missing
`M5`, missing `P115`, calibration-layout error, or planner displacement.
Intermittent mechanical release and a toolhead binary that predates the 130 ms
clearance setting remain the leading explanations. Pen mounting and
high-speed dynamic sag have not been separated.

## Decisions and next action

- Reject this physical sheet and do not fit or promote a profile from its
  measurements.
- Confirm which toolhead firmware binary is actually running, including whether
  `PEN_CLEAR_EXTRA_LIFT_MS=130` is deployed.
- Run the T-01H no-drag check for at least 30 `M3`/`M5` cycles with
  representative X/Y travel. Record the `p` status after failed-looking `M5`
  events and test low versus high travel speed separately.
- Inspect clamp height and the end of the pen nib if the current 130 ms build
  still leaves trails. Do not increase the pulse blindly beyond 130 ms.

This extends T-01H and M-12; it does not authorize a new compensation profile.
