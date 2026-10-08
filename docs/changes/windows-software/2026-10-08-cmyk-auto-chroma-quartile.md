---
id: WSW-20261008-011
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
  - color-separation
related:
  - WSW-20261008-010
  - WSW-20261008-006
---

# Auto reads the colourful quartile for saturation and GCR

## Summary

Auto (photo) measured average chroma, which a vivid subject over neutral
ground (blossoms over dirt and branches, for example) drags down - so it
kept GCR at 95 and let black swallow the colour. It now uses the 75th
percentile of per-pixel chroma: saturation is
`clamp(110 + (0.35 - p75) * 80, 110, 145)` and GCR is
`clamp(90 - max(0, p75 - 0.20) * 120, 60, 95)`. Vivid photos therefore keep
more chroma in C/M/Y with less K, while muted ones still get the extra
saturation and heavier black.

## Reason

Owner's wisteria photo: the Auto result (S 110, GCR 95) rendered washed
out against the strongly purple/green source. The mean-chroma statistic saw
mostly neutral branches and dirt.

## Implementation

- `software/converter_core/cmyk.py`: `chroma_p75` drives the saturation and
  GCR rules in `auto_photo_settings`.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 398
  tests (1 skipped: the pre-existing headless shader compile). New test:
  vivid purple/green stripes get a lower GCR and a lower (but >= 110 %)
  saturation than a neutral gray image.
- Checked against the owner's actual photo: Auto now returns saturation
  120 % / GCR 85 % (previously 110 / 95).
- `python tools\docs_index.py --check` passes.

## Struggles and rejected approaches

- Mean chroma was kept for muted-image detection in an earlier version;
  the quartile covers both ends without a second statistic.

## Risks and follow-up

- GCR can now go as low as 60 % for very colourful images, which keeps more
  ink in C/M/Y and less in K; the measured calibration profile remains the
  way to match the pens exactly.

## Files

- `software/converter_core/cmyk.py`: chroma quartile rules.
- `software/tests/test_cmyk_tab.py`: vivid-vs-gray test.
- `software/README.md`: Auto description.
