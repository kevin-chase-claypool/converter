---
id: WSW-20260927-003
date: 2026-09-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
tags:
  - converter
  - fill
  - hatch
  - inset
  - clipping
  - correctness
related:
  - WSW-20260927-002
  - WSW-20260927-001
---

# Apply the fill bleed margin by pulling back clipped passes

## Summary

Hatch is now clipped to the fill region exactly as drawn, and the bleed margin
is applied afterwards by shortening the ends the clip created. Ink can no longer
land outside the fill region. The per-subpath region offset that produced the
margin has been removed.

## Reason

Vector shading on a bitmap-traced artwork put 3,342 of 10,518 hatch endpoints
outside the fill region, some by 10.3 mm. Measured against the true even-odd
region:

| | area |
|---|---|
| true fill region | 10,110 mm² |
| region the clipper was given | 7,400 mm² (73.2%) |
| area added outside the fill | 1,337 mm² (13.2%) |
| area removed | 4,047 mm² (40.0%) |

The clipping itself was correct - every endpoint sat inside the region it was
handed. The region was wrong.

`_inset_fill_region` offset every subpath independently and chose the direction
from a centroid-containment guess (`outer shrink, holes grow`). That is valid
only when subpaths are disjoint or strictly nested, which is the classic
outer-ring-plus-holes structure. A bitmap trace is thousands of mutually
overlapping subpaths, so the guess carries no information there, and offsetting
each subpath independently cannot preserve even-odd parity at all: growing one
subpath flips parity in the ring around it and shrinking another flips parity
elsewhere. With 4,875 overlapping subpaths those errors compounded.

The alternative explanation was ruled out by measurement: a nonzero winding
test was implemented and, of 120 endpoints that even-odd called outside, **0**
were inside by nonzero winding. The converter was not using the wrong fill rule.

## Implementation

`software/converter_core/geometry.py`:

- `fill_region_pattern_contours` no longer offsets the region. It passes
  `fill_inset` to the line-family clip calls as a pull-back margin.
- `clip_segment_to_region` gained `pull_back`. After deciding which sub-intervals
  are inside the region, it shortens an end only when that end was created by
  the clip (`t0 > 0` or `t1 < 1`), and drops a pass that no longer has length.
  Because it starts from the true region, shortening is the only operation
  available - a pass can never be moved outward.
- `line_region_contours` gained `pull_back` and forwards it.
- `_inset_fill_region` was removed. `inset_polygon_simple` remains in use by
  `concentric_region_contours`, which insets progressively by design.

The margin is now measured along the pass rather than perpendicular to the
boundary, so a pass meeting the boundary at a shallow angle clears it by
`margin * sin(angle)` rather than by `margin`. That is a smaller margin in the
worst case, not an overshoot.

## Verification

- `F15_cutaway_black_white_clean_vector.svg`: hatch endpoints outside the true
  fill region `3342 / 10518` → **`0 / 4440`**. Geometry stage 1.83 s → **1.54 s**,
  so the fix removes work rather than adding it.
- Well-behaved artwork is barely affected. Total hatch length per sample:
  `kindergarten-house-sun`, `m06-xy-theta-lettering`, and
  `us-constitution-preamble-single-line` are unchanged; `center-magnet-raster-math`
  and `raster-shading-math` move by +0.04%; `stripe_stroke_test` +0.4%;
  `spirit-logo-purple-rgb` -0.25%.
- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 37
  tests. Two new cases assert that a pulled-back pass always stays inside the
  fill region and that pulling back only ever shortens.
- `python -m py_compile software\qt_svg_to_gcode.pyw` passes.

## Struggles and rejected approaches

- The first containment check compared scaled output against unscaled polygons
  and reported everything outside; the two coordinate spaces had to be matched
  before the measurement meant anything.
- Keeping the offset for artwork where the centroid guess is valid, and falling
  back only when a self-check detects a corrupted region, was rejected. Detecting
  it soundly means comparing two even-odd regions, which costs more time than
  the fix, and the fallback would still leave two behaviours to maintain.
- Extending the same margin treatment to the tile and mark patterns was left
  alone. They test the region rather than clipping a pass, so a mark near the
  boundary can still touch it. That is unchanged in kind from before, and it is
  recorded as follow-up.

## Risks and follow-up

- Shape patterns (`dots`, `circles`, `diamonds`, `triangular`, `hexagonal`) and
  `waves`/`gyroid`/`concentric` no longer benefit from a boundary margin at all,
  because the margin was previously carried by the offset region they shared.
  Their marks are placed against the true region, so they stay inside it, but a
  mark can touch the outline. If that shows up in a plot, the fix is to test the
  mark's extremities rather than its centre.
- Fill output changed for every file, by design. The sample comparison above
  bounds that change for well-behaved artwork; artwork with overlapping or
  traced subpaths changes substantially, and for the better.
- Tone will look different wherever the previous region was corrupted, so the
  first plot after this change should be judged from scratch rather than against
  the previous one.

## Files

- `software/converter_core/geometry.py`: pull-back margin, inset removed.
- `software/tests/test_fill_spatial_index.py`: containment and shortening cases.
- `software/README.md`: documents where the margin is now applied.
