---
id: WSW-20261025-003
date: 2026-10-25
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_wave_coupon.py
  - samples/gcode/cmyk-wave-coupon.gcode
  - samples/gcode/cmyk-wave-pitch-coupon.gcode
tags:
  - cmyk
  - wave-screen
  - depth
  - amplitude
  - clearance
  - dot-pitch
related:
  - WSW-20261025-002
  - 2026-10-25-m-13-independent-wave-depth
---

# Use local amplitude budgets for CMYK wave depth

## Summary

Zero-anchored CMYK waves now calculate a separate amplitude budget for each
row instead of scaling the whole image to its steepest sample. The budget
ignores depth changes across blank paper, and exact `75 %` pitch boundaries no
longer fail on floating-point noise. The result recovers visible wave height
while retaining the tested pen-clearance guarantee.

## Reason

The `11:01` regenerated Ben1 set proved that the new converter was active, but
the preview became shallow and dense rather than gaining depth. The row phase
was independent, yet the amplitude safety pass still used one global
`max_tone_step`; one steep inked patch or an irrelevant jump across blank paper
could reduce every row.

Two minimized tests reproduced the failures:

- A `12 x 4 px` hard-tone patch reduced untouched-row travel from `1.187` to
  `0.741`.
- A large depth change confined to the blank half of a fixture reduced visible
  row travel from `1.715` to `0.565`.

The real Ben1 screen then exposed a third numerical defect: the row-order
projection produced an exact `0.75 mm` floor as
`0.7499999999999929`. The strict comparison treated that as a clearance
failure and invoked the global damp-to-safe fallback even though the nearest
actual segment pair was `1.53 mm` on paper.

## Implementation

- `WAVE_FREQUENCY_TONE_GAIN` is reduced from `2.0` to `1.0`. Dark rows still
  wind faster than light rows, but no longer consume an extreme fraction of
  the physical slope budget.
- Each row calculates its own maximum active tone, maximum active tone change,
  phase slope, and safe amplitude factor.
- Tone changes are included only where two adjacent samples both carry ink.
  A gap, image boundary, or changing depth over blank paper cannot limit an
  emitted segment.
- The global depth-scale fallback remains available only if the physical
  segment check genuinely fails. It is no longer activated by an exact band
  floor, because the band comparison now has the same `1e-9` numerical
  tolerance as the segment check.
- Regenerated both black coupons and all four Ben1 files.

## Verification

- Both minimized regressions now pass: untouched rows retain their amplitude,
  and blank-paper depth changes no longer affect inked rows.
- The zero-anchored exact-floor regression passes at the nominal `75 %`
  boundary.
- Existing multi-pitch, all-angle, monotonic-band, finite-segment, path
  tolerance, independent-frequency, and impossible-pitch regressions pass.
- Real Ben1 yellow at effective `2.80 mm` now has `1.142 mm` median and
  `1.354 mm` maximum peak-to-peak wave height. The previous 11:01 build was
  about `0.65 mm` median. The first clearance attempt passes with no global
  scale reduction.
- All four real Ben1 screen angles pass on their first clearance attempt:

  | Ink | Marks | Source points | Clearance attempts |
  |---|---:|---:|---|
  | C15 | 1,840 | 151,770 | 1, pass |
  | M75 | 1,859 | 205,174 | 1, pass |
  | Y0 | 1,115 | 240,407 | 1, pass |
  | K45 | 1,792 | 222,106 | 1, pass |

- Regenerated yellow G-code SHA-256 is
  `216152cd5eae26206fa76cc092f109e481d4562664b056c9d6f51258ce943766`.
  It contains `88,467` drawing moves and passes the strict motion guard with a
  `5.26 deg` maximum bed step, `269 motor deg/s` peak A rate, no pen-up
  rotation, and three subdivision-cap exceptions.
- All four Ben1 files pass strict motion and travel-window checks. Bed
  compensation `4c8270de8a74` remains in every header and manifest.
- Regenerated coupon hashes:
  - `cmyk-wave-coupon.gcode`:
    `7F63FE63D8DF5AEE69A08A566825B814DF94DCC130B2B48E4CB63B83D4D6AE51`
  - `cmyk-wave-pitch-coupon.gcode`:
    `F7BF0DD6B56BFA306192591C88B6782D305747A8FC2A4A38C16C87BFCEC4DB44`
- Full converter discovery passes `535` tests with one expected OpenGL-context
  skip.
- The user then saved the same recipe from the restarted application at
  `11:33:14`. Its yellow SVG hash matches the local-budget generation exactly;
  the G-code SHA-256 is
  `EFD6150609F31D3EA09175B62D00E0B8DBDA5808443883E666EC3DF5D3BAAFB1`
  with `94,601` drawing moves. It passes strict motion at `5.36 deg` maximum
  bed step, `268.8 motor deg/s` peak A rate, no pen-up rotation, and
  `0.096 mm` worst bounded path bow. All four application-saved files remain
  inside the travel window.

## Struggles and rejected approaches

- Keeping one global slope budget preserved clearance but made every row as
  shallow as the most restrictive patch.
- Increasing frequency gain recovered low/high rhythm but reduced physical
  wave height further.
- Counting depth transitions across blank paper protected a segment that did
  not exist.
- Strict comparison of an exact projected floor caused a false global fallback
  on real floating-point output.

## Risks and follow-up

- The regenerated set has passed software geometry and motion checks, but no
  physical yellow print has yet accepted the new depth.
- Restart the converter so it loads this revision, inspect the yellow preview,
  and run the ordinary-paper multi-pitch black coupon before using another
  yellow pen or 14-inch sheet.
- The physical acceptance remains no adjacent ink contact and clearly visible
  mixed wave depth in all three pitch bands.

## Files

- `software/converter_core/cmyk.py`: row-wide active-segment amplitude budgets,
  lower frequency gain, and tolerant band-floor comparison.
- `software/tests/test_cmyk_tab.py`: two red-first local-budget regressions and
  exact-boundary coverage.
- `software/tests/test_cmyk_wave_coupon.py`: regenerated coupon motion and
  pitch-matrix checks.
- `samples/gcode/cmyk-wave-coupon.gcode` and
  `samples/gcode/cmyk-wave-pitch-coupon.gcode`: current black diagnostics.
- `software/README.md`: current zero-anchored wave behavior.
- `docs/report/lab-notes/2026-10-25-m-13-independent-wave-depth.md`: failed
  11:01 evidence and local-budget comparison.
