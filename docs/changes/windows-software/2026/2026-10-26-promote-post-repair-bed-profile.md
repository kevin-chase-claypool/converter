---
id: WSW-20261026-003
date: 2026-10-26
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: verified
components:
  - software/converter_core/settings.py
  - software/tests/test_bed_compensation.py
  - software/tests/test_cmyk_tab.py
  - tools/make_bed_compensation_motion_test.py
  - samples/gcode/bed-error-compensation-2026-10-26-13p5in-extrapolated.json
  - samples/gcode/bed-error-analysis-2026-10-26-13p5in-extrapolated.json
  - samples/gcode/bed-error-verify-2026-10-26-post-repair-photo.jpg
  - samples/gcode/bed-error-verify-2026-10-26-post-repair-measured.csv
  - samples/gcode/bed-error-verify-2026-10-26-post-repair-photo.json
  - samples/gcode/bed-error-verify-2026-10-26-post-repair-overlay.jpg
  - samples/gcode/bed-error-verify-2026-10-26-post-repair-analysis.json
  - samples/gcode/bed-compensation-motion-test.gcode
tags:
  - bed-compensation
  - M-12
  - verification
  - default-profile
  - rotating-bed
---

# Promote the independently verified post-repair bed profile

## Summary

Promoted the post-repair eight-angle correction map to the converter's default
bed compensation profile. The default keeps the existing 13.5-inch coverage by
extrapolating the measured 165.100 mm field to 171.450 mm.

The independent compensated verification passed every M-12 gate. Overall
station RMS fell from `1.744 mm` to `0.218 mm`, maximum error fell from
`2.965 mm` to `0.591 mm`, and every angle stage improved.

## Reason

The previous default profile was measured before the NE drag-chain pillar
repair and motor work. A new full-field sheet passed all fitting gates with
leave-one-station-out error of `0.212 mm` RMS / `0.503 mm` maximum, so an
independent compensated sheet was printed.

The verification reduced overall RMS by `87.5 %` and maximum error by `80.1 %`.
All angle stages improved, including the previously weak A90, A270, A315, and
post-rotation A0 control fields.

## Implementation

- `DEFAULT_BED_COMPENSATION_PATH` now selects
  `bed-error-compensation-2026-10-26-13p5in-extrapolated.json`.
- The active profile fingerprint is `4bad792e35ad`.
- The profile retains the measured corrections through `165.100 mm` and
  extends coverage to `171.450 mm`, matching the existing 14-inch stock minus
  the `6.350 mm` rim margin.
- The 360-degree boundary correction reaches `2.783 mm`, below the `5 mm`
  planner guard.
- The compensated motion-test generator tracks the application default rather
  than duplicating a profile path.
- `bed-compensation-motion-test.gcode` was regenerated with the new default.

## Verification

- Verification extraction found four fiducials, 333 station Ls, and 74 labels;
  component assignment was `3.450 / 6.427 / 9.943 px` minimum / median /
  maximum.
- Overall compensated result: `0.218 mm` RMS / `0.591 mm` maximum, accepted
  against `0.35 / 0.90 mm`.
- RMS improvement: `87.5 %`, accepted against the `30 %` minimum.
- Every angle stage is not worse; the analyzer's
  `every_angle_stage_not_worse` gate is true.
- Threshold sweeps at `18/18`, `20/18`, and `22/18` all pass. Overall RMS was
  `0.218`, `0.218`, and `0.247 mm`; maximum was `0.592`, `0.591`, and
  `0.706 mm`; improvement was `87.5`, `87.5`, and `85.8 %`.
- Regenerated `bed-compensation-motion-test.gcode` passes strict motion
  preflight: `4,235` drawing moves, `0.62 deg` largest drawing-block rotation,
  `211 motor deg/s` peak A rate, `18` fed rotating pen-up moves, and no bare
  rotating `G0`.
- Focused planner, CMYK, motion-test, and wave-isolation suites pass (`135`
  tests); full converter discovery passes `547` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- The first verification-photo mask used the raw calibration photo's `0.47`
  radius and missed five station marks. Widening only to `0.48` produced the
  exact `333 / 74` count, with all measurements assigned below `10 px`.
- The measured candidate used `165.100 mm` coverage for the physical
  verification. Regenerating the same verification program with the promoted
  `171.450 mm` profile changed only the fingerprint header; every motion line
  was byte-identical.
- Changing raw-profile estimators or thresholds is unnecessary: the
  independent threshold sweep reproduced the pass.

## Risks and follow-up

- The inner `165.100 mm` field is independently verified. As before, the outer
  `6.350 mm` annulus from `165.100` to `171.450 mm` remains an extrapolation
  and still needs the separate edge-band test tracked in the roadmap.
- The map remains valid only for the current bed, paper support,
  toolhead/carriage, pen clamp, and registration state.

## Files

- `software/converter_core/settings.py`: selects the new default profile.
- `software/tests/test_bed_compensation.py`: default fingerprint, coverage,
  boundary, and generated-header expectations.
- `software/tests/test_cmyk_tab.py`: CMYK defaults inherit the promoted map.
- `tools/make_bed_compensation_motion_test.py`: tracks the application default.
- `samples/gcode/bed-error-compensation-2026-10-26-13p5in-extrapolated.json`:
  active verified correction samples and extrapolated coverage.
- `samples/gcode/bed-error-verify-2026-10-26-post-repair-*`: independent
  verification photo, extraction, overlay, and comparison.
- `samples/gcode/bed-compensation-motion-test.gcode`: current default-profile
  motion diagnostic.
