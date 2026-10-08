---
id: WSW-20261008-018
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/converter_core/cmyk.py
tags:
  - cmyk
  - controls
  - gcr
  - brightness
related:
  - WSW-20261008-016
---

# Brightness reaches 20 % and GCR tops out at 100 %

## Summary

The Brightness control stopped at 50 %, which the owner hit while trying to
push ink into a bright portrait; it now reaches 20 % (the pipeline accepts
any value above 1 %, so only the spinner bound was tight). The Black (GCR)
spinner allowed up to 150 %, but the separation is only valid to 100 %:
`k = min(c, m, y) x gcr` is clipped at full coverage above that, and the
C/M/Y terms go negative before they are clipped, so the conversion stops
being monotone and the layer loses its lightest ink - the "breaks" the owner
saw near 100 %. The spinner now tops out at 100 %, and `rgb_to_cmyk_tone`
clamps `gcr` to 0..1 so an old saved 150 % behaves like 100 % instead of
misbehaving.

## Reason

Owner: "i am only able to drop the brightness to 50 % and i cant get any
lower. also, the gcr value seems to have made a huge difference setting it to
99 %. when i set it to 100 % it seems like it breaks though".

## Implementation

- `software/generator_tabs/cmyk_tab.py`: Brightness range 50-200 -> 20-200;
  Black (GCR) range 0-150 -> 0-100.
- `software/converter_core/cmyk.py`: the grey component takes
  `min(1, max(0, gcr))`.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 403 tests
  pass, 1 skipped (the pre-existing headless shader compile).
- Measured on the owner's photo: GCR 95 % -> K mean 0.421, C mean 0.166;
  99 % -> K 0.438, C 0.129; 100 % -> K 0.443, C 0.119, no NaNs or negative
  coverages in any case.

## Struggles and rejected approaches

- Leaving the 150 % range and only documenting it was rejected: the
  conversion was mathematically degenerate there, so the limit belongs in
  both the control and the maths.

## Risks and follow-up

- At exactly 100 % the ink with the least coverage in a pixel (cyan on warm
  skin) reaches zero, so those areas are drawn by K, M and Y alone. 95-99 %
  keeps a little of it; density is better raised with brightness, contrast or
  gamma.

## Files

- `software/generator_tabs/cmyk_tab.py`: control ranges.
- `software/converter_core/cmyk.py`: grey-component clamp.
