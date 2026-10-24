# Lab Note: 2026-10-23 - M-12 compensated verification pass

## Objective

Verify that corrected bed-compensation profile `2cdf3731de4a` reduces the
repeatable full-field X/Y error without introducing a worse angle response.

## Configuration

- Hardware revisions: RP23CNC `RP23U5XBB` V1.01; installed production X/Y/A
  mechanics and toolhead.
- Wiring/pin map: unchanged.
- Firmware commit/build: installed production controller build; no firmware
  changed for this run.
- grblHAL settings: not captured in the supplied message; not changed for this
  analysis.
- Registration and test program: fresh `G65 P113`, followed by
  `samples\gcode\bed-error-verify.gcode`. The program header identifies profile
  fingerprint `2cdf3731de4a`. The operator identified this as the latest
  verification print; the photo itself cannot independently prove which file
  was streamed.
- Converter settings/sample: compensated verification sheet generated from the
  corrected profile; one pen throughout, with the four normal drying `M0`
  pauses.
- Baseline: `samples\gcode\bed-error-map-2026-10-23.csv`, measured from the
  original uncompensated sheet.
- Bed mesh: `samples\gcode\bed-mesh-2026-10-11.csv`, SHA-256
  `e99cd98458e3521676493815102b1576fba3448926dd7b67dc20b42682a0bb16`.
- Photo:
  `docs/report/lab-notes/assets/2026-10-23-m-12-compensated-verification-pass.jpg`,
  2612 x 1967 px, SHA-256
  `98ecf959dc20f9d7c71d2886ac1749f1850b5eaaa760b3064c35a8f4f1c06e7e`.
- Instruments: overhead phone photo and software extraction of the printed
  marker vertices. No independent caliper measurement was used.

## Code, commands, and configuration used

```text
G65 P113
(load samples\gcode\bed-error-verify.gcode, fingerprint 2cdf3731de4a)
(Cycle Start; continue through four drying M0 pauses)
```

```powershell
py tools\measure_bed_error_photo.py C:\Users\jacks\Downloads\cal.jpg `
  --seed-diagnostic samples\gcode\bed-error-map-2026-10-23-photo.json `
  --maximum-assignment-px 20 `
  --measurement-out samples\gcode\bed-error-verify-pass-2026-10-23.csv `
  --diagnostic-out samples\gcode\bed-error-verify-pass-photo-2026-10-23.json `
  --overlay-out docs\report\lab-notes\assets\2026-10-23-m-12-compensated-verification-pass-overlay.png

py tools\analyze_bed_error_calibration.py `
  --measurements samples\gcode\bed-error-verify-pass-2026-10-23.csv `
  --compare-to samples\gcode\bed-error-map-2026-10-23.csv `
  --report-out samples\gcode\bed-error-verify-pass-analysis-2026-10-23.json
```

The repository's `python` command currently resolves to the Windows
app-execution stub and exits without running either script. `py` invokes the
available Python 3.13.13 interpreter and is the exact launcher used above.

## Procedure

1. Prepare the fresh round sheet and secure it before registration. Do not
   change its mounting after the first mark.
2. Run `G65 P113`, then stream the compensated verification program and allow
   each of the four `M0` passes to dry.
3. Photograph the complete stationary sheet with all four pose fiducials
   visible.
4. Use the previous sheet's photo diagnostic to constrain expected local
   geometry while extracting 185 station L corners.
5. Compare the independently normalized verification measurements with the
   original uncompensated sheet using the M-12 acceptance gates.

## Results

The sheet was complete and stationary. Seed-assisted extraction found four
fiducials and 235 L-like candidate components, from which all 185 expected
stations were assigned uniquely. Expected-to-detected assignment distance was
`0.020 px` minimum, `1.949 px` median, and `4.935 px` maximum. The overlay
places every measured marker on its printed L corner without an ambiguous
assignment.

Threshold sensitivity:

