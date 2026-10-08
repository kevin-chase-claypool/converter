---
id: WSW-20261008-006
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
  - user-interface
  - defaults
  - automation
related:
  - WSW-20261008-005
  - WSW-20261008-001
---

# Add an Auto (photo) button to the CMYK image options

## Summary

Image options gains an **Auto (photo)** button. It analyzes the loaded
artwork at a small resolution and fits the image-side controls so the ink
simulation starts close to the photo: auto levels on, brightness 100-180 %
(from the median luminance, so it only ever lifts dark images), contrast
120-285 % (from the inter-quartile tonal spread - flatter images get more),
saturation 100-140 % and GCR 70-95 % (from the mean chroma, so vivid photos
keep more colour), and a starting gamma 1.0-1.6 (from the median again,
left as the print-lightness dial to tweak). The status line reports the
values it chose, and every control stays manually editable.

## Reason

Owner: "is there a way we can add an 'auto' button to set it up as close to
a good representation of the photo as possible? im just having a hard time
between photos and it would be easier if all i had to manipulate after
'auto' was gamma." Nothing is removed; Auto is a starting point.

## Implementation

- `software/converter_core/cmyk.py`: `auto_photo_settings(image_path)` -
  downscale to 256 px, luminance percentiles (p25/p50/p75), mean chroma,
  and the clamped formulas above.
- `software/generator_tabs/cmyk_tab.py`: the Auto button at the top of
  Image options; `apply_auto_settings` sets the six controls and reports
  the chosen values in the status line.
- `software/README.md`: control-list note.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 392
  tests (1 skipped: the pre-existing headless shader compile). New tests: a
  dark synthetic image gets gamma >= 1.3 and brightness >= 140 while a
  bright one stays at gamma 1.0 / brightness 100; clicking the button
  applies exactly the analyzer's values and writes the status line.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Predicting gamma exactly was rejected: gamma is the owner's single
  manual dial, so Auto only gives it a sensible start.
- Setting the Screen or Page controls was rejected: style, pitch, scale,
  and resolution stay workflow choices.

## Risks and follow-up

- The heuristics are deliberately conservative (brightness never darkens,
  saturation never lowers); unusual images may still want manual nudges.

## Files

- `software/converter_core/cmyk.py`: `auto_photo_settings`.
- `software/generator_tabs/cmyk_tab.py`: Auto button and handler.
- `software/tests/test_cmyk_tab.py`: analyzer and button coverage.
- `software/README.md`: documentation.
