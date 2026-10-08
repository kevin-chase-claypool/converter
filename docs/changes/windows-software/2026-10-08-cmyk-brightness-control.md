---
id: WSW-20261008-003
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
  - tone
  - brightness
  - defaults
related:
  - WSW-20261008-001
  - WSW-20261008-002
---

# Add a brightness lift and restore contrast to 200 %

## Summary

The Image options gain a **Brightness** control (50-200 %, default 130 %):
a gamma curve (`rgb ** (100 / brightness)`) applied after auto levels,
saturation, and contrast, which brightens shadows and mid tones while
keeping the black and white points - no clipping, no washed-out paper. The
**Contrast** default moves back to 200 %, which is safe again with the soft
S-curve from `WSW-20261008-001`; the two together give the punchy but open
rendition the owner was after.

## Reason

Owner, after the rectilinear light-stretch fix: "yes the brighness is too
low" and "maybe contrast too low as well." The night photo's plot was
correctly dark for paper but too dark against a backlit screen.

## Implementation

- `software/converter_core/cmyk.py`: `prepare_image_tones(..., brightness=
  100.0)`; for values other than 100 the image is lifted by
  `rgb ** (100 / max(1, brightness))` just before the CMYK separation.
- `software/generator_tabs/cmyk_tab.py`: the Brightness spin box after
  Contrast (default 130), passed through `_build_artwork_layers` and added
  to the layer cache key; contrast default 110 -> 200.
- `software/README.md`: control list and shipped-defaults sentence/row.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 389
  tests (1 skipped: the pre-existing headless shader compile). New test: a
  30 % gray image at brightness 130 lays at least 0.05 less mean K ink than
  at 100 %, with the black point preserved; the shipped-defaults test
  asserts brightness 130 and contrast 200.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Reusing Ink gamma for brightness was rejected: it scales ink coverage
  rather than the image, so it shifts the separation instead of the tone.
- A linear gain was rejected: it clips highlights and lifts the black
  point; the gamma lift keeps both ends fixed.

## Risks and follow-up

- Brightness stacks with auto levels and contrast; very high values lighten
  shadows toward paper. The measured calibration profile is still the final
  colour-match step.

## Files

- `software/converter_core/cmyk.py`: brightness lift.
- `software/generator_tabs/cmyk_tab.py`: control, cache key, call site.
- `software/tests/test_cmyk_tab.py`: lift regression test and defaults.
- `software/README.md`: documentation.
