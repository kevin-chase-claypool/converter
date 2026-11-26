---
id: WSW-20261126-011
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - cmyk
  - image-defaults
  - artwork-layout
  - sidecar
  - recipe
  - restore
  - user-interface
---

# Save CMYK defaults for the current image

## Summary

The CMYK Image group now includes **Save defaults for this image**. It writes
the current complete CMYK recipe and artwork placement immediately to that
image's `.theta-layout.json` sidecar, rather than waiting for artwork switch or
application close.

## Reason

The per-image sidecar already contained every CMYK control visible in the
screenshots, but it was written only by automatic lifecycle events. The user
needed a direct, discoverable way to preserve the tuned recipe for one image.

## Implementation

- Added the explicit Image-group action and status feedback.
- The action calls the existing atomic artwork-layout writer, which captures:
  image options and per-ink weights, screen style and pitch, wave controls,
  hatch levels, overdraw, pen width, path tolerance, mark cap, seed, row order,
  kinematics and center hold, pen and measured offsets, preview/write layers,
  calibration state, page/margin/Artwork scale, registration state, artwork
  placement, and every other registered generator-tab recipe.
- Successful writes now also add the sidecar path to the converter log.
- Opening the exact same image restores the recipe through the existing
  version-2 layout path.

## Verification

- A MainWindow regression sets the complete screenshot recipe, clicks the new
  button, verifies the sidecar fields, mutates multiple controls, restores the
  sidecar, and confirms the saved values return.
- The complete generator and CMYK modules pass `153` tests with one expected
  OpenGL-context skip. Complete converter discovery passes `643` tests with
  one expected OpenGL-context skip, and Python compilation passes.

## Struggles and rejected approaches

Relying only on close/switch auto-save was rejected because it is invisible and
offers no confirmation. Saving a global preset was rejected because these
settings are image-specific and the existing sidecar already provides the
correct ownership boundary.

## Risks and follow-up

The sidecar lives beside the source image and requires that directory to be
writable. Failure is reported rather than silently falling back to global
defaults. A moved or renamed image needs its matching `.theta-layout.json`
sidecar moved with it.

## Files

- `software/generator_tabs/cmyk_tab.py`: save-now action and status.
- `software/qt_svg_to_gcode.pyw`: success log with sidecar path.
- `software/tests/test_generator_tabs.py`: recipe persistence/restore
  regression.
- `software/README.md`: current per-image defaults behavior.
