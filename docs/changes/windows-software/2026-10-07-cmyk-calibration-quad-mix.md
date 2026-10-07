---
id: WSW-20261007-011
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_sheet.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_sheet.py
  - docs/testing/CMYK_CALIBRATION.md
  - software/README.md
tags:
  - cmyk
  - calibration
  - test-print
  - ai-handoff
related:
  - WSW-20261007-010
  - WSW-20261007-009
---

# Add the C+M+Y+K quad to the calibration mixes

## Summary

The mix row now prints C+M, C+Y, M+Y, C+M+Y, and C+M+Y+K at full tone
(sheet version 4, ten cells per row like the ladders). Previously black
appeared only in dense single-ink spots, so the multiply check could not
validate black over ink and a pen-set calibration would have needed a second
print to cover it. With the quad on the same sheet, one print and one scan
now validate every ink and every overprint combination the preview model
uses.

## Reason

Owner: "did you pack as much into that space as possible so i dont need to
do multiple scans?" Auditing the sheet for analysis coverage found the one
real gap: no mix patch contained K.

## Implementation

- `software/generator_tabs/cmyk_sheet.py`: `MIX_SETS` gains
  `("c", "m", "y", "k")`; the mix row is five mixes plus four spots and the
  paper patch, which keeps the row at ten cells and the cell width equal to
  the ladder rows.
- `tools/cmyk_calibrate.py` needed no change: the validation loop already
  multiplies however many channels a mix patch names.
- `docs/testing/CMYK_CALIBRATION.md`, `software/README.md`, and the tab
  tooltip now describe the mixes as pairs, triple, and quad.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 369
  tests (1 skipped: the pre-existing headless shader compile), including
  the sheet census (mix patches now 5) and the synthetic-scan recovery
  (five validation rows, quad error within tolerance).
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Adding a separate black-overprint row was rejected: folding the quad into
  the existing mix row costs no space and keeps the layout at ten rows.

## Risks and follow-up

- Sheet version 4 changes the mix row, so any older v3 sheet must not be
  mixed with a v4 rebuild; the version is recorded in the manifest.

## Files

- `software/generator_tabs/cmyk_sheet.py`: quad mix cell, version 4.
- `software/generator_tabs/cmyk_tab.py`: tooltip wording.
- `software/tests/test_cmyk_sheet.py`: census and validation expectations.
- `docs/testing/CMYK_CALIBRATION.md`, `software/README.md`: wording.
