---
id: WSW-20260930-003
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/geometry.py
  - software/tests/test_fill_source.py
tags:
  - infill
  - correctness
  - defaults
  - fill-regions
related:
  - WSW-20260930-002
  - docs/HANDOFF.md
---

# Default to outlines only and fill only genuinely closed loops

## Summary

`Fill spacing mm` now ships as `0` (outlines only), and the fill generator only
accepts a contour as a fill region when that contour actually closes. Open
subpaths are no longer implicitly closed and filled.

## Reason

The 2026-09-30 mandala print showed short stray marks - "random dashes" - in the
white space of the artwork. Reproducing the file from its source SVG
(`1013896_OJ8XYA1.svg`, fill 4 mm, tolerance 1, four shade levels, Fit inside)
matched `mom.gcode` to within 0.01% and attributed them: the 4 mm fill adds
2,806 fragments of 3 mm or less, where the same build at spacing `0` adds none.
The fill was hatching the interiors of the artwork's small closed shapes, and
the operator had always run this artwork at `0`.

Two separate problems were worth fixing rather than only resetting the setting:

- Fill was on by default, so a line-art conversion silently added fill geometry
  the operator did not want, and it had to be zeroed every session because
  settings are not persisted.
- Of 10,704 fill regions, 338 were *open* subpaths. An SVG fill implicitly
  closes an open subpath, but this plotter draws only the ink in the file, so
  that implicit chord is a boundary the pen never draws and the fill reads as
  marks in blank space.

## Implementation

- `settings.py`: `hatch_spacing_mm` default `4.0` -> `0.0`, with the UI default
  and tooltip updated.
- `geometry.py`: the visible-fill branch now uses `closed_outline_regions`
  (closed within the closure tolerance, at least four points, non-degenerate
  area) instead of accepting any contour with three or more points, so filled
  and stroke-only elements follow one rule: only a loop the pen closes may be
  filled.
- `software/README.md` and `docs/HANDOFF.md` describe the new default and the
  closure rule.

## Verification

- All eight test modules pass. `test_fill_source.py` now asserts the `0` default
  and that a closed filled path still hatches while the same path without its
  closing `Z` is not filled.
- On the operator's source SVG: spacing `0` -> 5,448 contours, 0 fill contours,
  0 fill fragments; spacing `4` -> 8,545 contours, 3,097 fill (197 fewer open
  regions than before) and 2,614 fill fragments.
- `python tools\docs_index.py --write/--check` pass.

## Struggles and rejected approaches

An earlier response told the operator to set fill spacing to 4 mm, which caused
the dashes; that advice is corrected here. Reducing only the shade levels or
raising the spacing was rejected as the fix because neither addresses the open
subpath regions, and neither stops a future session from re-enabling fill
accidentally.

## Risks and follow-up

- Artwork that relied on the old default for a filled look now needs an explicit
  spacing. Tone artwork with an embedded image or gradient still gets a 4 mm
  starter from the app's auto-configuration, because outlines only would draw
  nothing for a photo.
- A genuinely filled, deliberately *open* path now stays unfilled. That is the
  intended pen-plotter behaviour but is a deliberate deviation from SVG's
  implicit-closure rule, so it is recorded here.
- Fill fragments inside real closed shapes remain possible when the spacing is
  coarse relative to the shape; that is a spacing choice, not a defect.

## Files

- `software/converter_core/settings.py`: outlines-only default and tooltip.
- `software/converter_core/geometry.py`: closed-loop requirement for fill
  regions.
- `software/tests/test_fill_source.py`: default and closure tests.
- `software/README.md`, `docs/HANDOFF.md`: current behavior.
- `docs/project/ENGINEERING_LOG.md`: dated entry for this session.
