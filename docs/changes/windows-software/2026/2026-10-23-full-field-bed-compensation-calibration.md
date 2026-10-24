---
id: WSW-20261023-004
date: 2026-10-23
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/bed_calibration.py
  - software/converter_core/bed_compensation.py
  - software/converter_core/gcode.py
  - software/converter_core/settings.py
  - software/qt_svg_to_gcode.pyw
  - tools/make_bed_error_calibration.py
  - tools/analyze_bed_error_calibration.py
  - tools/measure_bed_error_photo.py
  - samples/gcode/bed-error-map.gcode
  - samples/gcode/bed-error-map.csv
  - samples/gcode/bed-error-map-2026-10-23.csv
  - samples/gcode/bed-error-compensation-2026-10-23.json
tags:
  - theta
  - bed
  - calibration
  - compensation
  - fiducials
  - planner
  - repeatability
related:
  - WSW-20261023-003
  - ADR-009
---

# Full-field bed compensation calibration

## Summary

Added a one-sheet calibration that separates A=0 position dependence from the
rotation contribution and an A=0 repeatability control. A companion analyzer
turns complete measurements into a checked, optional machine-XY compensation
profile. The converter now applies that profile after theta planning and P100
registration, with identical subdivision in preview and saved G-code.

## Reason

Two dense centre-calibration photographs reproduced a large spatial spread but
left a centre-only residual of about 0.37 mm RMS and 0.50 mm maximum. A P100
centre offset therefore cannot remove the remaining striations. The operator
also found that closely spaced wet marks contaminated prior sheets. The new
layout uses one pen, separated angle lanes, printed station numbers, four pose
fiducials, and controlled drying pauses so position, angle, and repeatability
are distinguishable without a multi-pen tip offset.

## Implementation

- `bed-error-map.gcode` covers a 13-inch field with 37 numbered stations on
  50, 95, and 150 mm rings. Four large fiducials establish the sheet pose.
- Pass 1 draws the A=0 reference. Passes 2-4 replay the same positions at
  90/180/270 degrees in 10 mm-separated lanes. Pass 5 is a second A=0 control
  after the complete rotation sequence.
- The program uses one 0.20 mm pen, returns the bed to A=0 before each of four
  drying `M0` pauses, emits no bare `G0` rotation, and leaves G54 unchanged.
- The analyzer requires every generated measurement row, removes common sheet
  scale/rotation/translation with the fiducials, reports A=0 spatial error,
  A=0 control residual, angle-at-position spread, and leave-one-station-out
  profile residual. It can correlate those fields with a
  `bed_mesh_probe.py` CSV.
- Profile validation refuses incomplete data, implausible scale, uncovered
  artwork, corrections above 5 mm, or a profile that fails the residual and
  improvement gates unless the operator explicitly overrides the gate.
- Measured errors are bed-frame displacements. Each non-zero-angle correction
  is rotated by its bed angle before it is stored as a machine-XY correction:
  `C_machine = -R(theta) * error_bed`. The verification comparison uses
  independently normalized before/after sheets rather than fitting the test
  sheet back into itself.
- The v2 profile stores scattered circular-sheet samples rather than a
  rectangular grid full of unmeasured corner cells. Local affine interpolation
  evaluates correction vectors for any planned bed point.
- `plan_program` loads the profile once. Both G-code and preview add the
  correction after rotation, use the corrected points for travel and feed
  length, and combine polar and compensation subdivision. A saved compensated
  program records the profile fingerprint, coverage, and maximum correction.
  A blank profile path preserves the uncompensated coordinate path and header.
- `make_bed_error_calibration.py --compensation ...` emits a compensated
  verification sheet so the same measurement analysis can be applied after a
  profile has been fitted.
- `measure_bed_error_photo.py` identifies the four fiducials, 185 station L
  marks, and 74 label glyphs, fits a projective sheet transform, extracts each
  L corner, and writes the complete measurement CSV plus a deterministic
  expected/detected overlay.

## Verification

- The generated raw sheet is 2,088 lines. Its measured ink extent is
  163.754 mm radius inside the 165.100 mm planned field and 177.800 mm stock.
- `check_gcode_motion.py --strict` passes: 0 degrees of drawing A motion,
  0 motor-deg/s A rate, six fed pen-up rotations, and no bare `G0` rotation.