| Threshold | L candidates | Maximum assignment px | Verification RMS mm | Verification maximum mm | Improvement |
|---:|---:|---:|---:|---:|---:|
| 18 | 235 | 4.935 | 0.338 | 0.754 | 41.9 % |
| 20 (reported run) | 235 | 4.935 | 0.338 | 0.752 | 41.9 % |
| 22 | 234 | 4.549 | 0.337 | 0.762 | 42.0 % |

Before/after station fields:

| Stage | Before RMS mm | Before maximum mm | After RMS mm | After maximum mm |
|---|---:|---:|---:|---:|
| A=0 reference | 0.292 | 0.537 | 0.319 | 0.600 |
| 90 degrees | 0.765 | 1.208 | 0.278 | 0.538 |
| 180 degrees | 0.793 | 1.309 | 0.389 | 0.633 |
| 270 degrees | 0.535 | 1.004 | 0.353 | 0.752 |
| A=0 control | 0.324 | 0.722 | 0.339 | 0.647 |
| Overall | 0.581 | 1.309 | 0.338 | 0.752 |

The overall RMS improvement is `41.9 %`. Every formal M-12 verification gate
passes:

- RMS is at most `0.35 mm`.
- Maximum error is at most `0.90 mm`.
- Improvement is at least `30 %`.
- No 90/180/270 stage is worse by more than `0.05 mm`.

The A=0 reference and control increased by about `0.02 mm` RMS. That is inside
the stage tolerance and is the expected tradeoff from a map fitted across all
angles. The remaining worst point is station 09 at A=270, where the residual is
`0.752 mm` in X; it was `0.220 mm` before compensation. Stations 09 and 14 at
A=270 and station 09 at the A=0 control form the small set of locally worse
points.

## Difficulties and corrective actions

- The default non-seeded extractor found `2` fiducials, `207` L-like
  components, and `20` label glyphs because the photo's surrounding machine
  details and local fragments do not satisfy its strict global component-count
  contract. Seeded extraction from the original sheet supplied the expected
  geometry, assigned the exact 185-station layout, and produced the retained
  overlay and measurement CSV.
- Mark-center extraction at thresholds 18, 20, and 22 agrees to `0.001 mm` in
  RMS and `0.010 mm` in maximum error, so the pass is not a threshold artifact.
- The documented `python` command is not usable in this environment because it
  resolves to the Windows Store stub and returns success without starting the
  script. The equivalent commands ran successfully through `py`.
- Compensation removes most angle-dependent error but does not remove the
  localized residual at station 09/14, A=270. Refitting the profile from this
  verification sheet would make the validation circular and risk overfitting;
  no new profile was generated from this sheet.

## Interpretation

Profile `2cdf3731de4a` passes the documented independent verification for this
machine configuration. The correction is effective where the original error
was largest: 90/180/270 RMS fell by `64 %`, `51 %`, and `34 %` respectively.
The accepted profile therefore improves rotating-bed placement across the
measured field rather than merely reproducing the A=0 reference.

This is a lateral correction, not evidence that the bed surface is flat. The
remaining approximately `0.34 mm` RMS and `0.75 mm` maximum include physical
bed-plane, paper, carriage, and repeatability effects that the optional
planner map does not measure directly. The existing bed mesh has mixed
height correlations and cannot separate those causes.

## Decisions and next action

- Accept `2cdf3731de4a` as the verified compensation profile for the current
  bed, carriage, toolhead, pen mounting, paper support, and P100 registration.
- Keep P100 centre and A-index constants unchanged.
- Do not tighten this profile further from the same sheet. The documented
  acceptance gate is met, and fitting the verification sheet again would turn
  independent verification into training data.
- Re-run the full calibration after any bed, paper mounting, toolhead,
  carriage, pen-clamp, or registration change. If artwork requires materially
  less than the remaining `0.34 mm` RMS, diagnose bed plane/runout and
  carriage coupling as a separate mechanical task rather than adding another
  software correction layer.
