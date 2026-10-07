---
id: WSW-20261007-016
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
  - user-interface
  - screening
related:
  - WSW-20261007-013
---

# Raise the CMYK max-marks cap

## Summary

**Max marks/ink** now runs up to 200000 (was capped at 40000). The cap only
guards planning scale: mark count sets the number of pen cycles, so plot
time scales roughly linearly with it. It applies to the dot-style screens
(halftone, stipple, TSP); the line and crosshatch screens are not capped by
it.

## Reason

Owner: "im trying to sharpen the image, so far i had to increase to 40000
and 5000 res, 40000 was the limit, but im wondering if it could be higher."
It can; the old value was an arbitrary ceiling from the first CMYK release.

## Implementation

- `software/generator_tabs/cmyk_tab.py`: `int_spin(15000, 200, 40000, 500)`
  -> `int_spin(15000, 200, 200000, 500)`.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 374
  tests (1 skipped: the pre-existing headless shader compile); a new test
  sets the control to 80000 and confirms the value sticks.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Removing the ceiling entirely was rejected for now: beyond roughly
  200000 marks the four ink programs become multi-day plots, and the
  selector still needs a finite range.

## Risks and follow-up

- A high mark count multiplies the M3/M5 pen cycles per ink; a dense
  halftone program can take days at 200000 marks.

## Files

- `software/generator_tabs/cmyk_tab.py`: control range.
- `software/tests/test_cmyk_tab.py`: uncapped-value test.
