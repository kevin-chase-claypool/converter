---
id: WSW-20260905-007
date: 2026-09-05
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/gcode.py
  - software/qt_svg_to_gcode.pyw
tags:
  - preview
  - performance
  - motion-planning
related:
  - WSW-20260905-006
---

# Share the preview motion plan

## Summary

Removed the repeated contour/theta planning pass introduced when the preview
was changed to show the complete G-code program.

## Reason

Preview first built graphics moves, then independently regenerated the same
motion plan to populate the exact command list. Large or theta-heavy artwork
therefore incurred the costly planning work twice.

## Implementation

`plan_program()` now creates the clipped contour and theta-plan result once.
The preview worker passes that result to both preview-move generation and
complete G-code emission. Standalone conversion APIs retain their existing
behavior by creating a plan when one is not supplied.

## Verification

- `python -m unittest discover -s software\tests -v`
- `python -m py_compile software\qt_svg_to_gcode.pyw software\converter_core\gcode.py`
- `git diff --check`

## Struggles and rejected approaches

Parsing emitted G-code back into preview geometry was rejected because it would
add a second representation of the same coordinate and theta semantics. Shared
planning preserves one source of truth.

## Risks and follow-up

The calculation is no longer duplicated, but the total preview time still
depends on artwork complexity, clipping, fill generation, and the one required
theta solve. Controller-time validation remains gated by M-06.

## Files

- `software/converter_core/gcode.py`: shared motion-plan API.
- `software/qt_svg_to_gcode.pyw`: use one plan for preview and command list.
- `software/tests/test_theta_feed.py`: shared-plan parity coverage.
- `software/README.md`: describe preview planning behavior.
