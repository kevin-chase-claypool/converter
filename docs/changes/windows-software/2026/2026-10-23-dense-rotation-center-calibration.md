---
id: WSW-20261023-003
date: 2026-10-23
category: windows-software
affected_categories:
  - windows-software
  - hardware
  - rp23cnc-software
status: implemented
components:
  - software/converter_core/rotation_calibration.py
  - software/tests/test_rotation_calibration.py
  - tools/make_rotation_center_calibration.py
  - tools/fit_rotation_center.py
  - samples/gcode/rotation-center-calibration.gcode
  - samples/gcode/rotation-center-calibration.csv
  - samples/gcode/rotation-center-calibration-2026-10-23.csv
  - samples/gcode/rotation-center-calibration-2026-10-23-repeat.csv
tags:
  - theta
  - center
  - calibration
  - repeatability
  - bed
  - runout
related:
  - WSW-20261023-002
  - 2026-10-23-m-12-rotation-center-photo-calibration
---

# Dense balanced rotation-centre calibration

## Summary

The calibration sheet now has 12 stations in a balanced 4 x 3 lattice: three
spatially distributed repeats each of 0, 90, 180, and 270 degrees. It writes a
companion CSV, and the fitter accepts all completed rows, subtracts the 20 mm
pair baseline, averages and removes the A=0 controls, and reports one residual
for the repeated-angle fit.

## Reason

The first four-station sheet placed one sample of each angle at one location.
Its photo-derived control was within about 0.1 mm, but the centre-only fit left
0.350 mm RMS / 0.412 mm maximum residual. That cannot distinguish an
angle-dependent error from a local bed-plane or station effect. Three repeats
per angle across the bed make that distinction observable without another
one-angle spot test.

## Implementation

- The default layout is 12 stations on a 4 x 3 lattice inside the 13-inch test
  footprint. Stations are ordered by angle to reduce unnecessary A reversals.
- Every station contains a 36 mm A=0 reference cross, a 30 mm replay cross,
  an L-fiducial at the reference, and a 20 mm reference-to-replay baseline in
  both axes.
- Printed labels use `ANGLE-REPLICATE` form, for example `0-1`, `90-2`, and
  `270-3`. A direction key at lower centre marks machine +X/+Y.
- The generator writes
  `samples/gcode/rotation-center-calibration.csv`. Empty gap cells are skipped
  by the fitter; a partially completed row is rejected.
- The fitter averages all completed A=0 rows, subtracts that control bias, and
  fits repeated 90/180/270 measurements together. Residuals now include
  station-to-station disagreement instead of only one point per angle.
- A derived radius/edge check prevents a station pair or label from extending
  beyond the selected test diameter.

## Verification

- Tests cover the default 12-station balance, three repeats of every angle,
  the 4 x 3 positions, pair spacing, printed labels, CSV generation and
  parsing, blank-row handling, control-bias removal, and the fitted centre.
- The calibration suite passes 20 tests; the full software suite passes 457
  tests with one OpenGL-context skip.
- `python tools\make_rotation_center_calibration.py` generates the current
  928-line G-code sample and the 13-row measurement CSV.
- `python tools\check_gcode_motion.py
  samples\gcode\rotation-center-calibration.gcode --strict` passes with no
  drawing A motion, no A-rate violation, and no bare `G0` rotation.
- A rendered geometric check shows a 13.9 mm minimum clear distance between
  segments from different stations.
- **Bench run (2026-10-23):** the 12-station photo with three repeats per angle
  was resolved through its fiducials and reference arms. At A=0 the raw Y gap
  varied from `19.0388` to `20.4598` mm across the bed. After removing the
  control bias, per-angle mean offsets were only about 0.1-0.3 mm, while the
  repeated positions scattered by about 0.2-0.45 mm. The centre fit left
  `0.385 mm` RMS / `0.551 mm` maximum residual, so P100 was not changed.
  Completed readings are in
  `samples/gcode/rotation-center-calibration-2026-10-23.csv`; analysis is in
  `docs/report/lab-notes/2026-10-23-m-12-dense-rotation-center-analysis.md`.
- **Repeat photo (2026-10-23):** the same paper was analyzed independently from
  `PXL_20261023_203657257.jpg`. The A=0 Y spread remained `1.039 mm`; the
  angle means stayed small, and the centre-model residual was `0.366 mm` RMS /
  `0.501 mm` maximum. This confirms that the position-dependent field is
  repeatable rather than a one-photo artifact. Repeat readings are in
  `samples/gcode/rotation-center-calibration-2026-10-23-repeat.csv`.

## Struggles and rejected approaches

- The first 12-station concept used a circular ring. Rendering exposed
  overlapping replay arms between adjacent stations, so that layout was
  rejected before use.
- A central direction key intersected a replay arm near the middle of the
  lattice. It was moved to the lower-centre free area.
- A long command line with 12 measurements was rejected as error-prone. The
  companion CSV is generated with the correct station labels and angles.

## Risks and follow-up

- The dense sheet is visually busier; use the printed `ANGLE-REPLICATE` labels
  and L-fiducials rather than trying to infer pair membership from crossings.
- The first bench run confirms that repeated-angle residuals are dominated by
  position-dependent disagreement. Do not change P100 from these samples.
- The next step is to correlate the A=0 spatial residuals with the existing bed
  mesh/probe data and determine whether a mechanical plane/runout correction or
  a separately validated spatial compensation map is appropriate.

## Files

- `software/converter_core/rotation_calibration.py`: balanced layout, labels,
  fiducials, CSV helpers, and control-bias removal.
- `software/tests/test_rotation_calibration.py`: layout, CSV, and fit coverage.
- `tools/make_rotation_center_calibration.py`: G-code and CSV generator.
- `tools/fit_rotation_center.py`: repeated-angle and control-aware fit.
- `samples/gcode/rotation-center-calibration.gcode`: 12-station bench program.
- `samples/gcode/rotation-center-calibration.csv`: matching measurement form.
- `samples/gcode/rotation-center-calibration-2026-10-23.csv`: completed
  bench readings from the first dense-sheet run.
- `samples/gcode/rotation-center-calibration-2026-10-23-repeat.csv`: completed
  readings from the independent repeat photo.
- `software/README.md`, `firmware/README.md`,
  `firmware/grblhal/macros/README.md`, `docs/testing/TEST_PLAN.md`,
  `docs/project/ROADMAP.md`: current usage and acceptance criteria.
