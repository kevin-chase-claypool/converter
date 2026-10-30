---
id: WSW-20261030-001
date: 2026-10-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - auto-photo
  - wave-screen
  - image-fidelity
  - exposure
  - color
related:
  - WSW-20261024-013
  - WSW-20261026-001
  - WSW-20261029-008
---

# Preserve photo fidelity in Wave-screen Auto

## Summary

**Auto (photo)** now uses a separate exposure-preserving setup for the
equidistant Wave screen. On the loaded sunset photograph it changes the old
selection from `240 %` contrast, `60 %` brightness, `0.60` gamma, `115 %`
saturation, and `85 %` GCR to `120 %`, `150 %`, `1.40`, `100 %`, and `35 %`
respectively. It also widens the exact row pitch from `0.80` to `1.20 mm`
before artwork scale and applies a milder `100 %` unsharp mask at `1.5 mm`.

## Reason

The existing auto search optimized grayscale gradient energy using a
tone-varying line-pitch model. The Wave screen does not vary row pitch with
tone; it places a binary ink mask on fixed-pitch wave rows. Applying the
line-screen search therefore pushed normal photographs toward maximum contrast
and dense ink. On the loaded landscape it lost the blue sky and turned broad
regions into dense red, purple, and black texture.

## Implementation

- Add an optional `style` argument to `auto_photo_settings`.
- For `waves`, `waves_even`, and `waves_zero`, choose controls from source
  luminance percentiles, tonal span, and the 90th-percentile chroma.
- Keep auto levels enabled, but regularize contrast, brightness, gamma,
  saturation, and GCR around preservation of the photograph's normal exposure.
- Recommend at least `3.4` pen widths between row centre lines for the Wave
  screen. This reduces the full-ink duty cycle and preserves separated color
  detail in dark foliage, without disturbing equidistance.
- Return a moderate sharpening preset with the wave-specific controls and apply
  it from the CMYK tab.
- Leave non-wave styles on the existing detail/screen-aware search.

## Verification

- On the loaded image
  `PXL_20241218_215026972~2.jpg` (SHA-256
  `0DB593F75E18601BC140EF2625B7266D2AAD6540E8E0675708606063A9E82A77`),
  the new settings are saturation `100 %`, contrast `120 %`, brightness
  `150 %`, GCR `35 %`, gamma `1.40`, dot pitch `1.20 mm` pre-scale
  (`2.76 mm` on paper), and sharpen `100 %` at `1.5 mm`.
- Manual converter previews compared the old extreme settings against the new
  balanced settings. The new preview retained the blue sky region, separated
  the warm cloud highlights, and kept the dark foreground without the old
  all-over dense tint.
- Focused CMYK tests pass: `95` tests.
- Full converter discovery passes `578` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

Pushing brightness and ink gamma to their upper limits made the preview whiter,
but erased too much of the sky and foreground. Lowering GCR without correcting
the tone controls preserved more color but remained too dense. The accepted
result balances exposure and chroma rather than minimizing a single luminance
error.

## Risks and follow-up

Wave-screen tone is still binary at each sampled row coordinate, so a physical
print cannot reproduce continuous-tone photography as accurately as the
halftone or stipple styles. Auto now preserves the source better, but a future
tone-modulated wave mask would be required for true continuous photographic
density. A physical comparison on the loaded image remains pending.

## Files

- `software/converter_core/cmyk.py`: wave-specific photo Auto analysis.
- `software/generator_tabs/cmyk_tab.py`: pass the screen style and apply Auto's
  sharpening controls.
- `software/tests/test_cmyk_tab.py`: normal-exposure and UI application tests.
- `software/README.md`: current Auto behavior.
