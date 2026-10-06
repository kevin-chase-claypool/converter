---
id: WSW-20261006-013
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - user-interface
  - layout
  - preview
related:
  - WSW-20261006-011
  - WSW-20261006-012
---

# Settings pane fills its column and removes the dead strip

## Summary

The dead strip between the feature settings and the preview is gone. The
settings column now fills its side of the splitter edge-to-edge, so the
preview starts immediately after it at any window width.

## Reason

The Convert page laid the sidebar out with `addStretch(1)`: the stretch took
the tab pane's extra width while the scroll area stayed at its size hint, and
the 320/340 px maximum widths stopped it from growing into the pane. The owner
photographed the resulting empty strip between the settings and the preview.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `convert_layout.addWidget(sidebar_scroll, 1)`
  replaces the trailing stretch, and the sidebar's 320 px and scroll area's
  340 px maximum widths were removed so the column fills whatever width the
  splitter gives it.
- `software/tests/test_generator_tabs.py` asserts the settings scroll area
  fills its stacked page within 4 px.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 9 tests pass, including the dead-strip check.
- Full suite: `python -m unittest discover -s software\tests` -> 228 tests
  pass.
- Offscreen measurements: at 500x1000 the splitter is `[274, 507]` with the
  stack and sidebar both 274 px; at 1500x950 it is `[380, 1104]` with both
  380 px. The render shows the preview starting at the settings edge.

## Struggles and rejected approaches

- Capping the stack to the sidebar width was rejected: it would stop the owner
  from widening the settings column, and the real cause was the layout stretch,
  not the pane size.

## Risks and follow-up

- Dragging the splitter wider widens the settings panel's group boxes (the
  numeric fields keep their own widths); the defaults remain 380 px.

## Files

- `software/qt_svg_to_gcode.pyw`: sidebar layout and width caps.
- `software/tests/test_generator_tabs.py`: dead-strip regression test.
