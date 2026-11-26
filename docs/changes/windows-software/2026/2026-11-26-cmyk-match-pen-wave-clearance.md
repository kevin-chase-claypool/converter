---
id: WSW-20261126-008
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - wave-screen
  - pen-clearance
  - dot-pitch
  - preview
  - error-message
  - regression
related:
  - WSW-20261126-006
  - WSW-20261126-007
---

# Make Match pen satisfy Wave clearance

## Summary

CMYK **Match pen** now accounts for the Wave screen's required `0.25 mm` edge
gap. At the screenshot configuration (`0.90 mm` pen, `80 %` Artwork scale), it
sets the pitch so the final on-paper row clearance is `1.15 mm` instead of
only `0.90 mm`. Preview build failures now use a truthful **Preview failed**
dialog title.

## Reason

The Wave screen correctly rejects adjacent rows whose edge clearance is below
the pen width plus `WAVE_MIN_EDGE_GAP_MM`. **Match pen**, however, always set
the on-paper pitch to exactly one pen width. Clicking the apparent recovery
action therefore reproduced the same warning and prevented the preview from
rebuilding.

The host reported every build exception through the title **Preview needs
artwork**, even when artwork was present and the actual failure was a screen
geometry constraint.

## Implementation

- Added the tab's active pen-clearance calculation. Ordinary screens retain a
  one-pen-width target; Wave, equidistant-Wave, and legacy Wave diagnostics add
  the converter-owned `0.25 mm` edge gap.
- **Match pen** divides that final-paper clearance by Artwork scale and reports
  the resulting on-paper clearance in the status line.
- The effective-pitch readout now identifies values below pen clearance,
  exactly at clearance, or separated by a gap.
- General Preview build failures are shown as **Preview failed**.

## Verification

- Focused tests verify the unchanged ordinary-screen target, the Wave
  `0.90 mm + 0.25 mm` target at `80 %`, and a complete CMYK preview build from
  that matched setting.
- A screenshot-state regression also confirms **Fit inside** contains the
  matched page within the configured reach.
- The complete CMYK and generator modules pass `151` tests with one expected
  OpenGL-context skip. Complete converter discovery passes `631` tests with
  one expected OpenGL-context skip, and Python compilation passes.

## Struggles and rejected approaches

Suppressing the Wave clearance error was rejected because it would permit
overlapping rows. Adding the edge gap to every screen style was also rejected
because only Wave rows require that separation policy.

## Risks and follow-up

The reach warning is a separate condition. Use **Fit inside** to contain the
full page within the configured `180 mm` safe reach; **Fill bed** intentionally
allows the four bounding-box corners to extend beyond the circular drawable
area.

## Files

- `software/generator_tabs/cmyk_tab.py`: Wave-aware Match pen and pitch status.
- `software/qt_svg_to_gcode.pyw`: accurate Preview failure dialog title.
- `software/tests/test_cmyk_tab.py`: clearance target and preview-build
  regressions.
- `software/README.md`: current Match pen behavior.
