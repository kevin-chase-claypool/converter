---
id: WSW-20261008-016
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - automation
  - screening
  - density
related:
  - WSW-20261008-014
  - WSW-20261008-015
---

# Auto renders the screen before it picks the tone

## Summary

Auto assumed the tone it asked for was the ink the plot lays down. The
rectilinear screen does not work that way: rows sit one pen width apart and
open up by up to 7x in light tones, so a light tone only inks about a fifth
of its area. The tab now passes Pen width and the effective pitch
(`Dot pitch x Artwork scale`) into `auto_photo_settings`, which converts each
candidate's tone into row coverage (`pen / row pitch`, cut off below the ink
floor), multiplies the four inks and scores the rendered luminance. The
screen-aware search also covers the darker half of the controls (brightness
60-180 %, gamma 0.6-1.6) because "more ink" is the only way to reach the
photo's tone on a sparse screen.

## Reason

Owner: "i ran auto again", with a pale preview at C 120 / B 100 / gamma 1.0 -
Auto's tone term had aimed the *tone* at the photo, but the screen rendered
that tone at roughly half the coverage, so the plot came out washed out.

## Implementation

- `software/converter_core/cmyk.py`: optional `pen_width_mm` and
  `effective_pitch_mm`; the screen branch renders tones through the
  rectilinear stretch, the ink floor, the display inks and the tab's tone
  grid. Saturation and GCR are computed before the search so the render uses
  them.
- `software/generator_tabs/cmyk_tab.py`: the Auto button passes the current
  Pen width and effective pitch.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 402 tests
  pass, 1 skipped (the pre-existing headless shader compile).
- Owner's portrait at 0.30 mm pen / 0.31 mm rows: C 270 / B 100 / gamma 0.60
  (was C 120 / B 100 / 1.0). Wisteria: C 240 / B 60 / gamma 1.0.
- New test: a sparse screen (0.31 mm rows) returns a darker chain than the
  tone-only model, and a screen finer than the pen (0.10 mm) returns a
  lighter one.

## Struggles and rejected approaches

- Keeping the tone-only search and just adding the darker grid points was
  rejected: without the screen model the search already matched the photo's
  tone and would not have moved.
- A full colour fit was again measured and rejected - the ink model adds
  contrast, so a least-|print - photo| fit collapses to the lowest-ink
  corner.

## Risks and follow-up

- Plots will ask for much more ink on sparse screens: expect longer runs and
  more pooling. Judge the first one on paper before batch printing.
- The screen model uses the display ink colours, not a loaded calibration
  profile.

## Files

- `software/converter_core/cmyk.py`: screen model in the Auto search.
- `software/generator_tabs/cmyk_tab.py`: tab feeds pen width and effective
  pitch.
- `software/tests/test_cmyk_tab.py`: sparse-vs-fine screen test, tab Auto
  expectation.
- `software/README.md`: Auto description.
