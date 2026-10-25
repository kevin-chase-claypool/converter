---
id: WSW-20261025-002
date: 2026-10-25
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_wave_coupon.py
  - tools/make_cmyk_wave_coupon.py
  - samples/gcode/cmyk-wave-coupon.gcode
  - samples/gcode/cmyk-wave-pitch-coupon.gcode
tags:
  - cmyk
  - wave-screen
  - depth
  - dot-pitch
  - clearance
  - manifest
related:
  - WSW-20261024-013
  - WSW-20261024-014
  - 2026-10-25-m-13-independent-wave-depth
---

# Make zero-anchored CMYK wave depth pitch-independent

## Summary

The zero-anchored CMYK screen now gives every row its own tone-driven phase
and amplitude while preserving stroke order and a physical pen envelope. The
same implementation is tested at `2.80`, `3.36`, and `4.20 mm` effective pitch
at all four CMYK screen angles. Artwork-save manifests now preserve the exact
recipe, source hash, compensation profile, and output hashes.

## Reason

The latest full yellow Ben1 print still looked monotonous. The selected
zero-anchored implementation had replaced independent row phase with one
common carrier and a small texture term. On the real image this made all rows
wander at the same rate even though scene depth differed. A deterministic
regression measured exactly `100`, `83`, and `66` zero crossings for both
light and dark rows at `2.80`, `3.36`, and `4.20 mm` respectively, proving the
failure was independent of pitch.

The black coupon had exercised only `3.36 mm`, and the failed yellow set used
the separate effective pitch of `2.80 mm` (`1.00 mm x 280 %`). The generator
therefore needed a pitch-scaled invariant, not another coupon-specific
adjustment. The earlier missing recipe metadata also made that distinction
hard to recover from the saved set.

## Implementation

- Each zero-anchored row resets phase at its zero point, then accumulates its
  own amplitude and phase rate from the seven-row-smoothed scene-luminance
  field.
- A monotone projection keeps visible row centrelines in baseline order with
  at least `75 %` of pitch separation at every sample column. It shifts only
  rows that would otherwise converge; it does not fade every row toward one
  shared waveform.
- A slope-aware bound scales amplitude from the effective pitch, required
  pen-plus-gap clearance, and maximum tone-driven slope. This makes the
  centerline distance invariant explicit at every pitch rather than relying on
  the production coupon's dimensions.
- The existing finite segment-to-segment check remains as the final guard.
  A physically impossible pitch below the pen-width-plus-edge-gap envelope
  now raises a clear planning error.
- Scene depth continues to come from luminance before saturation, contrast,
  brightness, and gamma, so ink controls can change coverage without flattening
  the wave-depth source.
- Artwork manifests advance to version 2 and record source file/hash, screen
  style, Dot pitch, Artwork scale, effective pitch, pen and tolerance, image
  controls, weights, bed-compensation path, offsets, preflight, and G-code
  hashes. Calibration-sheet manifests retain their existing schema.
- Regenerated both black coupons and the four Ben1 files with the new
  algorithm.

## Verification

- The new multi-pitch regression goes red on the previous common carrier:
  dark and light rows had identical crossing counts at every pitch. With
  independent row phase, dark rows now have at least `1.35x` the crossings of
  light rows at `2.80`, `3.36`, and `4.20 mm`.
- A second regression exercises all four screen angles at every one of those
  pitches, checks every adjacent finite segment pair against the `1.05 mm`
  centreline envelope, and confirms the sampled vertical gap never falls below
  `75 %` of pitch.
- On the real Ben1 yellow screen at `2.80 mm`, regular-column gaps measured
  `2.230-3.373 mm`; the row frequencies varied from short/flat runs to 255
  crossings across the long visible runs. The yellow layer took about
  9-14 seconds to screen including its exact segment-clearance pass.
- The regenerated yellow G-code contains `131,879` drawing moves and passes the
  strict motion guard: maximum bed step `6.33 deg`, peak A rate
  `268 motor deg/s`, no pen-up rotation, and `0.139 mm` worst bounded path bow.
  Its four over-tolerance counts are tolerated by the existing subdivision
  cap.
- All four regenerated Ben1 files pass strict motion checks. Cyan/Magenta/
  Yellow/Black maximum bed steps are `1.73/5.96/6.33/6.77 deg`; peak A rates
  are `264.6/268.6/268.4/267.8 motor deg/s`.
- The regenerated pitch coupon covers C15/M75/Y0/K45 at `2.80`, `3.36`, and
  `4.20 mm` in one rotating-bed program. It passes strict motion checks with
  a `5.71 deg` maximum bed step, `269 motor deg/s` peak A rate, no pen-up
  rotation, and `0.108 mm` worst bounded path bow.
- The full CMYK-tab suite passes `86` tests. The expanded coupon suite passes
  all `4` tests. Full converter discovery passes `532` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- Raising or lowering Dot pitch cannot repair a shared phase law; the
  regression failure was identical at every tested pitch.
- A global clearance search reduced all row amplitudes together and erased
  depth far from the actual conflict.
- Fully independent unbounded sine rows can cross, while exactly translated
  rows preserve spacing but cannot create independent frequency depth.
- Clamping only vertical spacing does not alone preserve a round-pen envelope
  on steep wave flanks; the slope term is required.

## Risks and follow-up

- No physical print yet validates the regenerated Ben1 set. Preview and run the
  single black multi-pitch coupon before spending another yellow layer or a
  14-inch round sheet.
- The guarantee applies to centreline geometry before pen spread and machine
  following error. The radial cartridges provide a `0.25 mm` nominal ink gap,
  but a physical pass must still inspect edge contact.
- Bed compensation remains enabled in every regenerated file under profile
  `4c8270de8a74`; it is deliberately not disabled as part of this fix.
- The converter must be restarted before using the updated core in the open Qt
  application.

## Files

- `software/converter_core/cmyk.py`: independent row phase, monotone clearance
  projection, slope-aware amplitude scaling, and scene-depth preservation.
- `software/generator_tabs/cmyk_tab.py`: version-2 recipe and hash manifest.
- `software/tests/test_cmyk_tab.py`: multi-pitch frequency, all-angle
  clearance, impossible-pitch, and manifest regressions.
- `software/tests/test_cmyk_wave_coupon.py`: single-run multi-pitch coupon
  coverage.
- `tools/make_cmyk_wave_coupon.py`: multi-pitch coupon mode and stronger
  per-row tonal diagnostic.
- `samples/gcode/cmyk-wave-coupon.gcode` and
  `samples/gcode/cmyk-wave-pitch-coupon.gcode`: regenerated black diagnostics.
- `software/README.md`: current wave, pitch, and manifest behavior.
- `docs/report/lab-notes/2026-10-25-m-13-independent-wave-depth.md`: failed
  print evidence, software measurements, and pending physical checks.
