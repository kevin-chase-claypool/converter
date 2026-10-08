---
id: WSW-20261008-010
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
  - tone
  - defaults
related:
  - WSW-20261008-006
  - WSW-20261008-005
---

# Auto (photo) now searches for detail legibility

## Summary

`auto_photo_settings` no longer uses fixed median/spread formulas. It walks
the exact tone chain the pipeline applies - auto levels (1-99 % stretch),
soft contrast, brightness, ink gamma - over a 7 x 5 x 7 grid (245
combinations) and scores each on the downscaled luminance with mid
tone-weighted gradient energy (`4p(1-p)`) minus a 0.4 x clipping penalty,
picking the combination that keeps the most structure in the visible mid
tones. Saturation and GCR keep the mean-chroma rules; auto levels stays on.
The contrast curve was factored into `_soft_contrast`, shared by the
pipeline and the search, so the optimizer scores exactly what the plot will
do. The Auto status line now also reports an effective-pitch advisory
(pitch x scale versus pen width: below 0.6x "raise for detail", above 2.5x
"lower for density", else "good balance").

## Reason

Owner: "improve the automatic image-to-setting pipeline. i want to get the
preview as close to the image as possible, right now details in the preview
are very hard to make out." The old formulas only saw the median and IQR;
they could not tell whether the chosen curve actually kept detail visible.

## Implementation

- `software/converter_core/cmyk.py`: `_soft_contrast` (moved from
  `prepare_image_tones`, behaviour unchanged) and `_detail_score`;
  `auto_photo_settings` grid search returning the best contrast,
  brightness, and gamma.
- `software/generator_tabs/cmyk_tab.py`: the Auto status message appends
  the effective-pitch advisory.
- `software/README.md`: Auto description.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 397
  tests (1 skipped: the pre-existing headless shader compile).
- Deterministic picks on synthetic textures: a night-like dark field
  (brightness 180, contrast 120, gamma 1.6), a mid-key texture (contrast
  240), a bright field (brightness 120, gamma 1.0). The same image always
  returns the same settings; one analysis takes about 0.04 s.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- The first run passed control percentages straight into the curve factor
  (contrast 120 read as 120x) and every image picked the first grid point;
  the search now divides by 100 like the tab does.
- Flat synthetic test images were rejected as test material: with no
  gradients every score ties and the first grid point wins by design.

## Risks and follow-up

- The metric optimises legibility, not punch: Auto may choose less contrast
  than a hand-tuned look. Raising Contrast after Auto is safe under the
  soft curve.

## Files

- `software/converter_core/cmyk.py`: shared contrast curve, detail score,
  grid search.
- `software/generator_tabs/cmyk_tab.py`: pitch advisory in the Auto report.
- `software/tests/test_cmyk_tab.py`: dark/bright/mid behaviour tests.
- `software/README.md`: documentation.
