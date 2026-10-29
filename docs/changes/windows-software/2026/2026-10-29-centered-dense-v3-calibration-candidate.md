---
id: WSW-20261029-006
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: superseded
components:
  - samples/gcode/bed-error-map-dense-91-v3-centered-measured-t55.csv
  - samples/gcode/bed-error-compensation-2026-10-29-dense-v3-candidate.json
  - samples/gcode/bed-error-analysis-dense-91-v3-centered.json
  - samples/gcode/bed-error-verify-dense-91-v3-centered-auto.gcode
  - samples/gcode/bed-error-verify-dense-91-v3-centered-auto.csv
  - samples/gcode/bed-error-verify-dense-91-v3-centered-auto-comparison.json
tags:
  - bed-calibration
  - bed-compensation
  - dense-mesh
  - p100
  - verification
related:
  - WSW-20261029-002
  - WSW-20261029-004
  - WSW-20261029-007
  - RPSW-20261029-001
---

# Fit the centered dense v3 calibration candidate

## Summary

The centered 91-station v3 sheet produced a complete, threshold-repeatable
calibration candidate. Candidate `18bfb4ed1c33` passes every fitting gate and
an independent compensated verification sheet was generated. That physical
verification failed the formal promotion gates. The project owner subsequently
promoted the candidate by explicit override; see `WSW-20261029-007`.

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
- Generate matching manual and five-second-dwell dense-v3 compensated
  verification programs with profile fingerprint `18bfb4ed1c33`.

## Verification

- All three extraction thresholds produced identical station coordinates.
- A0 spatial error: `0.518 mm` RMS / `0.890 mm` maximum.
- A0 control error: `0.353 / 0.783 mm`.
- Leave-one-station-out prediction: `0.274 / 0.760 mm`.
- Improvement: `50.2 %`.
- The generated verification program passes macro parsing and strict motion
  checks. The automatic version uses eight `G4 P5` dwells and one initial
  Cycle Start.
- Thresholds 20/55/80 for the verification photo again produced identical
  coordinates.
- Independent verification improved overall RMS from `0.550` to `0.486 mm`
  and improved every angle-stage RMS, but maximum error moved from `1.163` to
  `1.171 mm` and improvement was only `11.6 %`. The required maximum is
  `0.90 mm` and minimum improvement is `30 %`.

## Struggles and rejected approaches

The earlier uncentered sheet showed large A0 residuals and failed profile
gates. No image-derived profile was promoted from that result. The single
visible pen-up drag on the earlier sheet is retained as separate T-01H
evidence and was not used to excuse or alter the centered fit.

## Risks and follow-up

The standard gate-qualified decision is rejection. The project owner
subsequently selected this profile as the default by explicit override; see
`WSW-20261029-007`. Re-analyze the verification residual only if a principled
refinement can be justified without fitting the verification sheet as a
replacement profile. Revisit the outer annulus and intermittent pen-clear
behavior before expanding coverage.

## Files

- `samples/gcode/bed-error-map-dense-91-v3-centered-*`: source photo,
  diagnostics, overlays, and three threshold measurements.
- `samples/gcode/bed-error-compensation-2026-10-29-dense-v3-candidate.json`:
  gate-passing candidate profile.
- `samples/gcode/bed-error-analysis-dense-91-v3-centered.json`: complete fit
  report.
- `samples/gcode/bed-error-verify-dense-91-v3-centered.gcode` and `.csv`:
  operator-confirmed fresh-sheet verification.
- `samples/gcode/bed-error-verify-dense-91-v3-centered-auto.gcode` and `.csv`:
  one-start verification with five-second automatic pass dwells.
- `samples/gcode/bed-error-verify-dense-91-v3-centered-auto-photo.jpg`,
  diagnostics, threshold measurements, and comparison JSON: independent
  physical result.
- `docs/report/lab-notes/2026-10-29-m-12-dense-v3-centered-calibration.md`:
  detailed bench and extraction record.
- `docs/report/lab-notes/2026-10-29-m-12-dense-v3-centered-compensated-verification.md`:
  independent verification and rejection evidence.
