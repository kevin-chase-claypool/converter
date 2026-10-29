---
id: WSW-20261029-006
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - samples/gcode/bed-error-map-dense-91-v3-centered-measured-t55.csv
  - samples/gcode/bed-error-compensation-2026-10-29-dense-v3-candidate.json
  - samples/gcode/bed-error-analysis-dense-91-v3-centered.json
  - samples/gcode/bed-error-verify-dense-91-v3-centered.gcode
  - samples/gcode/bed-error-verify-dense-91-v3-centered.csv
tags:
  - bed-calibration
  - bed-compensation
  - dense-mesh
  - p100
  - verification
related:
  - WSW-20261029-002
  - WSW-20261029-004
  - RPSW-20261029-001
---

# Fit the centered dense v3 calibration candidate

## Summary

The centered 91-station v3 sheet produced a complete, threshold-repeatable
calibration candidate. Candidate `18bfb4ed1c33` passes every fitting gate and
an independent compensated verification sheet has been generated. The active
profile remains `4bad792e35ad` until that verification passes.

## Reason

The previous dense v3 sheet was measured before the last P100 center
adjustments and failed validation. After centering, a fresh v3 auto sheet
produced a visibly improved field, so it was extracted and fitted without
manual point edits.

## Implementation

- Preserve the 1709 x 2269 source photo and t20/t55/t80 measurements.
- Use V-shape fiducial selection and per-mark template refinement.
- Fit the field against `samples\gcode\bed-mesh-2026-10-11.csv`.
- Write a `165.100 mm` candidate profile with a `1.142 mm` maximum correction.
- Generate a matching dense-v3 compensated verification program with profile
  fingerprint `18bfb4ed1c33`.

## Verification

- All three extraction thresholds produced identical station coordinates.
- A0 spatial error: `0.518 mm` RMS / `0.890 mm` maximum.
- A0 control error: `0.353 / 0.783 mm`.
- Leave-one-station-out prediction: `0.274 / 0.760 mm`.
- Improvement: `50.2 %`.
- The generated verification program passes macro parsing and strict motion
  checks.

## Struggles and rejected approaches

The earlier uncentered sheet showed large A0 residuals and failed profile
gates. No image-derived profile was promoted from that result. The single
visible pen-up drag on the earlier sheet is retained as separate T-01H
evidence and was not used to excuse or alter the centered fit.

## Risks and follow-up

The centered profile is not accepted until a fresh physical verification
sheet improves overall RMS and maximum error without worsening an angle stage.
The outer extrapolated annulus and the intermittent pen-clear behavior remain
open.

## Files

- `samples/gcode/bed-error-map-dense-91-v3-centered-*`: source photo,
  diagnostics, overlays, and three threshold measurements.
- `samples/gcode/bed-error-compensation-2026-10-29-dense-v3-candidate.json`:
  gate-passing candidate profile.
- `samples/gcode/bed-error-analysis-dense-91-v3-centered.json`: complete fit
  report.
- `samples/gcode/bed-error-verify-dense-91-v3-centered.gcode` and `.csv`:
  fresh-sheet verification.
- `docs/report/lab-notes/2026-10-29-m-12-dense-v3-centered-calibration.md`:
  detailed bench and extraction record.
