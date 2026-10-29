---
id: WSW-20261029-001
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: superseded
components:
  - software/converter_core/bed_calibration.py
  - software/tests/test_bed_compensation.py
  - software/tests/test_bed_photo_measurement.py
  - samples/gcode/bed-error-map-dense-91-v2.gcode
  - samples/gcode/bed-error-map-dense-91-v2.csv
  - samples/gcode/bed-error-verify-dense-91-v2.gcode
  - samples/gcode/bed-error-verify-dense-91-v2.csv
tags:
  - bed-calibration
  - dense-mesh
  - station-label
  - layout-collision
  - photo-measurement
related:
  - WSW-20261028-002
  - WSW-20261029-002
---

# Separate dense-calibration station numbers from pass lanes

## Summary

The first physical 91-station dense calibration exposed a layout defect:
station-number glyphs were inside the pass-lane footprint. The issued
`dense-91` geometry is preserved for traceability, and the corrected
`dense-91-v2` layout uses narrower pass lanes and moves labels farther inward.
New dense calibration and compensated-verification programs use the same v2
station-number placement.

## Reason

The operator reported marks drawing through many station numbers during the
first dense print. Exact segment analysis found 13 lane/label intersections.
No A=0 reference mark intersected a label, but later passes merged label and
station components, which would make the automated photo assignment
unreliable.

## Implementation

`dense-91-v2` keeps the same 91 station centres, three-digit-safe numbering,
3 mm L marks, 1.8 mm labels, nine angle passes, and outer fiducials. It changes:

- pass-lane offset from 7 mm to 5 mm;
- inward label offset from 10 mm to 14 mm;
- the generated file suffix and CSV `layout_id` to `dense-91-v2`.

The original `dense-91` layout remains registered so any already captured
measurement CSV retains its original geometry. The corrected calibration and
verification use `dense-91-v2`; the analyzer detects the layout identifier in
the measurement CSV.

## Verification

- The new clearance regression failed on `dense-91` with a zero-distance
  intersection, then passed after the layout change.
- Minimum label-to-any-mark separation is `3.790 mm`, leaving room for the
  0.20 mm pen and normal registration error.
- `bed-error-map-dense-91-v2.gcode` and
  `bed-error-verify-dense-91-v2.gcode` both pass macro parsing and strict motion
  checks. Each contains 2,336 drawing moves and eight `M0` pauses.
- All `56` focused bed-calibration tests and all `563` converter tests pass
  with one expected OpenGL-context skip.
- Calibration G-code SHA-256:
  `B937EA2FACDBFD4D2FA9B350AF547A252E9BA51B6B939704245775D73BD04239`;
  compensated verification SHA-256:
  `0CDC159393202E4D0E5526F63F2CB7FDD716FFABCAE23F24758C7148B0B5B619`.
  Both 823-row CSVs share
  `6FE1657BC4E055DD40D5EE6A66462CF7B43B74137BEA517F1961E429807279CF`.

## Struggles and rejected approaches

- The original collision check covered fiducials against station marks but not
  station labels against their own pass lanes. That missed a visible print
  defect despite the overall layout extent passing.
- Moving only the labels inward by 4 mm would have increased interference with
  the next inner ring. Reducing the lanes from 7 mm to 5 mm as well preserved
  both label-to-mark and ring-to-ring separation.
- Renaming the corrected geometry instead of modifying `dense-91` prevents an
  old measurement CSV from being interpreted with new coordinates.

## Risks and follow-up

The sheet currently being printed with `dense-91` cannot be repaired in place
and must be restarted on a fresh sheet using the current dense layout.

The v2 physical sheet was subsequently completed and photographed. Its marks
were too crowded for repeatable component assignment: changing the extraction
threshold moved station coordinates by about `1.0 mm` RMS, the A0 control was
`1.257 mm` RMS / `2.532 mm` maximum, and leave-one-out prediction reached
`0.639 mm` RMS / `3.089 mm` maximum. No v2 compensation profile was accepted.
`dense-91-v3` supersedes its 5 mm pass lanes with 6 mm lanes; see
`WSW-20261029-002`.

## Files

- `software/converter_core/bed_calibration.py`: versioned dense layouts and
  label placement.
- `software/tests/test_bed_compensation.py`: red-first label/mark clearance
  regression.
- `software/tests/test_bed_photo_measurement.py`: v2 layout metadata.
- `samples/gcode/bed-error-map-dense-91-v2.gcode` and `.csv`: corrected
  calibration sheet.
- `samples/gcode/bed-error-verify-dense-91-v2.gcode` and `.csv`: matching
  compensated verification sheet.
- `software/README.md`, `docs/testing/TEST_PLAN.md`, and
  `docs/project/ROADMAP.md`: current procedure and supersession guidance.
