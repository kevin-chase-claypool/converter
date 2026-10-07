---
id: WSW-20261007-014
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/cmyk_sheet.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_sheet.py
tags:
  - cmyk
  - screening
  - crosshatch
related:
  - WSW-20261007-002
  - WSW-20261007-010
---

# Extend crosshatch screens past four families

## Summary

The crosshatch screen now supports levels 2-9 (up to eight line families;
it was clamped to four). The first four families keep the classic +45
degree spacing; any further families spread evenly over the half turn
(180 degrees / n) so no direction repeats. The **Hatch levels** control
range is 2-9, and the calibration sheet's hatch-level ladder sweeps 2-8
(sheet version 6) so the extended range is measurable on one sheet.

## Reason

Owner: "is there a reason it doesnt allow for higher crosshatch levels than
5?" The four-family clamp was a 45 degree spacing assumption in
`screen_channel`, not a machine limit. Extra families give finer tone steps
(one more threshold band per level) and darker maximum fills, which matters
at larger pitches where one family covers little area.

## Implementation

- `software/converter_core/cmyk.py`: `passes = max(1, int(levels) - 1)`
  (no four-family clamp); the family angle step is `180 / max(4, passes)`,
  so levels 2-5 render exactly as before.
- `software/generator_tabs/cmyk_tab.py`: Hatch levels range 2-9 with an
  updated tooltip that explains the spacing rule.
- `software/generator_tabs/cmyk_sheet.py`: `HATCH_LEVELS` becomes
  (2..8) and `SHEET_VERSION` becomes 6; the crosshatch step row keeps ten
  cells (seven levels + three overdraw) like the other screens.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 373
  tests (1 skipped: the pre-existing headless shader compile). New tests:
  level 9 produces more marks than level 6, the control accepts 9, and the
  sheet's crosshatch ladder reports levels 2-8.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Spacing every family at 45 degrees was rejected: beyond four families
  the directions repeat and the "extra" families would simply double-draw.
- Keeping the clamp and adding only a fifth family was rejected as an
  arbitrary half-measure; the even-spread rule scales to any count.

## Risks and follow-up

- Each family is a full-cell line pass, so mark count and plot time scale
  linearly with the level count; eight families double the ink of four.

## Files

- `software/converter_core/cmyk.py`: family count, angle spread.
- `software/generator_tabs/cmyk_tab.py`: control range and tooltip.
- `software/generator_tabs/cmyk_sheet.py`: ladder range, version 6.
- `software/tests/test_cmyk_tab.py`, `software/tests/test_cmyk_sheet.py`:
  coverage.
