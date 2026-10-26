# Lab Note: 2026-10-26 - M-12 post-repair full-field calibration

## Objective

Determine whether the full-field rotating-bed error changed enough after the
NE drag-chain pillar replacement and motor work to justify replacing the failed
2026-10-24 map.

## Configuration

- Hardware revisions: operator reports the stepped NE drag-chain pillar was
  replaced with a straight pillar running on the 3030 extrusion. The exact Y/A
  motor and TB6600 build energized for this sheet was not independently
  captured in the photo or G-code.
- Wiring/pin map: unchanged per the operator.
- Firmware commit/build: not captured.
- grblHAL settings: no setting change was made during the nine passes.
- Converter settings/sample: `samples\gcode\bed-error-map.gcode`, calibration
  v3, 37 stations, nine passes, four fiducials, one 0.20 mm pen, and eight
  drying pauses.
- Instruments: portrait-angle phone photo
  `samples\gcode\bed-error-map-2026-10-26-photo.jpg`.

## Code, commands, and configuration used

```powershell
py tools\measure_bed_error_photo.py `
  samples\gcode\bed-error-map-2026-10-26-photo.jpg `
  --threshold 20 --blur-radius 18 `
  --minimum-station-dimension 17 --maximum-assignment-px 23 `
  --mask-center-fraction 0.5,0.5 --mask-radius-fraction 0.47 `
  --measurement-out samples\gcode\bed-error-map-2026-10-26-measured.csv `
  --diagnostic-out samples\gcode\bed-error-map-2026-10-26-photo.json `
  --overlay-out samples\gcode\bed-error-map-2026-10-26-overlay.jpg

py tools\analyze_bed_error_calibration.py `
  --measurements samples\gcode\bed-error-map-2026-10-26-measured.csv `
  --bed-mesh samples\gcode\bed-mesh-2026-10-11.csv `
  --profile-out samples\gcode\bed-error-compensation-2026-10-26-post-repair-candidate.json `
  --report-out samples\gcode\bed-error-analysis-2026-10-26-post-repair.json

py tools\make_bed_error_calibration.py `
  --out samples\gcode\bed-error-verify-2026-10-26-post-repair.gcode `
  --measurement-out samples\gcode\bed-error-verify-2026-10-26-post-repair.csv `
  --compensation samples\gcode\bed-error-compensation-2026-10-26-post-repair-candidate.json
```

## Procedure

1. Run `G65 P113` and leave the registered `G54` frame untouched.
2. Plot all nine calibration passes on the secured sheet, waiting at every
   `M0` until the prior pass dries.
3. Photograph the complete sheet from above.
4. Extract and review all mark assignments.
5. Fit the eight-angle profile with the current bed mesh.
6. Repeat extraction around the selected threshold/blur to check sensitivity.
7. Generate, but do not promote, the independent compensated verification
   program.

## Results

- Extraction resolved exactly four fiducials, 333 station Ls, and 74 label
  glyphs. All 333 stations assigned with
  `4.159 / 12.968 / 22.178 px` minimum / median / maximum component-centroid
  error.
- The full-field overlay places one measured point on every station L corner.
- A0 spatial error is `0.324 mm` RMS / `0.626 mm` maximum.
- A0 control residual after the complete rotation sweep is `0.209 mm` RMS /
  `0.373 mm` maximum.
- Leave-one-station-out prediction is `0.212 mm` RMS / `0.503 mm` maximum, an
  `87.8 %` improvement over the raw fitted error.
- Candidate `efe87c63b54d` has a `165.100 mm` measured radius and a maximum
  correction of `2.988 mm`, below the `5 mm` bound.
- The final A0 control is substantially better than the failed 2026-10-24
  sheet's `0.684 / 0.901 mm`, and the maximum leave-one-out error fell from
  `1.032` to `0.503 mm`.
- Position variability after removing the common A0 field, RMS / maximum by
  angle:

| Angle | RMS | Maximum |
|---|---:|---:|
| A45 | `0.111 mm` | `0.227 mm` |
| A90 | `0.204 mm` | `0.380 mm` |
| A135 | `0.226 mm` | `0.503 mm` |
| A180 | `0.146 mm` | `0.308 mm` |
| A225 | `0.119 mm` | `0.219 mm` |
| A270 | `0.120 mm` | `0.291 mm` |
| A315 | `0.126 mm` | `0.290 mm` |

Threshold/blur sensitivity:

| Threshold / blur | A0 control RMS / max | Leave-one-out RMS / max | Improvement |
|---|---:|---:|---:|
| `15 / 15` | `0.205 / 0.355 mm` | `0.211 / 0.552 mm` | `87.7 %` |
| `18 / 18` | `0.209 / 0.369 mm` | `0.212 / 0.503 mm` | `87.8 %` |
| `20 / 18` | `0.209 / 0.373 mm` | `0.212 / 0.503 mm` | `87.8 %` |
| `22 / 18` | `0.204 / 0.360 mm` | `0.213 / 0.507 mm` | `87.8 %` |

The generated verification program contains 3,138 lines, eight `M0` pauses,
943 drawing moves, and 436 pen-up travel moves. Strict motion preflight passes:
no bare rotating `G0`, no drawing-block rotation above the cap, and no A-rate
violation. Its header identifies candidate `efe87c63b54d` and the bed-frame
angular interpolation mode.

## Difficulties and corrective actions

- The initial `0.5, 0.5` centre with a `0.44` radius omitted 19 station marks
  near the edge of this rotated photo. A reviewed `0.47` radius recovered them.
- At that radius, 14 station-number labels were exactly 16 px wide and were
  admitted as station Ls, producing 347 candidates. Adding
  `--minimum-station-dimension 17` removed exactly those 14 components and
  produced the expected 333 station components and 74 labels.
- The partial crop mixed missing stations with label-sized candidates, so a
  raw "station candidate" count near 333 was not evidence of a complete sheet.
- The rotated perspective makes component-centroid landing error larger than
  the previous sheet, requiring `23 px` assignment tolerance. The full-field
  overlay was reviewed rather than accepting count alone.
- A real camera shadow remains over part of the sheet, but changing threshold,
  blur, and contrast produced the same accepted residual range.

## Interpretation

This sheet passes every profile-fitting gate and is materially more repeatable
than the 2026-10-24 map. The large reduction in A0 control residual is
consistent with the reported mechanical drag-chain correction. The subsequent
independent compensated sheet proved that the reduction also survives on a
fresh physical print.

The residual still has angle-dependent structure and moderate-to-strong
correlation with the bed mesh at several angles. The mesh includes the paper,
so it cannot separate paper flatness from bed/carriage height error.

## Decisions and next action

- The follow-up independent verification passed; see
  `2026-10-26-m-12-post-repair-compensated-verification.md`.
- Promote `4bad792e35ad`, the 13.5-inch extrapolated form of this measured
  field, as the active default.
- The separate `165.100` to `171.450 mm` edge-band verification remains open in
  the roadmap.

The exact completed verification commands and measurements are recorded in the
follow-up lab note.
