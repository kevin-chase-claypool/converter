---
id: WSW-20260930-007
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - generative
  - pattern-generator
  - density
related:
  - WSW-20260930-006
  - software/README.md
---

# Kaleidoscope: engraving-density random patterns

## Summary

The generator was rebuilt from a handful of texture bands into an engraved
mandala composition: shape rings filled with nested contour lines, separator
rings carrying flower studs, a rayed centre and a scalloped beaded rim.
Intricacy 10 in a 12-division, 181.3 mm frame now draws about 4,000 mirrored
contours / 96,000 points (about 120,000 G-code lines) instead of roughly 1,200
contours, and the *style* of the extra detail changed with it - shading inside
shapes rather than more empty rings.

## Reason

The operator was not impressed by the maximum intricacy of the first generator
and supplied a 9,045-path Illustrator mandala as the target: "i want a lot more
going on". Rendering that reference showed what it actually consists of -
large leaf shapes with nested line shading, rows of small flowers, striped
fan/feather areas, and a fine rayed centre - so the fix was both more elements
and a different vocabulary.

## Implementation

- `converter_core/generative.py` was recomposed around *shape rings*:
  - Families are now `leaf` (one shaded leaf per wedge), `tulip` (a tall centre
    lobe between two side lobes), `lens` (two arcs of different bulge crossing
    at the seams), `bundle` (nested topographic arches), `feather` (a spine with
    radial barbs), `scallop`, `chevron` and `rays`. Every family rests on its
    band edges and reaches both seam angles, so the mirrored copies join into
    continuous rings.
  - Shading counts scale with intricacy: nested fills inside leaves and tulips,
    more barb lines in feathers, more nested arches in bundles, up to four
    scallop lines.
  - `random_pattern` lays out `2 + intricacy // 3` shape rings on a geometric
    radius ladder, places 2-4 line separator rings between them, adds flower
    studs on alternating separators, and finishes with the scalloped rim, its
    double ring and its stud ring.
  - The centre is a shaded rosette plus a ray ring whose spokes start at half
    the rosette radius, with tight rings at 0.50 and 0.72 of it.
- Removed the first draft's `wicker`, `beads`, `hatch`, `scales` and `sawtooth`
  bands: as whole-band textures they read as scribble rather than engraving.

## Verification

- `software/tests/test_generative.py` gained `test_top_intricacy_is_dense`
  (>= 120 wedge contours, >= 3,000 wedge points, >= 3,000 mirrored contours)
  and its chord regression now distinguishes a stray *diagonal* chord from
  deliberate radial spokes and circle facet edges. All nine tests pass, and all
  ten test modules pass.
- Headless Qt at seed 4 / intricacy 10 / 12 divisions / 181.3 mm: build 0.11 s,
  4,056 contours, 96,096 points, max radius exactly 181.30 mm, `plan_program`
  2.25 s, emit 1.85 s, 120,460 G-code lines, 4,056 pen cycles.
- Visual checks through the real mirror step: `samples/png/gen_dense4.png`
  (levels 5/8/10), `gen_l10.png` (level 10 detail) and `gen_div.png`
  (8 and 24 divisions) - rings of shaded shapes, stud rows, scalloped rim and a
  clean rayed centre with white space at the middle.
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- The first density attempt kept the old texture families and simply added more
  bands. It produced visual noise, and the centre became an inked blob: with
  `2 * divisions` mirrors, starburst spokes that reached to 0.10 of the rosette
  radius overlapped to a solid disc. Moving the spokes out to half the rosette
  radius and cutting them to 3-5 per wedge fixed it.
- A skewed hatch family was tried as engraving texture and rejected in favour of
  the `feather` (spine + radial barbs) and leaf-ring (nested interior contour)
  treatments, which look deliberate rather than scribbled.
- `_leaf`'s shading lines and the tulip's window are clamped to the lobe that
  owns them, so shading cannot leak into a neighbouring lobe.

## Risks and follow-up

- Max intricacy is deliberately a long plot (about 120k G-code lines, 4,056 pen
  cycles). There is still no warning when the chosen intricacy will take hours.
- A design remains tied to its division count: the shapes are composed for the
  current wedge, so changing `Divisions` produces a different drawing.
- The result is more regular than the hand-drawn reference; organic jitter and
  more shape families remain open enhancements.

## Files

- `software/converter_core/generative.py`: shape-ring composition, shading,
  separators, studs, scalloped rim and rayed centre.
- `software/tests/test_generative.py`: density test and refined chord test.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
