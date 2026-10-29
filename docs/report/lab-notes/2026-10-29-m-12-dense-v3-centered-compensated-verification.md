# Lab Note: 2026-10-29 - Dense v3 centered compensated verification

## Objective

Verify whether candidate `18bfb4ed1c33` reduces the physical residual from the
centered dense-v3 calibration sheet enough to replace active profile
`4bad792e35ad`.

## Configuration

- Hardware: RP23CNC / `RP23U5XBB` V1.01 with the centered production pen.
- Verification program:
  `samples\gcode\bed-error-verify-dense-91-v3-centered-auto.gcode`,
  profile fingerprint `18bfb4ed1c33`, eight automatic five-second pass dwells.
- Program SHA-256:
  `E63BFBBE94FDD892D4D4632C4CCD1D29E6407AD43EA5F44CD5F6F91AEEE7A416`.
- Pen: Pigma Micron 005 for all nine passes.
- Photo: `samples\gcode\bed-error-verify-dense-91-v3-centered-auto-photo.jpg`,
  1658 x 2201 px, SHA-256
  `37CF51B926C271B400A90B026497FD7E24B0A44949D06DABFFE3143F8032BF8C`.

## Code, commands, and configuration used

```powershell
python tools\measure_bed_error_photo.py `
  samples\gcode\bed-error-verify-dense-91-v3-centered-auto-photo.jpg `
  --layout dense-91-v3 --threshold 55 --fiducial-threshold 25 `
  --blur-radius 6 `
  --seed-diagnostic samples\gcode\bed-error-map-dense-91-v3-centered-photo.json `
  --measurement-out samples\gcode\bed-error-verify-dense-91-v3-centered-auto-measured-t55.csv `
  --diagnostic-out samples\gcode\bed-error-verify-dense-91-v3-centered-auto-photo.json `
  --overlay-out samples\gcode\bed-error-verify-dense-91-v3-centered-auto-overlay-t55.jpg

python tools\analyze_bed_error_calibration.py `
  --measurements samples\gcode\bed-error-verify-dense-91-v3-centered-auto-measured-t55.csv `
  --compare-to samples\gcode\bed-error-map-dense-91-v3-centered-measured-t55.csv `
  --report-out samples\gcode\bed-error-verify-dense-91-v3-centered-auto-comparison.json
```

Extraction was repeated at thresholds 20 and 80 with the threshold-55
diagnostic as the seed.

## Procedure

1. Secure a fresh 14-inch sheet and run `G65 P113`.
2. Plot the centered compensated verification file in automatic five-second
   dwell mode.
3. Photograph the complete sheet from above.
4. Extract all four fiducials and 819 station marks.
5. Repeat extraction at thresholds 20/55/80 and require identical coordinates.
6. Compare the normalized station field against the centered uncompensated
   baseline.
7. Apply the M-12 RMS, maximum, improvement, and per-angle gates.

## Results

Thresholds 20, 55, and 80 produced identical station coordinate files.

Overall comparison:

| Metric | Centered baseline | Compensated verification | Gate |
|---|---:|---:|---:|
| RMS | `0.550 mm` | `0.486 mm` | `<= 0.35 mm` |
| Maximum | `1.163 mm` | `1.171 mm` | `<= 0.90 mm` |
| Improvement | — | `11.6 %` | `>= 30 %` |

Every angle-stage RMS improved, and no stage RMS was worse by more than
`0.05 mm`. Individual maxima increased slightly at several angles, including
A180 from `1.163` to `1.171 mm`.

Per-angle RMS results:

| Group | Baseline | Verification |
|---|---:|---:|
| A000 reference | `0.518 mm` | `0.453 mm` |
| A045 | `0.454 mm` | `0.445 mm` |
| A090 | `0.571 mm` | `0.521 mm` |
| A135 | `0.571 mm` | `0.543 mm` |
| A180 | `0.603 mm` | `0.536 mm` |
| A225 | `0.585 mm` | `0.532 mm` |
| A270 | `0.580 mm` | `0.456 mm` |
| A315 | `0.578 mm` | `0.458 mm` |
| A000 control | `0.469 mm` | `0.414 mm` |

## Difficulties and corrective actions

The candidate improves every angle-stage RMS but does not meet the required
overall RMS, maximum, or improvement margins. The result is consistent with a
real but insufficient correction rather than a gross registration or
extraction error.

No manual point edits were used. The verification was not refitted as a
replacement profile.

## Interpretation

Candidate `18bfb4ed1c33` does not pass the M-12 acceptance contract. It
reduces average error modestly, but leaves a `1.171 mm` maximum and only
achieves `11.6 %` improvement. The project owner nevertheless selected it as
the default after reviewing the result.

## Decisions and next action

- Record that candidate `18bfb4ed1c33` fails the formal promotion gates.
- The project owner explicitly overrode that gate decision and promoted the
  candidate; see `WSW-20261029-007`.
- Keep the centered baseline and verification data as evidence.
- Do not use another full sheet until the residual is re-analyzed for
  refinement opportunities or the remaining error is traced mechanically.

The comparison is recorded in
`samples\gcode\bed-error-verify-dense-91-v3-centered-auto-comparison.json`.