- Tests cover round-field bounds, five-pass structure, four drying pauses,
  complete/incomplete measurement handling, fiducial pose removal, finite
  sample interpolation, angle wrap, correction bounds, coverage rejection,
  synthetic field recovery, leave-one-station-out acceptance, bed-mesh
  correlation, compensated verification mode, and G-code/preview point parity.
- The full software suite passes 480 tests with one OpenGL-context skip.
- **Bench run (2026-10-23):** photo `cal.jpg` produced the exact expected
  component counts (4 fiducials, 185 station Ls, 74 label glyphs) and all 189
  measurement rows. The maximum expected-to-detected marker offset was
  `6.863 px`, well below the 10 mm lane separation.
- A=0 spatial error was `0.292 mm` RMS / `0.537 mm` maximum. The independent
  A=0 control after rotations measured `0.176 mm` RMS / `0.369 mm` maximum.
- The 90/180/270 residual RMS values were `0.752 / 0.784 / 0.557 mm`.
  Leave-one-station-out profile prediction was `0.197 mm` RMS / `0.552 mm`
  maximum, a `66.1 %` improvement over raw station error.
- The first profile (`911d2694c8c9`) passed the fitter but failed its
  compensated print: overall raw RMS rose from `0.581` to `1.169 mm`, and the
  180-degree error approximately doubled from `0.793` to `2.003 mm` RMS.
  A=0 stayed approximately unchanged, identifying a missing bed-to-machine
  frame rotation rather than a registration change.
- The corrected profile has fingerprint `2cdf3731de4a`, `165.1 mm` coverage,
  and a `1.331 mm` maximum correction. Regenerated
  `bed-error-verify.gcode` contains that fingerprint, reaches a maximum
  `163.940 mm` radius, and passes strict motion analysis.
- **Bench verification (2026-10-23):** the corrected compensated sheet
  assigned all 185 stations with `4.935 px` maximum assignment distance.
  Overall station RMS fell from `0.581` to `0.338 mm`, maximum from `1.309` to
  `0.752 mm`, and error by `41.9 %`. The 90/180/270 RMS values fell to
  `0.278/0.389/0.353 mm`; every M-12 verification gate passed. Thresholds 18,
  20, and 22 agreed within `0.001 mm` RMS and `0.010 mm` maximum.
- The existing bed mesh showed mixed coupling: A=0 Y error `r=-0.548`,
  90-degree magnitude `r=-0.574`, and 270-degree magnitude `r=+0.744`.
  Position and rotation/plane/carriage effects are both present.
- Extraction thresholds 18, 20, and 22 all produced the exact `4/185/74`
  component counts. A=0 spatial RMS stayed `0.290..0.292 mm`, leave-one-out
  RMS stayed `0.194..0.197 mm`, and the maximum fitted correction stayed
  `1.271..1.331 mm`.
- The first compensated verification failed, as documented below. After the
  machine-frame rotation fix and independent verification comparison were
  added, the full suite finished at 480 passing tests with one
  OpenGL-context skip.

## Struggles and rejected approaches

- The unfinished 7 x 7 square covered only +/-105 mm and required fictitious
  corner samples outside the round stock. It was replaced by a circular polar
  station layout with scattered interpolation.
- Five coloured pens made the sheet easier to segment but added a different
  tip offset for every pass and repeated the wet-line problem. One pen with
  known position-coded lanes removes that variable.
- Fitting a single centre vector into the profile would double-compensate P100.
  Fiducials remove the common pose, and the profile carries only the residual
  spatial/angular field.
- Interpolating the circular field by bilinear square-grid lookup cannot
  represent missing corners. Plain inverse-distance interpolation left a
  synthetic linear field with unnecessary residual, so the runtime uses a
  local affine fit with an inverse-distance fallback.

## Risks and follow-up

- The raw measurement sheet and corrected compensated verification are
  bench-verified. Profile `2cdf3731de4a` is accepted for the current machine
  configuration. A localized residual remains at stations 09/14, A=270; the
  overall result is `0.338 mm` RMS / `0.752 mm` maximum. Do not refit from the
  verification sheet merely to reduce that local point because it would make
  the validation circular.
- Fiducial fitting removes a common affine pose. That is intentional because
  P100 owns registration, but a real global X/Y scale or skew defect belongs
  in `$100`/`$101` or mechanical alignment, not in this residual map.
- Height correlation can show whether the measured field follows the bed mesh.
  It cannot by itself separate paper deformation from the bed surface because
  the probe includes the paper.
- Any bed, paper mounting, toolhead, carriage, pen-clamp, tension, or
  registration change can invalidate the profile. Re-run the sheet after those
  changes and keep the honest residual, including failed gates, in the lab
  note.
