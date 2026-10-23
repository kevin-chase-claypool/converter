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
  - samples/gcode/bed-error-map.gcode
  - samples/gcode/bed-error-map.csv
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
- The full software suite passes 474 tests with one OpenGL-context skip.

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

- The raw and compensated sheets have not yet been printed. The 0.35 mm RMS,
  0.90 mm maximum, and 10 % improvement gates are software acceptance gates,
  not bench evidence.
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
- `software/tests/test_bed_compensation.py`: layout, analysis, and planner
  regression coverage.
- `samples/gcode/bed-error-map.gcode`: ready-to-run full-field sheet.
- `samples/gcode/bed-error-map.csv`: complete marker measurement worksheet.
- `software/README.md`, `docs/testing/TEST_PLAN.md`,
  `docs/project/ROADMAP.md`, `docs/integration/INTERFACES.md`: operating
  procedure, current behavior, acceptance, and ownership.
