---
id: WSW-20261007-013
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
  - resolution
  - user-interface
related:
  - WSW-20261007-005
---

# Raise the CMYK resolution cap for large sources

## Summary

The CMYK tab's **Resolution px** control was capped at 2000; it now goes to
100000, which is beyond any camera or scanner source and therefore
effectively uncapped. The setting only ever downsamples - the image is never
upsampled - so any value at or above the source's longest side keeps the
full-resolution tone map, and the tooltip plus `software/README.md` now say
so, including the memory consequence of keeping a very large source.

## Reason

Owner: "in cmyk feature im limited by the resolution i can increase to. i
need to increase quite a bit, dont put a limit on it." The 2000 px ceiling
from `WSW-20261007-005` blocked high-resolution sources.

## Implementation

- `software/generator_tabs/cmyk_tab.py`: `int_spin(1200, 200, 2000, 50)` ->
  `int_spin(1200, 200, 100000, 50)` plus a tooltip explaining the no-upsample
  behaviour.
- `software/README.md`: CMYK control list notes the effectively uncapped
  range and the memory characteristic.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 371
  tests (1 skipped: the pre-existing headless shader compile); a new test
  sets the control to 8192 and confirms the value sticks.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- A true "no maximum" is not possible with a spin box; 100000 px is far
  beyond real source images while keeping the widget valid.
- Adding a hard memory guard was rejected for now: the owner explicitly
  asked for no limit, and the retained pixels are exactly the source pixels
  the operator chose to keep.

## Risks and follow-up

- Large retained sources allocate memory in proportion to their size; a
  10000 px source uses roughly an order of magnitude more memory than the
  old 2000 px ceiling would have.

## Files

- `software/generator_tabs/cmyk_tab.py`: control range and tooltip.
- `software/tests/test_cmyk_tab.py`: uncapped-value test.
- `software/README.md`: current-state note.
