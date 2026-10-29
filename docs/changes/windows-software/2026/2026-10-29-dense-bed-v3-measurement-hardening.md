---
id: WSW-20261029-002
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/bed_calibration.py
  - software/tests/test_bed_compensation.py
  - software/tests/test_bed_photo_measurement.py
  - tools/measure_bed_error_photo.py
  - samples/gcode/bed-error-map-dense-91-v3.gcode
  - samples/gcode/bed-error-map-dense-91-v3.csv
  - samples/gcode/bed-error-verify-dense-91-v3.gcode
  - samples/gcode/bed-error-verify-dense-91-v3.csv
tags:
  - bed-calibration
  - dense-mesh
  - photo-measurement
  - fiducial
  - marker-separation
related:
  - WSW-20261029-001
  - WSW-20261028-002
---

# Harden dense calibration extraction and issue v3

## Summary

The completed v2 physical sheet could not support a repeatable compensation
fit. Its 5 mm pass lanes left too little separation between marks for stable
component assignment, and independent fiducial-corner selection could choose
an arm endpoint instead of the printed V junction when the seed transform was
biased.

`dense-91-v3` increases the pass-lane offset to 6 mm while preserving the 91
station centres and all nine angle passes. The photo tool now identifies each
fiducial's shared vertex from its two incident arms, so a nearby but imperfect
seed cannot switch the fitted sheet scale or translation to another corner.
The original `dense-91` and `dense-91-v2` definitions remain registered for
their already issued files and measurements.

## Reason

The v2 sheet resolved all expected marks, but the extracted station positions
moved by approximately `1.0 mm` RMS when the image threshold changed between
55, 60, 70, and 80. The resulting A0 control and leave-one-out errors failed
the M-12 gates even though the raw A0 spatial RMS looked acceptable.

V2's closest pair of station-mark edges is `0.5355 mm` apart within one
station. That is too small relative to the 0.20 mm pen, phone-photo resolution,
and local registration error. The fiducials also expose three plausible
geometric vertices; choosing the one nearest a seed prediction can silently
select a tip rather than the common corner used to define sheet coordinates.

## Implementation

- Preserve `dense-91` and `dense-91-v2` as immutable historical layouts.
- Make `dense-91-v3` the current dense layout. It uses the same 91 stations,
  three radii, mark arms, labels, and fiducials as v2, with a 6 mm lane offset.
- Increase the closest edge separation between passes of one station from
  `0.5355 mm` to `1.2426 mm`.
- Keep the minimum label-to-any-station-mark separation at `2.801 mm` and the
  minimum station-to-fiducial separation at `5.971 mm`.
- Select a fiducial's shared V junction as the candidate with the shortest two
  incident edges, rather than the candidate nearest the seed prediction.
- Keep separate station, fiducial, minimum-dimension, and maximum-dimension
  thresholds for dense photo extraction.
- Generate v3 calibration and compensated-verification programs with the
  accepted profile `4bad792e35ad`.

## Verification

- The new fiducial regression failed before the fix by selecting a tip near a
  biased seed and passes after the change.
- A synthetic 2100 x 2100 v3 sheet renders all four fiducials and 819 station
  L marks. With a 30 px biased seed, extraction recovers the four shared
  junctions within 2 px and matches all 819 expected station marks. Repeating
  the same image at thresholds 55 and 65 changes no measured coordinate by
  more than `0.01 mm`.
- The projected v3 layout has 91 stations, 819 station marks, four fiducials,
  rings at `0/30/60/90/120/148.5 mm`, and a `164.0 mm` planned extent.
- All `60` focused bed tests pass. The full converter suite passes all `567`
  tests with one expected OpenGL-context skip.
- Both generated programs pass macro parsing and strict motion checks with
  2,336 drawing moves, 1,069 travel moves, eight `M0` pauses, and no bare
  rotating `G0`.
- Calibration G-code SHA-256:
  `818D4955B59F17BAE5FF1DCB6A26E4B182CB00D770FF5C702E9A83DF1177BE06`;
  compensated verification SHA-256:
  `2BDB40BA5961D5A54AC53955CAB88F652804728E8450A2CD9D4634A1C0A2CEF2`.
  Both 823-row CSVs share
  `C475F520D4207150003307319DBCEA9483DC486EF88522BE74241EA01EA313FF`.

## Struggles and rejected approaches

- The v2 A0 field initially looked plausible at `0.407 mm` RMS / `0.746 mm`
  maximum, but its A0 control was `1.257 / 2.532 mm` and leave-one-out was
  `0.639 / 3.089 mm`. Repeating extraction at nearby thresholds did not
  reproduce station coordinates closely enough to trust those values.
- Keeping the 5 mm lanes and changing only thresholds could not remove the
  crowding. Using one common station shift for all nine passes made the A0
  control appear artificially perfect and discarded the run-to-run evidence
  the control lane exists to measure.
- Treating the two fiducial tips as interchangeable changes the sheet scale by
  several percent. Accepting the nearest seed vertex made that failure depend
  on the previous photo and image threshold.

## Risks and follow-up

No physical v3 sheet has been printed or measured. The next gate is a fresh v3
sheet after `G65 P113`, followed by extraction at multiple thresholds and the
standard M-12 fit. Do not fit, promote, or apply a v3 profile from the rejected
v2 photograph.

The remaining outer-field and angular residual questions stay open until v3
produces a repeatable field and an independent compensated verification. If v3
still changes by millimetres between thresholds, stop profile fitting and
revisit the mark geometry before increasing station count again.

## Files

- `software/converter_core/bed_calibration.py`: versioned dense layouts and
  current v3 geometry.
- `tools/measure_bed_error_photo.py`: dense component bounds, separate
  thresholds, seeded station matching, and shared-vertex fiducial selection.
- `software/tests/test_bed_compensation.py`: v3 samples, numbering, spacing,
  and layout regressions.
- `software/tests/test_bed_photo_measurement.py`: dense bounds, ambiguous
  fiducial corner, and synthetic v3 extraction regressions.
- `samples/gcode/bed-error-map-dense-91-v3.gcode` and `.csv`: next physical
  calibration sheet.
- `samples/gcode/bed-error-verify-dense-91-v3.gcode` and `.csv`: independently
  compensated follow-up sheet, not yet printed.
- `docs/report/lab-notes/2026-10-29-m-12-dense-v2-photo-rejected.md`: v2
  physical and extraction evidence.
