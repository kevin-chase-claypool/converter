---
id: WSW-20261007-012
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
  - WSW-20261007-011
  - WSW-20261007-010
---

# Print the calibration mix cells at the dense spot spacing

## Summary

On the line and crosshatch screens the mix patches were screened at the
artwork pitch, so each ink covered only about a quarter of the cell and the
overlap that carries the overprint information was tiny (roughly 6 % for a
pair and 0.4 % for the C+M+Y+K quad). The dense single-ink spots, meanwhile,
used a tight spacing, so the multiply check compared mismatched coverages
and would have reported false errors on a real print. Sheet version 5 prints
every mix patch at the same tight spacing and level count as the spots
(`dot_scale` 1.40 for dots; the dense pitch for lines; the dense pitch plus
levels 4 for crosshatch), so the mix cells are now dense color fields with a
real overprint signal and the spot-based model is consistent with them.

## Reason

Owner: "it just doesnt seem like this one gives you much information." The
observation was correct: for the line screens the mix row (especially the
quad) carried almost no overprint information and could not have validated
the ink model.

## Implementation

- `software/generator_tabs/cmyk_sheet.py`: mix and spot cells now share one
  `dense_cell` definition per screen; version 5.
- `software/generator_tabs/cmyk_tab.py`, `docs/testing/CMYK_CALIBRATION.md`,
  `software/README.md`: describe the mixes as dense and spot-matched.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 370
  tests (1 skipped: the pre-existing headless shader compile); the new test
  asserts every mix patch matches its inks' spot pitch, levels, and dot
  scale on all three screens.
- Default 200 x 180 mm line sheet mark counts: about 334/384/366/366
  polylines for C/M/Y/K (the dense mixes add roughly 60-80 per ink).
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Raising the spot spacing instead (to match the artwork pitch) was
  rejected: it would dilute the measured ink transmittance with paper and
  give the preview the wrong multipliers.

## Risks and follow-up

- Dense mix cells add marks to every ink file; for crosshatch screens the
  mixes use three line families per ink, so their files grow the most.
- Any v4 or older sheet should be reprinted before analysis.

## Files

- `software/generator_tabs/cmyk_sheet.py`: shared dense mix/spot cells.
- `software/generator_tabs/cmyk_tab.py`: tooltip wording.
- `software/tests/test_cmyk_sheet.py`: spacing-consistency test.
- `docs/testing/CMYK_CALIBRATION.md`, `software/README.md`: wording.
