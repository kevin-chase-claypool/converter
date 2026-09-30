---
id: WSW-20260930-008
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
  - WSW-20260930-007
  - software/README.md
---

# Kaleidoscope: complex multi-layer random patterns

## Summary

Maximum intricacy was raised again, far beyond the previous upgrade: a
level-10 pattern in a 12-division, 181.3 mm frame now draws about 13,500
mirrored contours and 310,000 points (roughly 390,000 G-code lines and 13,500
pen cycles) instead of about 4,000 contours and 96,000 points. The added
complexity is structural, not just darker: spacing-driven contour fills inside
every shape, nested sub-shapes, three new dense families (diamond mesh, lace
scales, bead rows), separator bundles, stud flowers and dot rows between rings,
and a layered centre.

## Reason

The operator's first sentence after seeing the previous maximum was that they
were still not impressed and that it "needs to be way more complicated". The
reference artwork is a 9,045-path engraving; matching that kind of complexity
needs many layers of small elements, which meant changing how counts are
chosen, not only raising a few constants.

## Implementation

- `converter_core/generative.py`:
  - Counts are now *spacing-driven*: `_count(length_mm, spacing_mm)` places
    contour fills, studs, dots, barbs, scale rows and hatch lines one every few
    millimetres along the arc or across the band, so the drawing gets more
    complicated wherever there is more room. Spacings tighten with intricacy
    (for example contour fills run from 2.4 mm to 1.2 mm).
  - Shape rings are `leaf` (sub-leaves, contour fills and a vein), `tulip`,
    `lens`, `bundle`, `feather` (forked barbs and tip beads), `scallop`,
    `chevron`, `rays`, plus the new `mesh` (two crossing families of slanted
    strokes), `lace` (offset rows of overlapping scale arcs with bead eyes) and
    `beadrow` (several rows of beads and stud flowers).
  - `random_pattern` now lays out `3 + (2 * intricacy) // 3` shape rings (3-9),
    a separator bundle of up to eight lines after every ring, stud rows on every
    gap, and a rim with several concentric lines, a stud row and a dot row.
  - The centre is a layered stack: nested rosette leaves inside two rings, bead
    dots between them, and a ray ring whose spokes start at half the rosette
    radius so the `2 * divisions` mirrored copies stay apart.
- `software/tests/test_generative.py`: the density floor now requires at least
  400 wedge contours, 10,000 wedge points and 9,000 mirrored contours at
  level 10, and the intricacy test asserts that the amount of drawing (points)
  grows at every step.

## Verification

- Seed 4 / intricacy 10 / 12 divisions / 181.3 mm: 13,488 mirrored contours,
  308,232 points; headless Qt build 0.55 s, preview paint 0.38 s,
  `plan_program` 13.3 s, emit 5.9 s, 391,320 G-code lines, 13,680 pen cycles,
  max radius exactly 181.30 mm.
- Seed 11 reaches 15,480 mirrored contours, so the floor in the test is
  conservative rather than seed-specific.
- Monotonicity checked across seeds 0, 4, 7, 11 and 33: points rise at every
  step (for example seed 11: 7,093 -> 7,347 -> 9,014 -> 13,370 for levels
  1/4/7/10). Contour counts can dip slightly when a level adds rings but thins
  the bands, so the test asserts points, not contours, and only requires the
  final level to exceed the first in contour count.
- All ten test modules pass. Visual checks: `samples/png/gen_progression.png`
  (levels 4/7/10), `gen_complex_tuned.png` (two seeds at level 10) and
  `gen_preview_complex2.png` (app preview).
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- The first spacing pass was too dark: the mesh and lace families at 2-3 mm
  spacing turned whole bands into solid black under `2 * divisions` mirroring.
  Mesh spacing was widened to 3.2 mm at level 10 and lace rows to 2.9 mm, and
  separator bundles were tightened to 0.8 mm so they read as cords rather than
  filling the gap.
- Bead eyes used to sit on the outer edge of a scale and poked 1.5 mm past the
  band; the eyes and feather tip beads are now pulled inside by their own radius,
  which the band test caught.
- The previous "intricacy never loses a contour" rule proved too strict once
  higher levels split the same radius into more, thinner rings: the guarantee
  that matters is that the *drawing* grows, which is what the test now asserts.

## Risks and follow-up

- Level 10 is a genuinely long plot: 391k G-code lines and 13,680 pen cycles,
  with about twenty seconds to plan and emit. There is still no line-count or
  plot-time warning in the UI.
- The preview repaint takes a few hundred milliseconds; dragging the image at
  level 10 will feel heavier than at low levels.
- The design remains tied to its division count: shape rings are composed for
  the current wedge.

## Files

- `software/converter_core/generative.py`: spacing-driven counts, eleven shape
  families, separator/stud/dot dressing, layered centre and rim.
- `software/tests/test_generative.py`: higher density floor, points-based
  monotonicity.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
