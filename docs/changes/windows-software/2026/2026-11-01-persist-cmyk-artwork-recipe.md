---
id: WSW-20261101-004
date: 2026-11-01
category: windows-software
affected_categories:
  - windows-software
status: verified
components:
  - software/qt_svg_to_gcode.pyw
  - software/generator_tabs/cmyk_tab.py
tags:
  - artwork-layout
  - settings
  - persistence
  - cmyk
  - restart
related:
  - WSW-20261101-003
---

# Persist each artwork's CMYK recipe across restarts

## Summary

The per-artwork layout sidecar now saves and restores the complete CMYK recipe
as well as artwork placement. Reopening the same image restores the previous
image controls, screen settings, Wave geometry, row order, kinematics, page
layout, pen corrections, and preview/write selections.

## Reason

The converter previously persisted only `artwork_offset_x_mm` and
`artwork_offset_y_mm`. Restarting the application after changing the Jeep
recipe therefore restored placement and the image but reset the CMYK controls
to their shipped defaults.

## Implementation

- Extended `<artwork-file>.theta-layout.json` from version 1 to version 2.
- Main-window layout save/restore now delegates optional tab-specific state to
  `artwork_layout_state()` and `restore_artwork_layout_state()` hooks.
- The CMYK implementation records every operator-facing recipe control,
  including its current row order and XY-only/rotating-bed choice.
- Version-1 sidecars remain readable and continue to restore their placement
  fields without requiring migration.
- Restoring a recipe invalidates cached CMYK layers and analysis results so the
  next preview rebuilds from the restored values.

## Verification

- The artwork re-import regression saves and restores placement plus a modified
  CMYK recipe across two `MainWindow` instances.
- A separate regression verifies backward-compatible version-1 restoration.
- The focused generator-tab and CMYK-tab suites pass `142` tests with one
  expected OpenGL-context skip.
- The complete converter suite passes `602` tests with one expected
  OpenGL-context skip.
- Reopening the Jeep image in the restarted application logged
  `Restored generator recipes: cmyk.`; the expected placement, image controls,
  Wave recipe, XY-only motion, row order, page settings, and layer selections
  were visible, and Preview completed with 242,067 moves.

## Struggles and rejected approaches

Storing the recipe in the global application settings was rejected because
different source images need different CMYK controls. Keeping only the last
open image's controls would still overwrite the Jeep recipe when another image
was opened.

## Risks and follow-up

Only tabs that opt into the layout-state hooks are persisted. Other generator
tabs retain their current defaults until they provide artwork-specific state.
The sidecar remains beside the source artwork, so moving the image without its
`.theta-layout.json` companion also moves it away from its saved recipe.

## Files

- `software/qt_svg_to_gcode.pyw`: versioned generic tab-state persistence.
- `software/generator_tabs/cmyk_tab.py`: complete CMYK recipe capture/restore.
- `software/tests/test_generator_tabs.py`: round-trip and version-1 tests.
- `software/README.md`: operator behavior and sidecar contents.
