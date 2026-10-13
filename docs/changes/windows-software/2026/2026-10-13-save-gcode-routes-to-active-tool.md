---
id: WSW-20261013-005
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - cmyk
  - save
  - file-menu
  - workflow
related:
  - WSW-20261013-003
---

# File > Save G-code routes to the active tool's own save

## Summary

Ctrl+S / File > Save G-code on a generator tab now saves the way that tab is
meant to save. The CMYK tab writes its four layer programs; tabs without a
multi-file save still run the single-file Convert flow.

## Reason

Operator report (2026-10-13): "i thought we were building 4 gcodes?" after
Ctrl+S produced one `IMG_0514.gcode`. The shortcut always ran `convert()`,
which resolves the active tab's combined artwork and writes a single program -
for a CMYK set that merges all four inks into one plot with no layer suffix.
The four-file save only happened through the tab's own button ("Save 4 G-code
files...").

## Implementation

`save_active_tool()` checks the current stack widget for a callable `save_all`
(the CMYK tab has one) and delegates; otherwise it calls `convert()` as
before. The File menu action is bound to it instead of `convert` directly.

## Verification

- `py_compile` clean; 88 tests pass in `test_generator_tabs` and
  `test_cmyk_tab`.
- Bench check: with the CMYK tab active, Ctrl+S should now open the
  "Save 4 G-code files" flow (folder destination honored per
  `WSW-20261013-003`).

## Struggles and rejected approaches

Renaming the menu item dynamically was considered; delegation keeps one
action and one shortcut with the same labels everywhere.

## Risks and follow-up

- A tab that later grows a multi-file save should expose `save_all` to inherit
  this routing automatically.

## Files

- `software/qt_svg_to_gcode.pyw`: `save_active_tool`, menu binding.
- `docs/project/ENGINEERING_LOG.md`: session entry.
