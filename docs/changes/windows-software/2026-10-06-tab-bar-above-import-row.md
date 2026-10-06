---
id: WSW-20261006-012
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
related:
  - WSW-20261006-011
---

# Lift the tab bar above the import and save row

## Summary

The Convert / Flow Field / Line Draw / 3D Wireframe tab bar now spans the top
of the window, above the Artwork/G-code/Save row. The settings pages still swap
below it, and the import row, preview, and log stay static.

## Reason

The tab bar was attached to the settings pane inside the splitter, so it sat
below the import row and only spanned the left column. The owner asked for it
at the very top, above import and save.

## Implementation

- `software/qt_svg_to_gcode.pyw`: the `QTabWidget` was replaced by a detached
  `QTabBar` (expanding off, document mode) plus a `QStackedWidget`. The bar is
  the first widget in the window layout; the stack holds the Convert page and
  each generator page and is the left pane of the settings/preview splitter.
  `on_tab_changed` syncs the stack, and `load_generator_tabs` adds a tab and a
  page per module.
- `software/tests/test_generator_tabs.py` now checks the `QTabBar` /
  `QStackedWidget` split, that the bar's y position is above the Artwork
  field's, and keeps the existing static-chrome and layout checks.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 8 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 227 tests
  pass.
- Offscreen render at 1500x950: tab bar top edge at y=6, Artwork field at
  y=34, tabs compact and left-aligned, preview filling the area right of the
  settings pane.

## Struggles and rejected approaches

- Keeping the `QTabWidget` and moving only the import row below it was
  rejected because a QTabWidget's bar cannot span wider than its pages without
  duplicating the static content per tab.

## Risks and follow-up

- Any code that referenced `window.tabs` must use `window.tab_bar` (labels)
  and `window.stack` (pages); the in-repo references and tests were updated.

## Files

- `software/qt_svg_to_gcode.pyw`: detached tab bar and stacked pages.
- `software/tests/test_generator_tabs.py`: structure and ordering tests.
- `software/README.md`: user-facing description.
