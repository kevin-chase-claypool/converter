---
id: WSW-20261006-014
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/_tab_common.py
  - software/qt_svg_to_gcode.pyw
tags:
  - user-interface
  - generators
  - layout
related:
  - WSW-20261006-013
---

# Generator controls fill the settings column

## Summary

Flow Field, Line Draw, and 3D Wireframe controls now fill the settings column
edge-to-edge, with the tab hint and status stacked underneath instead of
sitting beside the controls. The settings column also has a 280 px floor so
the preview cannot squeeze it into a sliver.

## Reason

The generator tab base still used a horizontal layout: the control scroll
area, the hint, and the status were laid out left-to-right. At narrow window
widths the scroll area was squeezed to about 110 px and the form labels and
fields were clipped, while the hint text occupied the rest of the tab page -
visible in the owner's screenshots.

## Implementation

- `software/generator_tabs/_tab_common.py`: `GeneratorTab` uses a
  `QVBoxLayout`; the control scroll area takes the stretch (no maximum width)
  and the hint/status labels follow it. The scroll area is exposed as
  `controls_scroll` for tests.
- `software/qt_svg_to_gcode.pyw`: `stack.setMinimumWidth(280)` keeps the
  feature settings usable when the window is narrow; the preview takes the
  remainder.
- `software/tests/test_generator_tabs.py` asserts that at 630x1000 the active
  generator's controls fill the tab pane within its 6 px margins, the tab is
  at least 280 px wide, and the status sits below the controls.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 10 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 229 tests
  pass.
- Offscreen 630x1000 render on Flow Field: splitter `[280, 507]`, controls
  268 px inside the 280 px pane, status below the controls, preview filling
  the remainder with no gap.

## Struggles and rejected approaches

- Capping the generator controls at a fixed width was rejected; the other
  tabs already fill their column, and a fixed cap recreates the dead strip.
- Letting the preview keep a 507 px minimum without a settings floor was
  rejected because the settings pane collapsed to 120 px at narrow widths.

## Risks and follow-up

- Below roughly 800 px total width the settings form scrolls horizontally in
  the offscreen font metrics; at normal widths it fits.

## Files

- `software/generator_tabs/_tab_common.py`: vertical tab layout.
- `software/qt_svg_to_gcode.pyw`: settings column minimum width.
- `software/tests/test_generator_tabs.py`: narrow-layout regression tests.
- `software/README.md`: user-facing description.
