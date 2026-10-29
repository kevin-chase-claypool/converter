# Lab Note: 2026-10-29 - Reject the dense v2 calibration photo

## Objective

Determine whether the completed 91-station `dense-91-v2` physical sheet yields
a repeatable full-field bed compensation profile, or whether its tighter mark
spacing makes photo extraction too unstable for profile fitting.

## Configuration

- Hardware configuration: the existing rotating-bed machine after `G65 P113`;
  no wiring, controller, or registration change was made for this comparison.
- Calibration program: `samples\gcode\bed-error-map-dense-91-v2.gcode`.
- Layout: `dense-91-v2`, 91 stations, nine angle passes, 819 station L marks,
  four outer V fiducials, 3 mm arms, 5 mm pass-lane offset, and eight `M0`
  pauses.
- Pen: one Sakura Pigma Micron for the complete sheet, as required by the
  printed procedure.
- Photo:
  `samples\gcode\bed-error-map-dense-91-v2-photo.jpg`, 3072 x 4080 px,
  SHA-256 `b046475733264168ecb4a15e9de745dcc8a7614e76ae5860011504d6b506bb76`.

## Code, commands, and configuration used

The seeded dense matcher used the shared-corner seed in
`samples\gcode\bed-error-map-dense-91-v2-photo.json`. The fiducial threshold was
fixed at 40 while the station component threshold was varied:

```powershell
python tools\measure_bed_error_photo.py `
  samples\gcode\bed-error-map-dense-91-v2-photo.jpg `
  --layout dense-91-v2 --threshold 55 --fiducial-threshold 40 `
  --blur-radius 6 --seed-diagnostic samples\gcode\bed-error-map-dense-91-v2-photo.json `
  --measurement-out samples\gcode\bed-error-map-dense-91-v2-measured-t55-b6.csv

python tools\analyze_bed_error_calibration.py `
  --measurements samples\gcode\bed-error-map-dense-91-v2-measured-t55-b6.csv `
  --report-out samples\gcode\bed-error-analysis-dense-91-v2-t55-b6.json
```

The same commands were repeated at station thresholds 60, 70, and 80. The
corresponding measurement and analysis files preserve those runs.

## Procedure

1. Print the complete v2 sheet after `G65 P113`.
2. Photograph the complete sheet from directly above.
3. Seed the dense local station matcher from the reviewed shared-corner
   transform.
4. Verify that all four fiducials select the printed V junction.
5. Extract the sheet at four station thresholds while holding the fiducial
   threshold and blur fixed.
6. Compare every station coordinate between runs.
7. Fit each complete extraction independently and apply the normal M-12
   profile gates.

## Results

The physical print showed that the dense layout remained difficult to
separate at its 5 mm lane spacing. The final fiducial junctions were:

| Fiducial | Selected image point |
|---|---:|
| F1 | `(547, 900)` |
| F2 | `(505, 2905)` |
| F3 | `(2568, 2963)` |
| F4 | `(2574, 873)` |

All station coordinates changed materially between threshold runs:

| Threshold pair | RMS displacement | Maximum displacement |
|---|---:|---:|
| 55 vs 70 | `1.007 mm` | `4.659 mm` |
| 55 vs 80 | `1.064 mm` | `3.462 mm` |
| 70 vs 80 | `0.992 mm` | `5.103 mm` |

Fitting each extraction produced:

| Threshold | A0 spatial RMS / max | A0 control RMS / max | Leave-one-out RMS / max | Improvement |
|---|---:|---:|---:|---:|
| 55 | `0.407 / 0.746 mm` | `1.257 / 2.532 mm` | `0.639 / 3.089 mm` | `42.7 %` |
| 60 | `0.411 / 0.723 mm` | `1.038 / 2.286 mm` | `0.652 / 3.891 mm` | `43.4 %` |
| 70 | `0.456 / 0.759 mm` | `0.986 / 3.453 mm` | `0.736 / 4.212 mm` | `36.6 %` |
| 80 | `0.502 / 0.973 mm` | `0.816 / 2.921 mm` | `0.651 / 3.548 mm` | `37.9 %` |

Every run failed the M-12 validation gates. No compensation profile was
created.

## Difficulties and corrective actions

- The label clearance fix removed the direct
  station-number/pass-line crossings, but it did not create enough
  mark-to-mark separation for stable component assignment.
- The closest two pass edges within a v2 station are only `0.5355 mm` apart.
  With a 0.20 mm pen and phone-photo uncertainty, small threshold changes
  replaced measured components with their station-group fallback and moved
  the extracted corner by millimetres.
- Selecting one common nine-pass station shift made the A0 control appear
  artificially perfect. That approach was rejected because it erases the
  repeatability signal that the separate A0 control lane measures.
- The four fiducials each expose three geometric corners. A seed-based nearest
  choice can choose an arm endpoint and scale the entire field. The extractor
  now identifies the shared V junction from its two incident arms.
- A synthetic `dense-91-v3` image with a deliberately biased 30 px seed now
  recovers all four shared fiducial junctions and all 819 station marks.
  Repeating that image at thresholds 55 and 65 changes no coordinate by more
  than `0.01 mm`.

## Interpretation

The v2 sheet contains useful evidence that the dense field changes with bed
position and angle, but it cannot provide a trustworthy profile. The
millimetre-scale extraction dependence is larger than both the M-12 fit
allowance and the adjacent-row clearance problem the denser mesh is intended
to solve.

The raw A0 spatial RMS values are not sufficient acceptance evidence because
the A0 control and leave-one-out failures show that different passes at the
same nominal station are not being measured consistently.

## Decisions and next action

- Reject `dense-91-v2` as a calibration source. Do not fit or promote a profile
  from this photo.
- Preserve v2 files and these threshold runs as failed evidence.
- Print the new `bed-error-map-dense-91-v3.gcode`, whose 6 mm lanes increase
  the closest within-station edge separation to `1.2426 mm`.
- Repeat extraction at multiple thresholds before fitting. If v3 still moves
  by millimetres between thresholds, stop and revise the physical marker
  geometry rather than adding another station ring.

The acceptance gates are in
[`M-12`](../../testing/TEST_PLAN.md#m-12-full-field-bench-procedure). The
corresponding implementation and follow-up record is
[`WSW-20261029-002`](../../changes/windows-software/2026/2026-10-29-dense-bed-v3-measurement-hardening.md).
