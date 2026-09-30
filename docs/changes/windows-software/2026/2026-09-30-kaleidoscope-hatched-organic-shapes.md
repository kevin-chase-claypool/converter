---
id: WSW-20260930-018
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - generative
  - style
related:
  - WSW-20260930-017
  - software/README.md
---

# Kaleidoscope: hatched, organic shapes in the drawn pattern generator

## Summary

The operator's reference mandala (`1013893_OJ8XY61.svg`, 9,045 paths) is built
from hand-drawn leaves and petals that are **hatched inside** - striped
shading, irregular outlines, layered rings, dotted rows. The generator's shape
rings now do the same: leaves carry radial ribs and contour lines inside an
irregular outline, so a level-9 design reads as a drawn, shaded mandala rather
than a set of empty mechanical rings. Seeds still reshape the whole design.

## Reason

"this svg is a good example of what i ultimately want the kaleidoscope.bat to
do. i just want it to be more random than this." Earlier attempts added line
*quantity* (bands, meshes, dot rows) but not the reference's *style*: every
shape there is a drawn leaf with internal hatching.

## Implementation

- `converter_core/generative.py`:
  - `_leaf_profile(t, power, seed)` returns a leaf's half-width with two
    normalised low-frequency ripples layered on the mathematical teardrop, so
    outlines are irregular but smooth and never exceed the band.
  - `_leaf_ring` was rebuilt around it: an irregular closed outline (outer and
    inner edge), nested interior arches, contour lines following the leaf's
    length, radial ribs across it at 2-4 mm spacing, and a centre vein. The
    ribs are what read as engraved botanical hatching.
  - Spacings are tuned so the hatched shapes stay open: ribs 5.6 - 0.26 * level
    mm apart, interior contours 3.6 - 0.18 * level mm, both scaled by the
    seed's packing density.
- Nothing else moved: motif mode, bounds, persistence and the planner are
  untouched, and this turn deliberately made no path changes.

## Verification

- Core render through the real mirror step (`samples/preview/gen_hatched3.png`):
  seed 3 / intricacy 9 gives 447 wedge contours -> 10,728 mirrored; seed 17
  gives 285 -> 6,840, with visibly different layouts.
- The leaf families pass the existing band test (every point inside
  `r_in..r_out` and the wedge) - the wobble is normalised precisely so the
  irregular outline cannot escape its band.
- All eleven test modules pass.
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- The first hatched pass was too dense: ribs at 1.4 mm with 12+ contour lines
  filled the leaves solid. Spacings were opened up so the paper shows between
  strokes.
- Normalising the wobble by its peak was necessary: an unnormalised ripple
  pushed leaf tips past the band and tripped the family bound test.
- A previous attempt at this style (concentric shading bands between rings)
  painted heavy black rings and was removed; putting the hatching *inside* the
  shapes is what works.

## Risks and follow-up

- Levels 9-10 are dense plots: about 10,700 mirrored contours in the sample.
  Lower levels stay airy.
- Only the leaf family carries ribs so far; tulips, lenses and bundles still
  use plain contour shading and could take the same treatment.
- The motif library is unchanged and still the source of the "realistic shapes"
  question; engraving-style artwork remains the obvious upgrade once the folder
  paths are settled.

## Files

- `software/converter_core/generative.py`: `_leaf_profile` and the rebuilt
  `_leaf_ring`.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
