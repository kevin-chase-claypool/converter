---
id: WSW-20261008-017
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
  - screening
  - rectilinear
  - banding
related:
  - WSW-20261008-016
---

# Rectilinear pitch follows the inked tone and eases between rows

## Summary

The rectilinear screen advanced its row pitch from the *whole row's* average
tone, blank paper included, and it took that step in one go. A row crossing
both the subject and the background therefore jumped the spacing between
neighbouring rows, which is what the owner saw as striations in smooth areas
like the forehead. The advance now uses the mean tone of the samples the row
actually inks (values at or above the ink floor) and eases that tone over
successive rows, so the pitch still follows the picture but no longer steps.
On an edge fixture the largest gap-to-gap jump falls to 1.10x.

## Reason

Owner: "why are there striations". Measured on the owner's preview: rows sit
one pen width apart (0.11 mm x 280 % = 0.31 mm with a 0.30 mm pen), so tone is
carried by row spacing, and the spacing stepped wherever the row average
changed.

## Implementation

- `software/converter_core/cmyk.py`: `_line_runs` keeps an `eased_tone`
  running value; inked samples only, half-way step per row.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 403 tests
  pass, 1 skipped (the pre-existing headless shader compile).
- New test: a paper-to-0.35-tone edge gives a row-pitch sequence whose
  largest consecutive jump is under 1.25x.

## Struggles and rejected approaches

- Making the pitch strictly local (per run) was rejected: the rows are
  straight lines, so a per-run pitch would either bend them or seam the page
  into strips. Easing the row pitch removes the visible step without new
  geometry.

## Risks and follow-up

- The screen still quantises tone into discrete rows, so some texture remains;
  crosshatch at a fixed pitch is the alternative when a uniform screen
  matters more than the joined-row pen economy.

## Files

- `software/converter_core/cmyk.py`: eased row pitch in `_line_runs`.
- `software/tests/test_cmyk_tab.py`: edge banding test.
- `software/README.md`: rectilinear description.
