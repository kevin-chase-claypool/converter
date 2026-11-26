---
id: WSW-20261126-004
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
  - fill-bed
  - generator-tabs
  - printable-area
  - artwork-scale
  - regression
related:
  - HW-20261126-001
  - WSW-20261126-003
---

# Fill the bed by default for CMYK Photo

## Summary

CMYK Photo now honors the converter's global **Fill bed** default. Generated
CMYK artwork is enlarged until its bounds touch the current drawable circle
instead of being forced to the tab's fixed page at 1:1. Other generator tabs
retain their existing 1:1 behavior.

## Reason

The main Convert page defaults to **Fill bed**, but `MainWindow.settings_for_source()`
replaced that with manual scale `1.0` for every generator source. As a result,
a `200 x 200 mm` CMYK page at `100%` remained about 200 mm across inside the
184.15 mm-radius drawing circle. The machine and stock circles were correct;
the generator fit policy made the artwork look small.

## Implementation

- CmykTab declares `USES_BED_FIT_DEFAULT = True`.
- Generator handoff now preserves the global `fill` or `inside` fit for tabs
  that declare that policy. Other generator tabs still receive manual scale
  `1.0`, preserving their designed page dimensions.
- Selecting **Manual** globally still keeps CMYK at manual 1:1. Selecting
  **Fit inside** performs the no-crop inscribed fit.

## Verification

- A new regression confirms CMYK Photo passes `fit_mode=fill` into the shared
  fitting pipeline, computes the fill scale, and still respects an explicit
  Manual selection.
- The existing Flow Field regression confirms ordinary generator tabs remain
  manual 1:1.
- A real Golden Sunset CMYK export with a 250 mm page now reaches maximum XY
  radii of `183.10-183.41 mm`, versus about `174.21-174.36 mm` before this
  change, so the saved programs use the full drawable area.
- The four regenerated programs pass `check_gcode_motion.py --strict`.
- Complete converter discovery passes `759` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

Increasing the CMYK page alone would leave the global fit behavior ambiguous
and make manual previews inconsistent. Applying Fill bed to every generator
would break tools whose page size is an intentional output dimension. The
policy is therefore explicit to CMYK Photo only.

## Risks and follow-up

Fill bed intentionally clips the four corners of a rectangular source. Use
**Fit inside** when the entire image must remain inside the circle. The new
scale changes effective screen pitch, so inspect the four-pen preview before
saving. Physical paper validation remains separate.

## Files

- `software/generator_tabs/cmyk_tab.py`: opt CMYK Photo into the bed-fit policy.
- `software/qt_svg_to_gcode.pyw`: preserve default fit for opted-in generators.
- `software/tests/test_generator_tabs.py`: fill/manual routing regression.
- `software/README.md`: current CMYK Photo fit behavior.
