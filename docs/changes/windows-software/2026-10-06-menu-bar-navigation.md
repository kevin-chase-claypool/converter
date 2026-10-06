---
id: WSW-20261006-022
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - user-interface
  - navigation
related:
  - WSW-20261006-021
  - WSW-20261006-009
---

# Add File / Tools / View / Help menus and move tool selection into Tools

## Summary

The window now has a standard menu bar: **File** (open artwork, set G-code
destination, save G-code, exit), **Tools** (All Tools dashboard plus every
tool, grouped in submenus), **View** (reach guide, pen-down path, zoom, reset
view, log), and **Help** (keyboard shortcuts, About). The artwork/G-code row
and the small navigation bar were removed; the current paths are shown in the
status bar.

## Reason

The owner wanted the familiar File/View/Help structure to clean up the UI and
to hold tool selection, so the growing tool list no longer needs permanent
chrome.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `build_menus()` creates the four menus.
  **Tools** builds an exclusive `QActionGroup`: Convert is Ctrl+1, the
  generators follow their discovery order with Ctrl+2...Ctrl+0, and All Tools
  is Ctrl+T. `show_tool()` now checks the matching menu action and sets the
  window title; the All Tools dashboard page is unchanged.
- **View** mirrors the existing `Machine reach guide` and `Show X/Y pen-down
  path` checkboxes, adds zoom in/out/reset for the preview, and toggles the
  log's visibility. **Help** shows the shortcut list (F1) and an About dialog
  naming the converter core version.
- The artwork/G-code row and navigation bar are gone. `svg_path` and
  `gcode_path` remain as the path data holders behind the File dialogs, and
  the status bar shows `Artwork: ... | G-code: ...`.
- `software/tests/test_generator_tabs.py`: menu-bar check, Tools-menu page
  switching with checkmarks, status-bar paths, dashboard preview guard, and
  the existing scale/1:1/stale checks.

## Verification

- `python -m unittest discover -s software\tests -p "test_generator_tabs.py" -v`
  -> 17 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 266 tests
  pass.
- Offscreen render at 1400x950: File/Tools/View/Help menu bar at the top, the
  settings column and preview below it, log, and a status bar showing the
  artwork and G-code paths; no file row or navigation bar remains.

## Struggles and rejected approaches

- Keeping the file row alongside the File menu was rejected: the paths are
  visible in the status bar, which removes a permanent row.

## Risks and follow-up

- Paths are no longer directly editable; use File ▸ Open Artwork and File ▸
  Set G-code Destination.

## Files

- `software/qt_svg_to_gcode.pyw`: menus, status bar, show_tool title.
- `software/tests/test_generator_tabs.py`: menu and status-bar tests.
- `software/README.md`, `software/generator_tabs/README.md`: navigation docs.
