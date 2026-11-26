---
id: WSW-20261126-006
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/README.md
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
  - software/README.md
  - docs/project/ROADMAP.md
tags:
  - generator-tabs
  - cmyk
  - fit-inside
  - fill-bed
  - preview
  - printable-area
  - regression
related:
  - WSW-20261126-004
  - WSW-20261126-005
---

# Honor bed fits for generator artwork

## Summary

CMYK generator output now follows the global **Fill bed** or **Fit inside**
choice during Preview and Save. Other generator tabs keep their designed 1:1
default, but an explicit fit action is retained for the tab on which it was
made instead of being silently reset.

## Reason

`MainWindow.settings_for_source()` rebuilt every generator source with
`fit_mode="manual"` and `scale=1.0`. The preview fit controls updated the form,
but the next build discarded those values. A processed CMYK page could
therefore remain at its tab scale and be clipped by the red reach warning even
when the operator pressed **Fit inside**.

## Implementation

- `CmykTab` declares `USES_BED_FIT_DEFAULT = True`, so CMYK honors the global
  Fill bed / Fit inside policy and still returns to 1:1 when Manual is chosen.
- The main window remembers explicit auto fits per active generator tab.
  Changing the fit mode back to Manual removes that opt-in.
- Generator pages still default to manual scale `1.0`; only CMYK and tabs with
  an explicit fit request preserve the global auto-fit mode.
- The fit target remains the configured gantry reach. At the restored `180 mm`
  safe default this is a `360 mm` / `14.173-inch` drawable circle. The
  `368.3 mm` / `14.5-inch` stock-limited circle requires the separately
  documented `184.15 mm` reach and a fresh HOME + REGISTER verification.

## Verification

- Focused generator-tab regressions confirm CMYK defaults to Fill bed,
  switching to Fit inside produces scaled outlines inside the configured
  reach, Manual restores 1:1, and an explicit fit does not leak to another
  generator tab.
- The complete generator suite passes `42` tests with one expected
  OpenGL-context skip; the related CMYK, calibration-sheet, and preview modules
  pass `144` tests.
- Complete converter discovery passes `625` tests with one expected
  OpenGL-context skip. Python compilation passes for every changed Python file.

## Struggles and rejected approaches

Applying Fill bed to every generator by default was rejected because most
generator pages use Artwork scale as an intentional physical page dimension.
Updating only the form without changing `settings_for_source()` was rejected
because Preview and Save rebuild settings and would continue to ignore it.

## Risks and follow-up

The current `180 mm` reach keeps a safe margin below the last documented +Y
soft-limit envelope. Do not represent the full 14.5-inch rim-clear circle as
reachable until HOME + REGISTER confirms at least `184.15 mm` and the wider
compensation field has physical verification.

## Files

- `software/generator_tabs/cmyk_tab.py`: CMYK bed-fit policy.
- `software/generator_tabs/README.md`: generator contract for default and
  explicit bed fits.
- `software/qt_svg_to_gcode.pyw`: per-tab explicit fit persistence and source
  settings handoff.
- `software/tests/test_generator_tabs.py`: CMYK and explicit generator fit
  regressions.
- `software/README.md`: current generator fit behavior and safe reach limit.
- `docs/project/ROADMAP.md`: restored-baseline fit handoff status.
