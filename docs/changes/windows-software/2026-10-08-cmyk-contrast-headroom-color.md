---
id: WSW-20261008-004
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
  - contrast
  - tone
  - defaults
related:
  - WSW-20261008-001
  - WSW-20261008-003
---

# Extend contrast past 200 % and push colour into the mix

## Summary

Two changes for colour contrast:

1. **Contrast headroom.** The control now runs to 300 %. Between 100 % and
   200 % the soft S-curve blends in as before; above 200 % the curve keeps
   steepening (k 3 -> 6) instead of being ignored, so the slider that was
   "maxed out" now has real range without hard clipping.
2. **Colour in the mixes.** Defaults move to saturation **115 %** (was 105),
   black (GCR) **65 %** (was 80), and black weight **105 %** (was 120).
   Luminance contrast alone cannot add chroma, because the overprint
   multiplication flattens it; keeping K out of the mid tones and pushing
   more chroma through C/M/Y is what separates colours on paper.

## Reason

Owner: "the problem is that contrast is maxed out, and the color contrast
just still isnt good." The slider was capped at 200 %, and at 80 % GCR with
120 % K weight the black ink was swallowing the colour separation.

## Implementation

- `software/converter_core/cmyk.py`: contrast > 2.0 now sets the blend
  amount to 1.0 and grows the S-curve steepness up to k = 6 (contrast 3.0).
- `software/generator_tabs/cmyk_tab.py`: contrast range 25-300 with an
  explanatory tooltip; defaults saturation 115, GCR 65, K weight 105.
- `software/README.md`: shipped-defaults sentence and recommended row.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 390
  tests (1 skipped: the pre-existing headless shader compile). New test: a
  gray ramp at contrast 3.0 spans more than 0.85 of the K range with
  shoulders still inside 0.01-0.99 (contrast 2.0 spans ~0.70, so the test
  distinguishes the extension); the shipped-defaults test asserts
  saturation 115, GCR 65, and K 105.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Raising the luminance contrast alone was rejected: past the ink model's
  flattening it only deepens shadows; chroma has to come from the
  separation.
- Hard-clipping contrast (the pre-2026-10-08 math) was rejected again: it
  posterizes before it gives usable punch.

## Risks and follow-up

- k = 6 is a strong curve - smooth, but close to a threshold look at the
  extremes; back off toward 200-240 % if banding appears.
- The measured calibration profile is still the final colour-fidelity step.

## Files

- `software/converter_core/cmyk.py`: steepening soft contrast.
- `software/generator_tabs/cmyk_tab.py`: range, tooltip, defaults.
- `software/tests/test_cmyk_tab.py`: contrast-300 regression test and
  defaults.
- `software/README.md`: documentation.
