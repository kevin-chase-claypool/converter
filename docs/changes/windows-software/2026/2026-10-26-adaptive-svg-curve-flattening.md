---
id: WSW-20261026-004
date: 2026-10-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
  - software/tests/test_curve_flattening.py
  - software/README.md
tags:
  - svg
  - curve-flattening
  - tolerance
  - gcode-density
  - performance
---

# Flatten SVG curves adaptively within tolerance

## Summary

Replaced the fixed eight-step minimum for every SVG cubic and quadratic curve
with adaptive de Casteljau subdivision. A curve is flattened only until its
remaining control points are within the configured Tolerance of the chord.

On the dense 7,298-path mandala, this reduced planned drawing points from
`560,957` to `60,762` at the same `0.25 mm` tolerance, an `89.2 %` reduction.

## Reason

The old flattener used endpoint distance plus an unconditional eight-step
floor. That made even tiny, nearly straight Bézier segments emit eight `G1`
chords. It also under-sampled a self-loop whose endpoints were equal but whose
control points were far apart.

The saved mandala contained `568,458` motion blocks and `605,725` lines. Source
analysis showed 7,298 SVG paths, 57,026 path commands, and 38,808 cubic
segments. Compensation and rotary planning did not cause the block count.

## Implementation

- `path_to_contours()` now passes the source control points directly for cubic,
  smooth-cubic, quadratic, and smooth-quadratic commands.
- `_append_bezier()` recursively splits a quadratic or cubic at its midpoint
  until every interior control point is within Tolerance of the chord.
- Control-point distance is a conservative bound because a Bézier curve lies
  inside its control-point convex hull.
- The subdivision depth is capped at eight, allowing at most 256 leaf chords
  per source curve.
- The legacy evaluator-only `add_curve()` path retains the previous behavior
  for compatibility.
- `GEOMETRY_VERSION` is now `2.7-adaptive-curves`.

## Verification

- New regression before the fix:
  - 1,000 shallow cubic segments emitted `8,001` points instead of fewer than
    `1,500`.
  - A self-loop cubic exceeded the `0.05 mm` tolerance by about `0.105 mm`.
- New regression after the fix:
  - The shallow sequence emits `1,001` points.
  - Both an asymmetric curved cubic and a self-loop cubic stay within their
    requested tolerance.
- Actual mandala reconstruction at `0.25 mm` tolerance:
  - Parsed source points: `564,510` -> `60,982`.
  - Planned drawing points: `560,957` -> `60,762`.
  - Generated file: `605,725` -> `105,604` lines.
  - File size: `29,060,664` -> `3,595,788` bytes.
  - Maximum measured difference from the previous dense approximation:
    `0.187 mm`, inside the configured `0.25 mm` tolerance.
- The regenerated compensated mandala passes strict motion preflight. Its
  worst commanded bed-path bow fell from `0.758` to `0.421 mm`, and no bare
  rotating `G0` was introduced.
- Full converter discovery passes `551` tests with one expected OpenGL-context
  skip.

## Struggles and rejected approaches

- Using endpoint distance alone cannot detect a loop whose start and end are
  identical. It undersampled that case even with the old eight-step minimum.
- Keeping a smaller fixed minimum would improve typical short curves but would
  still waste points on nearly straight cubics and would not honor Tolerance
  for high-curvature loops.
- Tolerance remains meaningful: a tighter `0.10 mm` setting produces `98,894`
  planned points, while `0.25 mm` produces `60,762`.

## Risks and follow-up

- The eight-level recursion cap preserves a finite output size. A pathological
  curve requiring more than 256 leaves may still be capped rather than fully
  flattening to Tolerance.
- This work is verified by geometry tests and deterministic G-code comparison;
  no new physical print was made. A visual plot check can follow during the
  next normal mandala print.
- Generated G-code changes as expected, so caches or running converter
  instances must be restarted before regeneration.

## Files

- `software/converter_core/geometry.py`: adaptive quadratic and cubic
  flattening, shared distance helper, and geometry-version bump.
- `software/tests/test_curve_flattening.py`: point-density and tolerance
  regressions including a self-loop curve.
- `software/README.md`: current behavior and measured mandala improvement.
