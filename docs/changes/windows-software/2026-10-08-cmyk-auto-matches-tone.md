---
id: WSW-20261008-014
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - automation
  - tone
  - portraits
related:
  - WSW-20261008-010
  - WSW-20261008-011
---

# Auto matches the printed tone to the photo

## Summary

`auto_photo_settings` scored the tone chain on detail energy alone, so on a
bright low-contrast portrait it chose brightness 140 / contrast 180 and the
print came out a stop lighter than the photo (mean paper luminance 0.511
against 0.434) - which is exactly where skin washes out and reads pink. The
score now subtracts the printed tone error as well: the search aims the
print's mean tone at the photo's, clamped to the 0.30-0.75 window a plot can
hold (below it the sheet is a muddy ink stack, above it is mostly paper).
Dark photos therefore keep the deliberate lift that keeps their structure
visible.

## Reason

Owner: "auto just looks so bad on skin tones", with the Auto result
(S 125 / C 180 / B 140 / GCR 90 / gamma 1.0) on `momandbennett.jpg`.
Measured through the real chain plus the multiply ink model: the chosen
settings print at 0.511 mean paper luminance against the photo's 0.434, and
the predicted skin is lighter and pinker than the photo's.

## Implementation

- `software/converter_core/cmyk.py`: `photo_tone = clamp(stretched.mean(),
  0.30, 0.75)`; the search score is
  `_detail_score(printed) - abs(printed.mean() - photo_tone)`.
- On the owner's portrait Auto now returns brightness 100 / contrast 120
  (printed 0.432 against 0.434); the wisteria photo is unchanged
  (printed 0.517 against 0.513).

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 400 tests
  pass, 1 skipped (the pre-existing headless shader compile).
- New regression test: on a bright low-contrast field, where the detail-only
  search picked brightness 120 and printed 0.044 lighter than the photo, the
  chosen settings now come within 0.03 of the photo's tone.
- The dark/bright test keeps its lift requirement (brightness 180); its
  gamma expectation moves 1.5 -> 1.4 because the window clamp trades a
  little of the lift away.

## Struggles and rejected approaches

- A full colour fit (choose the settings that minimise mean
  `|print - photo|`) was measured and rejected: the ink model adds contrast,
  so the minimum is the same lowest-ink corner (brightness 100, contrast
  120, saturation 100) for every image, which flattens the print.
- Matching the printed mean with no clamp (weight 1.0 everywhere) dropped a
  dark test photo's detail score from 0.126 to 0.020, which is why the
  printable window exists.

## Risks and follow-up

- Auto still fits the built-in display inks; the measured calibration profile
  remains the exact-match step.
- Skin keeps the muted-image saturation boost (up to 145 %). If skin reads
  too pink, drop Saturation 10-15 points after Auto.

## Files

- `software/converter_core/cmyk.py`: tone term in the Auto search.
- `software/tests/test_cmyk_tab.py`: tone-match regression test; dark/bright
  expectation.
- `software/README.md`: Auto description.
