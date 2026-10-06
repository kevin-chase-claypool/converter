---
id: WSW-20261006-009
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - user-interface
  - preview
  - gcode
related:
  - WSW-20261006-005
  - WSW-20261006-008
---

# Put the G-code output to the right of the preview

## Summary

The G-code command list moved out of the Convert tab and now sits in its own
pane to the right of the shared preview panel. It is static window furniture,
so the emitted program stays visible whichever tab built the preview.

## Reason

The command list is the output of the preview/conversion pipeline, not a
Convert-tab setting, and the owner asked for it beside the preview area. It
was previously inside the Convert tab, where it disappeared on generator tabs
and competed for width with the settings sidebar.

## Implementation

- `software/qt_svg_to_gcode.pyw`: the window-level splitter is now
  **tabs | preview panel | command list** with stretch factors `1 / 1 / 0` and
  initial sizes `700 / 620 / 300`. The Convert tab now contains only the
  settings sidebar.
- `software/tests/test_generator_tabs.py` adds a placement test: the command
  list is not a child of the tab widget and its x position is greater than the
  preview panel's.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 7 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 226 tests
  pass.
- Offscreen render of the 1500x950 window: settings on the left, preview in
  the middle, empty G-code list pane on the right, all visible on every tab.

## Struggles and rejected approaches

- Keeping the command list inside the Convert tab and adding a second copy
  beside the preview was rejected: one program has one output list.

## Risks and follow-up

- At narrow window widths the splitter gives the command list its minimum
  share; the pane remains resizable and the list scrolls.

## Files

- `software/qt_svg_to_gcode.pyw`: splitter layout.
- `software/tests/test_generator_tabs.py`: placement regression test.
- `software/README.md`: user-facing description.
