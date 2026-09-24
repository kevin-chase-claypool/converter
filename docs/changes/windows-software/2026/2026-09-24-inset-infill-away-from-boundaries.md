---
id: WSW-20260924-010
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
tags:
  - infill
  - inset
  - boundary
  - correctness
---

# Inset infill away from polygon boundaries

## Summary

The infill region is inset by roughly the pen radius before the lattice is
clipped, so the infill stops just inside the shape boundary instead of bleeding
into surrounding blank borders (e.g. the white border around the SFA letters).

## Reason

The midpoint-based lattice clipping could leave a sub-pen-width overflow along
concave boundaries and even-odd holes, which the user reported as infill
encroaching into the blank border around the letters.

## Implementation

- `geometry.py`: added `FILL_INSET_MM = 0.2` and `_inset_fill_region`, which
  insets outer subpaths inward and holes outward using `inset_polygon_simple`.
- `parse_svg_geometry` threads the inset (scaled like the tolerance) through
  `element_contours` into `fill_region_pattern_contours`.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- SFA logo infill overflow sampling dropped 171 -> 78 outside points (~55%)
  with a 0.2 mm inset; larger insets self-intersect the concave outline and
  were rejected.

## Struggles and rejected approaches

The midpoint clip itself was found to be the source of the slight overflow, but
fixing it exactly for concave/hole polygons is complex; a small inset is a
robust approximation for this non-precision machine. Larger insets were rejected
after they made the overflow worse due to self-intersections.

## Risks and follow-up

The infill now leaves a ~0.2 mm gap inside the boundary. A truly exact clip
for concave/hole polygons would use a spatial index plus sub-segment re-checks;
that remains the proper follow-up if the residual is ever visible.

## Files

- `software/converter_core/geometry.py`: fill-region inset.