- Do not change tape or attempt to flatten a bubble after the first drawing
  mark. A later retaped sheet could not be assigned reliably and is treated as
  invalid rather than as compensation evidence.

## Files

- `software/converter_core/bed_calibration.py`: station layout, fiducial and
  measurement model, profile fitting, validation, and height correlation.
- `software/converter_core/bed_compensation.py`: profile schema, bounded
  interpolation, runtime correction, and subdivision estimate.
- `software/converter_core/gcode.py`: planner/preview post-registration map.
- `software/converter_core/settings.py`: optional profile path.
- `software/qt_svg_to_gcode.pyw`: **Bed compensation JSON** file selector.
- `tools/make_bed_error_calibration.py`: raw and compensated sheet generator.
- `tools/analyze_bed_error_calibration.py`: measurement-to-profile CLI.
- `tools/measure_bed_error_photo.py`: rectifies and measures the completed
  one-pen sheet from an overhead photograph.
- `software/tests/test_bed_compensation.py`: layout, analysis, and planner
  regression coverage.
- `software/tests/test_bed_photo_measurement.py`: photo homography, L-corner,
  and measurement CSV coverage.
- `samples/gcode/bed-error-map.gcode`: ready-to-run full-field sheet.
- `samples/gcode/bed-error-map.csv`: complete marker measurement worksheet.
- `samples/gcode/bed-error-map-2026-10-23.csv`: completed photo measurement.
- `samples/gcode/bed-error-map-2026-10-23-photo.json`: image hash,
  component counts, fiducial pixels, homography, and assignment statistics.
- `samples/gcode/bed-error-analysis-2026-10-23.json`: measured field,
  validation, and bed-mesh correlation report.
- `samples/gcode/bed-error-compensation-2026-10-23.json`: corrected,
  bench-verified profile.
- `samples/gcode/bed-error-verify.gcode`: compensated verification program.
- `samples/gcode/bed-error-verify-frame-error-2026-10-23.csv`: rejected first
  verification measurement.
- `samples/gcode/bed-error-verify-frame-error-photo-2026-10-23.json`: rejected
  verification extraction and image hash.
- `samples/gcode/bed-error-verify-frame-error-analysis-2026-10-23.json`:
  before/after comparison that exposed the frame error.
- `samples/gcode/bed-error-verify-pass-2026-10-23.csv`: passing corrected
  verification measurement.
- `samples/gcode/bed-error-verify-pass-photo-2026-10-23.json`: passing photo
  extraction, image hash, pose transform, and assignment statistics.
- `samples/gcode/bed-error-verify-pass-analysis-2026-10-23.json`: independent
  before/after comparison and acceptance result.
- `samples/gcode/bed-mesh-2026-10-11.csv`: mesh used for the correlation.
- `docs/report/lab-notes/2026-10-23-m-12-full-field-bed-calibration.md`:
  bench extraction, measurements, correlation, and acceptance decision.
- `docs/report/lab-notes/assets/2026-10-23-m-12-full-field-bed-calibration.jpg`
  and `...-overlay.jpg`: source photo and detected-marker overlay.
- `docs/report/lab-notes/assets/2026-10-23-m-12-bed-compensation-frame-error.jpg`
  and `...-overlay.jpg`: failed compensated verification.
- `docs/report/lab-notes/assets/2026-10-23-m-12-bed-compensation-frame-error-vectors.png`:
  before/after vector fields that exposed the frame error.
- `docs/report/lab-notes/2026-10-23-m-12-retaped-verification-invalid.md` and
  `assets/2026-10-23-m-12-retaped-verification-invalid.jpg`: rejected retaped
  sheet and handling boundary.
- `docs/report/lab-notes/assets/2026-10-23-m-12-full-field-bed-error-vectors.png`:
  A=0 spatial, rotation-residual, and control vector fields.
- `docs/report/lab-notes/2026-10-23-m-12-compensated-verification-pass.md`,
  `assets/2026-10-23-m-12-compensated-verification-pass.jpg`, and
  `assets/2026-10-23-m-12-compensated-verification-pass-overlay.png`: accepted
  run, source photo, and measured-marker overlay.
- `software/README.md`, `docs/testing/TEST_PLAN.md`,
  `docs/project/ROADMAP.md`, `docs/integration/INTERFACES.md`: operating
  procedure, current behavior, acceptance, and ownership.
