---
id: WSW-20261006-011
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs/_tab_common.py
tags:
  - user-interface
  - preview
  - layout
related:
  - WSW-20261006-010
---

# Make the settings pane content-width so the preview fills the rest

## Summary

The feature settings pane (the tab pane) now stays at its content width -
about 380 px - and the preview takes the entire remainder of the window. The
dead strip between the settings sidebar and the preview is gone.

## Reason

The window splitter still reserved 680 px for the tab pane while the Convert
sidebar is capped at 340 px, and the Convert tab page stretched to fill the
rest. The owner flagged the resulting ~300 px empty strip as wasted space.

## Implementation

- `software/qt_svg_to_gcode.pyw`: the main splitter keeps stretch factor 0 on
  the tab pane and 1 on the preview, with initial sizes `380 / 1120`. The
  Convert tab still holds the settings sidebar plus a stretch, which is now
  only the tab frame's width.
- `software/generator_tabs/_tab_common.py`: the tab hint and status moved from
  a side column to below the control column, so generator tabs also fit the
  narrow pane without clipping.
- `software/tests/test_generator_tabs.py` asserts the initial split gives the
  tabs pane at most 420 px and the preview more than twice that.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 7 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 226 tests
  pass.
- Offscreen render at 1500x950: splitter sizes `[380, 1104]`, preview starts
  immediately right of the settings column, and the generator tab's hint and
  status sit under its controls.

## Struggles and rejected approaches

- Widening the Convert sidebar to fill the pane was rejected: the preview is
  the workspace, and stretching form fields would not add usable space.
- Hiding the tab frame when Convert is active was rejected as more state for
  no benefit.

## Risks and follow-up

- The splitter stays draggable, so the settings pane can still be widened
  manually; long generator status text wraps in the narrow column.

## Files

- `software/qt_svg_to_gcode.pyw`: splitter sizes and stretch.
- `software/generator_tabs/_tab_common.py`: vertical hint/status layout.
- `software/tests/test_generator_tabs.py`: width regression test.
