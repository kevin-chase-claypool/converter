# Lab Note: 2026-10-26 - M-12 post-repair compensated verification

## Objective

Determine whether candidate `efe87c63b54d` reduces the residual bed error on an
independent compensated sheet after the NE drag-chain pillar repair and motor
work.

## Configuration

- Hardware revisions: operator reports the straight NE drag-chain pillar is
  installed. The exact Y/A motor and TB6600 build energized for this sheet was
  not independently captured.
- Wiring/pin map: unchanged per the operator.
- Firmware commit/build: not captured.
- grblHAL settings: no setting change was made during the nine passes.
- Converter settings/sample:
  `samples\gcode\bed-error-verify-2026-10-26-post-repair.gcode`, generated
  with candidate `efe87c63b54d` and bed-frame angular interpolation.
- Instruments: portrait-angle phone photo
  `samples\gcode\bed-error-verify-2026-10-26-post-repair-photo.jpg`.

## Code, commands, and configuration used

```powershell
py tools\measure_bed_error_photo.py `
  samples\gcode\bed-error-verify-2026-10-26-post-repair-photo.jpg `
  --threshold 20 --blur-radius 18 `
  --minimum-station-dimension 17 `
  --mask-center-fraction 0.5,0.5 --mask-radius-fraction 0.48 `
  --measurement-out samples\gcode\bed-error-verify-2026-10-26-post-repair-measured.csv `
  --diagnostic-out samples\gcode\bed-error-verify-2026-10-26-post-repair-photo.json `
  --overlay-out samples\gcode\bed-error-verify-2026-10-26-post-repair-overlay.jpg

py tools\analyze_bed_error_calibration.py `
  --measurements samples\gcode\bed-error-verify-2026-10-26-post-repair-measured.csv `
  --compare-to samples\gcode\bed-error-map-2026-10-26-measured.csv `
  --report-out samples\gcode\bed-error-verify-2026-10-26-post-repair-analysis.json
```

## Procedure

1. Run `G65 P113` and leave the registered `G54` frame unchanged.
2. Plot all nine compensated passes on an independent secured sheet using the
   same 0.20 mm pen and waiting at every `M0`.
3. Photograph the complete sheet from above.
4. Extract all four fiducials and 333 station marks.
5. Compare the normalized compensated errors to the original uncompensated
   post-repair calibration at the same station and angle.
6. Repeat extraction at `18/18` and `22/18` threshold/blur to check whether
   the result depends on image processing.

## Results

- Extraction resolved exactly four fiducials, 333 station Ls, and 74 labels.
  Assignment error was `3.450 / 6.427 / 9.943 px` minimum / median / maximum.
- Overall RMS fell from `1.744 mm` to `0.218 mm`, an `87.5 %` improvement.
- Maximum error fell from `2.965 mm` to `0.591 mm`, an `80.1 %` reduction.
- Every required aggregate gate and the every-angle-stage check passed.

| Stage | Before RMS / max | After RMS / max |
|---|---:|---:|
| A0 reference | `0.324 / 0.626 mm` | `0.205 / 0.415 mm` |
| A45 | `1.071 / 1.440 mm` | `0.225 / 0.591 mm` |
| A90 | `1.859 / 2.265 mm` | `0.217 / 0.495 mm` |
| A135 | `2.423 / 2.763 mm` | `0.210 / 0.367 mm` |
| A180 | `2.610 / 2.965 mm` | `0.201 / 0.429 mm` |
| A225 | `2.416 / 2.794 mm` | `0.205 / 0.399 mm` |
| A270 | `1.793 / 2.188 mm` | `0.228 / 0.399 mm` |
| A315 | `0.905 / 1.243 mm` | `0.277 / 0.494 mm` |
| A0 control | `0.322 / 0.612 mm` | `0.184 / 0.322 mm` |

Threshold sensitivity:

| Threshold / blur | Overall RMS | Overall max | Improvement | Result |
|---|---:|---:|---:|---|
| `18 / 18` | `0.218 mm` | `0.592 mm` | `87.5 %` | PASS |
| `20 / 18` | `0.218 mm` | `0.591 mm` | `87.5 %` | PASS |
| `22 / 18` | `0.247 mm` | `0.706 mm` | `85.8 %` | PASS |

## Difficulties and corrective actions

- The initial `0.47` working radius from the raw calibration photo omitted five
  station marks in this wider verification photo. A `0.48` radius produced the
  expected component counts and a reviewed overlay with one point on every L
  corner.
- A threshold of `22` raises measured RMS and maximum, but remains well inside
  every pass gate. The canonical `20/18` extraction was retained.
- The compensated sheet is evidence of residual error after applying the
  candidate. It was not refitted as a new raw calibration profile.

## Interpretation

The correction works on the physical machine across all measured angles,
including the stages that failed the rejected 2026-10-24 candidate. The result
is large enough and stable enough across extraction thresholds to justify
promoting the profile.

The verification used the `165.100 mm` measured candidate. The active
13.5-inch default `4bad792e35ad` retains those same correction samples and adds
the existing `6.350 mm` extrapolated outer annulus. A generated verification
file from the extrapolated profile changed only its fingerprint header; all
motion lines were identical.

## Decisions and next action

- Accept the post-repair eight-angle map.
- Promote `4bad792e35ad` as the converter's default profile.
- Keep the separate `165.100` to `171.450 mm` edge-band verification open in
  the roadmap.
