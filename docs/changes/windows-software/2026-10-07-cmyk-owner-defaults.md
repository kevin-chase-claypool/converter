---
id: WSW-20261007-015
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - defaults
  - crosshatch
  - user-interface
related:
  - WSW-20261007-005
  - WSW-20261007-014
  - WSW-20261007-016
---

# Set the CMYK defaults to the owner's tuned workflow

## Summary

The CMYK tab now opens with the settings from the owner's working session:
**Crosshatch levels** style, hatch level 5, dot pitch 1.2 mm, resolution
6000 px, max marks/ink 40000, dot size 100 %, solid dots off, and the
existing auto levels / saturation / contrast / gamma / GCR / weights / pen
width / overdraw values (which already matched). Dot size and solid dots
only affect the dot screens; they are inert in the crosshatch default.

## Reason

Owner: "keep the settings you see in the image as defaults." The screenshot
showed the tuned crosshatch workflow (momandbennett.jpg render).

## Implementation

- `software/generator_tabs/cmyk_tab.py`: style combo selects `crosshatch`;
  resolution default 1200 -> 6000; max marks 15000 -> 40000; dot size
  75 -> 100; solid dots checked -> unchecked; hatch levels 4 -> 5.
- `software/README.md`: the shipped-defaults sentence and the recommended
  settings table row match the new set.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 375
  tests (1 skipped: the pre-existing headless shader compile); the
  shipped-defaults test now asserts the crosshatch style, level 5, dot
  size 100, solid dots off, 40000 marks, and 6000 px resolution.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Keeping the WSW-20261007-005 halftone defaults as a separate "photo"
  preset was rejected: the owner asked for these values, and the dot-screen
  fields remain one click away in the same tab.

## Risks and follow-up

- New sessions start heavier: crosshatch level 5 with 6000 px resolution
  and 40000 marks suits the owner's machine but is slower than the old
  defaults; the controls are unchanged for lighter runs.

## Files

- `software/generator_tabs/cmyk_tab.py`: default values.
- `software/tests/test_cmyk_tab.py`: default assertions.
- `software/README.md`: current-state defaults.
