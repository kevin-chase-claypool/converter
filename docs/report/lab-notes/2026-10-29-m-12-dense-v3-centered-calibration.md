# Lab Note: 2026-10-29 - Dense v3 centered calibration candidate

## Objective

Measure the new 91-station v3 sheet after the latest P100 center-position
adjustment and determine whether it produces a valid bed-compensation
candidate.

## Configuration

- Hardware: RP23CNC / `RP23U5XBB` V1.01 with the production installed pen.
- P100 source at the time of analysis: X `2.30`, Y `0.31`; the operator
  reports the pen is visually centered and the sheet looks materially better.
- Program: `samples\gcode\bed-error-map-dense-91-v3-auto.gcode`, 91 stations,
  nine passes, five-second automatic pass dwells, and no manual `M0` stops.
- Pen: Pigma Micron 005 for all passes.
- Photo: `samples\gcode\bed-error-map-dense-91-v3-centered-photo.jpg`,
  1709 x 2269 px, SHA-256
  `6FC1DE1713C256D6EC5C56B4968510B0DCF340E029D15576271E795D0B64347D`.
- Bed mesh: `samples\gcode\bed-mesh-2026-10-11.csv`.

## Code, commands, and configuration used

```powershell
python tools\measure_bed_error_photo.py `
  samples\gcode\bed-error-map-dense-91-v3-centered-photo.jpg `
  --layout dense-91-v3 --threshold 55 --fiducial-threshold 25 `
  --blur-radius 6 `
  --seed-diagnostic samples\gcode\bed-error-map-dense-91-v3-auto-photo.json `
  --measurement-out samples\gcode\bed-error-map-dense-91-v3-centered-measured-t55.csv `
  --diagnostic-out samples\gcode\bed-error-map-dense-91-v3-centered-photo.json `
  --overlay-out samples\gcode\bed-error-map-dense-91-v3-centered-overlay-t55.jpg

python tools\analyze_bed_error_calibration.py `
  --measurements samples\gcode\bed-error-map-dense-91-v3-centered-measured-t55.csv `
  --bed-mesh samples\gcode\bed-mesh-2026-10-11.csv `
  --profile-out samples\gcode\bed-error-compensation-2026-10-29-dense-v3-candidate.json `
  --report-out samples\gcode\bed-error-analysis-dense-91-v3-centered.json

python tools\make_bed_error_calibration.py `
  --layout dense-91-v3 `
  --compensation samples\gcode\bed-error-compensation-2026-10-29-dense-v3-candidate.json `
  --pass-dwell-seconds 5 `
  --out samples\gcode\bed-error-verify-dense-91-v3-centered-auto.gcode `
  --measurement-out samples\gcode\bed-error-verify-dense-91-v3-centered-auto.csv
```

## Procedure

1. Generate the centered v3 field from the previous reviewed sheet geometry.
2. Extract all four fiducials and all 819 station L marks.
3. Repeat extraction at thresholds 20, 55, and 80.
4. Require identical station coordinates between thresholds.
5. Fit the eight measured angle fields and run leave-one-station-out
   validation against the existing bed mesh.
6. Generate, but do not promote, the independent compensated verification
   sheet.

## Results

- Thresholds 20, 55, and 80 produced identical station coordinate files
  (`0.000 mm` RMS and maximum difference).
- Raw station error: `0.550 mm` RMS / `1.163 mm` maximum.
- A0 spatial error: `0.518 mm` RMS / `0.890 mm` maximum.
- A0 control error: `0.353 / 0.783 mm` RMS / maximum.
- Leave-one-station-out prediction: `0.274 / 0.760 mm` RMS / maximum.
- Improvement from the measured field: `50.2 %`.
- All profile-fitting gates pass.
- Candidate profile: `18bfb4ed1c33`, coverage `165.100 mm`, maximum
  correction `1.142 mm`.
- The bed-mesh correlation is mixed. The A0 vector correlation is weak
  (`r=0.090`), while several angle magnitudes have moderate negative
  correlation; height coupling remains plausible but cannot explain the A0
  spatial field by itself.
- A faint possible travel trace remains visible near the upper-right field.
  It did not prevent repeatable extraction, but remains a pen-clearance
  observation.

## Difficulties and corrective actions

The earlier extraction attempts confused a compact fiducial with a nearby
station mark and depended on connected-component thresholds. Fiducial
V-shape scoring and per-mark template refinement now make the current field
repeatable. No manual point editing was used.

## Interpretation

The centered P100 position produced a materially better and fully gate-passing
candidate field. This remains a candidate, not a replacement: an independent
compensated verification sheet must confirm that the correction lowers the
physical residual.

## Decisions and next action

- Keep profile `4bad792e35ad` active.
- Print `samples\gcode\bed-error-verify-dense-91-v3-centered-auto.gcode` on a
  fresh secured sheet after `G65 P113`; one initial Cycle Start runs all nine
  passes with eight five-second dwells.
- Extract and compare it to the centered baseline with `--compare-to`.
- Promote candidate `18bfb4ed1c33` only if RMS, maximum, and every angle stage
  pass the independent-verification gates.

This closes the calibration-fitting stage only; compensated verification is
still open.
