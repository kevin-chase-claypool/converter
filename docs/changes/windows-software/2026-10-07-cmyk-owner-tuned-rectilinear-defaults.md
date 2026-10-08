---
id: WSW-20261007-025
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - cmyk
  - defaults
  - rectilinear
related:
  - WSW-20261007-024
  - WSW-20261007-023
---

# Set the CMYK defaults to the owner's tuned rectilinear set

## Summary

The CMYK tab now opens with the exact settings the owner tuned and
reported as great for the rectilinear fill: auto levels on, **saturation
130 %**, **contrast 200 %**, ink gamma 1.0, **black (GCR) 99 %**,
**resolution 10000 px**, weights **C 120 / M 120 / Y 120 / K 150 %**,
style **Rectilinear fill (joined rows)**, **dot pitch 0.10 mm**, dot size
100 %, solid dots off, hatch levels 8, overdraw 1, pen width 0.30 mm, max
marks 40000, seed 7, page 200 x 200 mm, margin 6 mm, **artwork scale
280 %**.

The two screenshots disagreed on one value: the first showed dot pitch
0.20 mm and the second 0.10 mm. The later state (0.10 mm) is used; it is a
single field to change if the other was meant.

## Reason

Owner: "these were all great settings, set these as defaults for
rectilinear."

## Implementation

- `software/generator_tabs/cmyk_tab.py`: the defaults above (saturation
  100 -> 130, contrast 100 -> 200, GCR 75 -> 99, resolution 6000 -> 10000,
  weights 100 -> 120/120/120/150, pitch 0.20 -> 0.10, hatch levels 5 -> 8,
  artwork scale 100 -> 280; style stays rectilinear).
- `software/tests/test_generator_tabs.py`: the every-tool artwork-scale
  convention test now expects 280 % for CMYK (it is the one tool whose
  tuned default is not 1:1) and 100 % for every other tool.
- `software/README.md`: shipped-defaults sentence and recommended-settings
  row.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 386
  tests (1 skipped: the pre-existing headless shader compile). The
  shipped-defaults test asserts every value above, and the artwork-scale
  convention test covers the CMYK exception.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Averaging the two screenshots' pitches was rejected: both are the owner's
  real states, and 0.10 mm (later) is the denser choice they were moving
  toward.

## Risks and follow-up

- This is a very heavy ink load: 0.10 mm pitch with 280 % scale puts mid
  tones near 0.56 mm effective spacing at 150 % black weight. Expect
  multi-hour per-pen plots and check paper wetness on large fills.
- Artwork scale 280 % enlarges every new artwork about the page centre;
  it is a per-job choice for users who want the photo to fill the bed.

## Files

- `software/generator_tabs/cmyk_tab.py`: the tuned defaults.
- `software/tests/test_cmyk_tab.py`, `software/tests/test_generator_tabs.py`:
  default assertions and the scale convention exception.
- `software/README.md`: current-state defaults.
