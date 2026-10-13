---
id: WSW-20261013-004
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - tolerance
  - straightness
  - settings
related:
  - WSW-20261013-002
---

# CMYK tab gets its own Path tolerance field

## Summary

The CMYK tab's Screen group now has a **Path tolerance** field (default
**0.15 mm**, range 0.05-1.0). It overrides the main tab's Geometry Tolerance
for this tab's output only, and applies to both the preview and the saved
layer files.

## Reason

Operator observation (2026-10-13): "those values default to .25 when i go to
cmyk". The tab inherited the main Geometry group's Tolerance, which the app
does not persist between launches, so every fresh session emitted CMYK sets at
the 0.25 default even after the operator had used 0.1-0.15 on the main tab.
Tolerance is the budget that keeps each emitted move within a straight line on
the rotating bed (the polar subdivision) - the rows near the bed centre are
where a coarse value shows as curved or drifting dots.

## Implementation

- `cmyk_tab.py`: new `path_tolerance` spinner in the Screen group with a
  tooltip; new `_effective_settings()` applies
  `dataclasses.replace(host settings, tolerance=...)`; the analyze worker and
  the preview cache key both use it, so changing the field invalidates the
  preview correctly.
- No converter-core change: `contours_to_gcode` already consumes
  `settings.tolerance` for the subdivision.

## Verification

- `py_compile` clean; `python -m unittest software.tests.test_cmyk_tab
  software.tests.test_generator_tabs`: 88 tests, OK (1 skipped).
- Bench check: regenerate one layer from the tab and confirm its preamble
  prints `tolerance 0.15` instead of `0.250`.

## Struggles and rejected approaches

Considered lowering the global default instead; rejected because other tools
(the Convert tab's artwork and the SVG sample workflows) were tuned against
0.25 and the operator wants the tighter value for halftones specifically.

## Risks and follow-up

- Lower tolerances add moves (the subdivision only splits the few moves that
  bow); at 0.15 the CMYK file sizes grew modestly in earlier measurements of
  the same mechanism. If a set gets too slow, raise toward 0.25.

## Files

- `software/generator_tabs/cmyk_tab.py`: field, tooltip, effective settings.
- `docs/project/ENGINEERING_LOG.md`: session entry.
