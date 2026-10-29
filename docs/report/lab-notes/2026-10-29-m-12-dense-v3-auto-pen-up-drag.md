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

The compact photo needed the `WSW-20261029-004` registration and template
changes before it could be evaluated. The primary extraction was:

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

The same extraction was repeated at station thresholds 20, 70, and 80.
Analysis of the threshold-55 CSV completed and produced a rejected profile
report at `samples\gcode\bed-error-analysis-dense-91-v3-auto.json`.

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
4. Repeat extraction at thresholds 20, 55, 70, and 80.
5. Project every same-angle pen-up travel segment back onto the photo.
6. Compare image contrast along the commanded travel path with parallel blank
   controls.
7. Inspect the generated G-code around the confirmed drag and automated
   candidates to determine whether `M5` and its `P115` acknowledgement
   preceded each move.

## Results

- The compact-image filter initially admitted the right components, but
  proximity-only selection confused the bottom-left fiducial with a nearby
  station mark. V-arm shape scoring now resolves the correct four shared
  vertices.
- The dense matcher now refines all 819 station L templates directly from the
  raw image. Thresholds 20, 55, 70, and 80 produce identical station
  coordinates (`0.000 mm` RMS and maximum difference).
- One long pen-up travel has clearly visible ink on the commanded line. An
  automated contrast check ranked four additional locations, but visual
  review did not confirm drags there, so those are treated as false positives.
- The one confirmed travel is preceded by the expected sequence:

  ```text
  M5
  G65 P115 Q1 A1 W2
  G1 X... Y... A... F3000 (travel)
  ```

- The converter did not omit the pen-clear command.
- The corrected fit does not exceed the 5 mm safety bound, but it still fails
  the profile gates: A0 spatial is `0.594 mm` RMS / `1.705 mm` maximum, A0
  control is `0.297 / 0.655 mm`, and leave-one-out is `0.676 / 3.689 mm` with
  `42.1 %` improvement.

## Difficulties and corrective actions

- The original fiducial-size floor assumed a 3072 x 4080 photo and rejected
  this smaller capture. The filter now accepts compact fiducials and ranks
  them by their V-arm dimensions.
- Proximity-only fiducial ranking selected the bottom-left station mark. That
  one error warped the fitted field and initially produced apparent 10 mm
  station errors.
- Connected-component measurement changed with threshold and made the sheet
  look unusable. Per-mark raw-image template refinement removed that
  threshold dependence.
- The obvious faint traces are not planner paths: they lie exactly on
  commanded pen-up travel lines after a successful `M5`/`P115` sequence.

## Interpretation

This sheet remains unaccepted for bed-compensation fitting, primarily because
the corrected A0 and leave-one-out errors exceed the acceptance gates. The
extractor is now repeatable across thresholds, so further image segmentation
changes are not the leading explanation.

The one confirmed drag still indicates an intermittent physical-clearance
failure. It is not sufficient to explain the entire residual field, but it
must be resolved before accepting another calibration run.

## Decisions and next action

- Keep this physical sheet as unaccepted evidence and do not promote a profile
  from it.
- Confirm which toolhead firmware binary is actually running, including whether
  `PEN_CLEAR_EXTRA_LIFT_MS=130` is deployed.
- Run the T-01H no-drag check for at least 30 `M3`/`M5` cycles with
  representative X/Y travel. Record the `p` status after failed-looking `M5`
  events and test low versus high travel speed separately.
- Inspect clamp height and the end of the pen nib if the current 130 ms build
  still leaves trails. Do not increase the pulse blindly beyond 130 ms.

This extends T-01H and M-12; it does not authorize a new compensation profile.
The existing sheet has been preserved, so another 14-inch sheet is not needed
to repeat the software extraction work.
