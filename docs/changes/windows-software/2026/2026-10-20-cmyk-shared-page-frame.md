---
id: WSW-20261020-001
date: 2026-10-20
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/gcode.py
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - alignment
  - planning
  - artwork-scale
  - calibration
related: []
---

# CMYK: one shared page frame for all four ink programs

## Summary

The CMYK preview and the four saved per-ink programs now share one page
frame: every layer is planned around the **page centre**, not around its own
ink coverage. The Artwork scale control therefore changes the printed size
without changing overlay - the four passes stay co-registered at any scale,
with or without the corner crosses.

## Reason

The 2026-10-20 diagnosis showed each ink was written to its own SVG and
planned separately; `plan_program` recentered every file on its own contour
bounding box. Different ink coverage meant different centres, so the passes
landed tens of millimetres apart (47 x 49 mm on an asymmetric test image at
100 % scale, 132 x 137 mm at the shipped 280 % scale). The corner crosses
could not rescue larger scales because the scaled ink extends past them.
The operator needs the Artwork scale control, so "print at 100 %" was not an
acceptable workaround.

## Implementation

- `converter_core/settings.py`: optional `frame_center_mm` anchor (validated
  as a finite pair). `None` keeps the single-artwork default: center the
  artwork's own bounding box.
- `converter_core/gcode.py`: `plan_program` uses the frame anchor as
  `source_center` when set, so clipping, recentering and placement are
  identical for every layer in that frame.
- `generator_tabs/cmyk_tab.py`: `apply_tab_settings` sets the frame to the
  page centre (scaled by `settings.scale`), so the preview,
  `_effective_settings()` analysis and all four saved programs inherit it.
  The calibration sheet uses the same hook.
- `converter_core/gcode.py`: the program header now records
  `(frame center …, bed motion …)`, so a saved file states which frame and
  kinematics produced it. Pre-fix CMYK saves read `frame artwork bbox`.

## Verification

- Reproduction (asymmetric quadrant image, page 200 mm, margin 6 mm, GCR
  95 %, Artwork scale 280 %, corner crosses **off**): before the fix the four
  layer anchors spread 131.61 x 137.21 mm; with the shared page frame they
  all land at x = 100.00, y = 100.00 mm (0.00 x 0.00 spread).
- New `test_artwork_placement.py` case: two different contour sets with one
  frame anchor report the same `source_center` and land at the offsets the
  frame implies.
- New `test_cmyk_tab.py` case: with a full-ink asymmetric image at 280 %
  scale and crosses off, all four layer programs report the page centre as
  their anchor; switching to 100 % keeps the shared frame and shrinks the
  drawn radius (scale still works).
- Full suite: 423 tests pass (1 skipped).

## Struggles and rejected approaches

- Corner crosses as the only anchor: verified to fail for scales above about
  105 % (82 x 82 mm residual at 280 %), because scaled ink extends past the
  crosses.
- Forcing Artwork scale to 100 % and sizing via the page: rejected - the
  operator needs the scale control to work.
- Comparing the four ink bounding boxes to build a union frame was rejected:
  it couples the frame to content and changes when any one ink changes;
  the page is the stable multi-pass frame.

## Risks and follow-up

- Existing CMYK jobs will land relative to the page centre instead of each
  ink's centre; that is the intended correction, but a bench print of the
  four corner crosses is still the acceptance check for the remaining
  machine-level registration (P100 centre, A slip).
- Single-file conversions (Convert tab and other generators) keep their
  current bbox-centered placement; only CMYK opts into the shared frame.

## Files

- `software/converter_core/settings.py`: `frame_center_mm` field + validation.
- `software/converter_core/gcode.py`: planner honours the frame anchor.
- `software/generator_tabs/cmyk_tab.py`: page-centre frame for all CMYK paths.
- `software/tests/test_artwork_placement.py`, `software/tests/test_cmyk_tab.py`: regression tests.
- `software/README.md`: document the shared frame and scale behavior.
- `docs/project/ENGINEERING_LOG.md`, `docs/project/ROADMAP.md`: records.
