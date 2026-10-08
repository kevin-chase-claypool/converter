---
id: WSW-20261007-017
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - bugfix
  - user-interface
related:
  - WSW-20261007-001
  - WSW-20261007-010
---

# Apply the CMYK Artwork scale to the screened marks

## Summary

The CMYK tab's **Artwork scale** control now works: the screened layers are
scaled about the page centre by the chosen percentage (10-1000 %), exactly
like every other generator tab. 100 % remains a no-op. Previously the value
only entered the layer cache key, so changing it rebuilt the same full-size
screen and nothing appeared to happen.

## Reason

Owner: "artwork scale in cmyk feature doesnt appear to do anything."

## Implementation

- `software/generator_tabs/cmyk_tab.py`: `_build_artwork_layers` applies
  `scale_polylines(marks, scale_pct / 100, width, height)` to each ink's
  screened marks before writing the per-ink SVGs, so the preview, planning,
  and G-code all see the scaled geometry.
- The calibration sheet deliberately stays 1:1: sheet mode keeps its fixed
  fiducial geometry regardless of the scale control.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 375
  tests (1 skipped: the pre-existing headless shader compile). The new test
  rebuilds at 50 % and asserts both mark spans halve about the page centre.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Scaling the source image fit instead of the marks was rejected: scaling
  the marks scales the screen pitch and all four inks together about the
  page centre, which is what every other tab's Artwork scale means.

## Risks and follow-up

- Scales above 100 % can push marks beyond the page, as in every other
  generator tab; the converter's bed clipping still applies.

## Files

- `software/generator_tabs/cmyk_tab.py`: scale application.
- `software/tests/test_cmyk_tab.py`: scale regression test.
