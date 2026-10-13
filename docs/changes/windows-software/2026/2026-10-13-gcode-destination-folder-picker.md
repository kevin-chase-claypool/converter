---
id: WSW-20261013-003
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - file-menu
  - save
  - cmyk
  - workflow
related:
  - WSW-20261013-002
---

# Set G-code Destination picks a folder, and multi-layer tabs use it

## Summary

Two save-path defects fixed together:

1. **File > Set G-code Destination...** now opens a *folder* picker. The
   chosen folder is remembered (`self.gcode_dir`) and shown as
   `<folder>/<artwork-stem>.gcode` in the status line.
2. Multi-layer tools (the CMYK tab writes four layer files; calibration
   sheets write more) now write into that folder with their own derived
   names instead of opening a per-save "Save G-code files" dialog.

## Reason

Operator report (2026-10-13): "set gcode destination isnt letting me choose a
folder". The command opened the native save-a-file dialog (`getSaveFileName`,
titled "Save G-code"), and the CMYK tab never saw the result anyway: it calls
`export_program_set(entries, None, base)` with `base_path=None`, so every save
prompted for a file name regardless of the chosen destination.

## Implementation

- `qt_svg_to_gcode.pyw`: `pick_gcode()` uses
  `QFileDialog.getExistingDirectory`, seeds the start folder from the current
  destination, derives the base stem from the artwork when the field is empty,
  and records `self.gcode_dir` (initialised empty next to
  `auto_gcode_path`).
- `export_program_set()`: when called with `base_path=None` and a destination
  folder is set, it derives `<folder>/<default_base>` (falling back to
  `plot.gcode`) instead of prompting. The dialog remains for users who never
  chose a destination.

## Verification

- `python -m py_compile software\qt_svg_to_gcode.pyw`: clean.
- `python -m unittest software.tests.test_generator_tabs
  software.tests.test_cmyk_tab`: 88 tests, OK (1 skipped).
- Manual UI walk-through (pick folder, save the CMYK set) is the next bench
  check when the app is restarted.

## Struggles and rejected approaches

Kept the destination field as a *file path* underneath (the folder picker
derives the name) so the Convert tab's Ctrl+S path needs no change; a full
directory-as-destination model would have touched every save call site.

## Risks and follow-up

- The derived file name keeps the stem of the current destination field; after
  opening a different artwork the stem stays at the first choice. Edit the
  field (data holder) or re-pick the folder if a new base name is wanted.

## Files

- `software/qt_svg_to_gcode.pyw`: folder picker, `gcode_dir`, batch save.
- `docs/project/ENGINEERING_LOG.md`: session entry.
