---
id: WSW-20261006-030
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/vector_trace_tab.py
tags:
  - generators
  - bug-fix
  - vector-trace
related:
  - WSW-20261006-029
---

# Fix Vector Trace closed loops collapsing to invisible paths

## Summary

Vector Trace's default **Outlines** mode produced no visible preview: every
traced contour collapsed to a two-point path where both points were the same
location. Closed loops are now simplified correctly and the preview draws the
outline.

## Reason

The owner reported "shows no preview when I hit preview" with a photo loaded.
Reproducing with the same image showed 55 paths, each with exactly two
identical points.

## Implementation

- `vector_trace_tab.py`: new `_simplify_closed()` splits a closed loop at the
  point farthest from its start and simplifies each half with Douglas-Peucker,
  because the open-path algorithm treats every point as collinear when the
  path's endpoints coincide. The smoothed loop is explicitly closed again
  before it becomes an SVG polyline.
- `software/tests/test_vector_trace_tab.py`: the outline test now asserts the
  path has more than four points, which the degenerate two-point result fails.

## Verification

- Reproduced with `C:\Users\jacks\Downloads\IMG_0514.JPG`: before the fix,
  55 paths / 110 points (2 per path); after the fix the same image traces
  proper multi-point loops.
- `python -m unittest discover -s software\tests -p "test_vector_trace_tab.py" -v`
  -> 5 tests pass.
- Full suite: `python -m unittest discover -s software\tests` -> 318 tests
  pass.

## Struggles and rejected approaches

- Removing the explicit closure before simplification was considered, but a
  plain Douglas-Peucker still degenerates on a closed loop; splitting the loop
  is the correct fix.

## Risks and follow-up

- Photos traced at Otsu produce many small contours; raise **Min area** to
  clean specks, or use a logo/silhouette image for the intended result.

## Files

- `software/generator_tabs/vector_trace_tab.py`: closed-loop simplification.
- `software/tests/test_vector_trace_tab.py`: regression assertion.
