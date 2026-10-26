---
id: WSW-20261026-002
date: 2026-10-26
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/measure_bed_error_photo.py
  - software/tests/test_bed_photo_measurement.py
  - samples/gcode/bed-error-map-2026-10-26-photo.jpg
  - samples/gcode/bed-error-map-2026-10-26-measured.csv
  - samples/gcode/bed-error-analysis-2026-10-26-post-repair.json
  - samples/gcode/bed-error-compensation-2026-10-26-post-repair-candidate.json
  - samples/gcode/bed-error-verify-2026-10-26-post-repair.gcode
tags:
  - bed-calibration
  - photo-measurement
  - full-field
  - M-12
  - component-size
related:
  - WSW-20261024-003
  - 2026-10-26-m-12-post-repair-calibration
  - WSW-20261026-003
---

# Make the bed-photo station-size floor configurable

## Summary

Added `--minimum-station-dimension` to the full-field bed-photo tool. It allows
the station-mark classifier to exclude station-number glyphs that scale to the
lower boundary of the station-L size range.

The post-repair 2026-10-26 photo now resolves exactly four fiducials, 333
station Ls, and 74 label glyphs. Its fitted candidate passes every M-12 fitting
gate. The subsequent independent compensated verification also passed and
promoted the matching profile in `WSW-20261026-003`.

## Reason

At the current photo scale, 14 two-digit labels were exactly 16 px on their
largest dimension. The detector admitted them as station-L candidates and
reported 347 candidates instead of 333. The same photo also had 19 station Ls
outside the tested `0.44` working-circle radius, so the station-number
miscount partly masked the incomplete crop.

Changing only the circle recovered all station marks but mixed the larger
labels into the station set. A configurable lower bound lets a reviewed scan
exclude those glyphs without changing the default behavior for earlier photos.

## Implementation

- `measure_photo()` accepts `minimum_station_dimension` and applies it in both
  standard and seed-assisted component selection.
- `_station_sized_components()` centralizes the station-candidate size filter.
- The CLI exposes `--minimum-station-dimension`, defaulting to `16`.
- The post-repair analysis used dimension `17`, assignment tolerance `23 px`,
  working centre `(0.5, 0.5)`, and working radius `0.47`.

## Verification

- Full converter discovery passes `547` tests with one expected OpenGL-context
  skip; the focused photo-measurement module passes all `8` tests.
- Canonical extraction: four fiducials, 333 station Ls, and 74 labels.
- Assignment error: `4.159 / 12.968 / 22.178 px` minimum / median / maximum.
- A0 spatial error: `0.324 mm` RMS / `0.626 mm` maximum.
- A0 control residual: `0.209 mm` RMS / `0.373 mm` maximum.
- Leave-one-station-out: `0.212 mm` RMS / `0.503 mm` maximum, an `87.8 %`
  improvement over raw error.
- Candidate fingerprint: `efe87c63b54d`; maximum correction `2.988 mm`.
- Threshold/blur sweeps from `15/15` through `22/18` kept leave-one-out RMS
  at `0.211-0.213 mm`, maximum at `0.503-0.552 mm`, and improvement at
  `87.7-87.8 %`.
- `bed-error-verify-2026-10-26-post-repair.gcode` contains the candidate
  fingerprint and passes strict motion preflight with no bare rotating `G0`.

## Struggles and rejected approaches

- Keeping the tested `0.44` radius omitted 19 printed stations.
- Widening the circle alone produced 347 station candidates because 14 labels
  also measured 16 px.
- Changing the default floor globally would alter classification for older
  photos, so the floor remains opt-in.
- Preliminary threshold scans returned incomplete or mixed component sets and
  were not used to fit the final candidate.

## Risks and follow-up

- The larger `23 px` assignment tolerance compensates for perspective and
  centroid landing error in this rotated photo. The generated overlay was
  reviewed at full field to confirm every green measured point lands on an L
  corner.
- The independently compensated sheet passed the `--compare-to` gates; see
  `WSW-20261026-003` for the promotion and verification evidence.

## Files

- `tools/measure_bed_error_photo.py`: configurable station-size floor.
- `software/tests/test_bed_photo_measurement.py`: focused filter regression.
- `software/README.md`: command guidance for larger labels and crop geometry.
- `samples/gcode/bed-error-map-2026-10-26-*`: source photo, extraction,
  diagnostic, and overlay evidence.
- `samples/gcode/bed-error-*-2026-10-26-post-repair.*`: candidate profile,
  analysis report, verification program, and matching CSV.
