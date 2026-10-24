---
id: WSW-20261023-009
date: 2026-10-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/bed_compensation.py
  - software/tests/test_bed_compensation.py
tags:
  - bed
  - compensation
  - performance
  - algorithm
  - subdivision
related:
  - WSW-20261023-007
  - ADR-009
---

# Add an adaptive bed-compensation curvature probe

## Summary

Exact bed-compensation planning now uses four points for its initial
curvature check. If the sampled deviation is at most one quarter of the active
Tolerance, the segment immediately uses one subdivision. Otherwise, the
original 16-point probe runs unchanged.

## Reason

Profiling the exact CMYK preview showed that `interpolate_bed_correction`
consumed `9.8 s` of an `11.3 s` move-building sample. The fixed probe evaluated
16 corrected positions for every source segment even though almost every
segment required no extra compensation subdivision.

Across 15,694 segments sampled from the full 8699-contour field, four points
and sixteen points produced identical step counts. A deliberately varying
synthetic field also showed that simply lowering the global sample count is
unsafe, so the fast path retains a full fallback.

## Implementation

- Added a four-point curvature probe with a fast-exit threshold of
  `0.25 * tolerance`.
- Segments above that threshold run the full 16-point probe and use its
  original step calculation.
- Added `adaptive=False` to the compensation probe as a fixed-sample oracle
  for regression tests and future algorithm comparisons.
- Existing G-code coordinates, correction values, 5 mm bound, and 600-step
  subdivision limit remain unchanged.

## Verification

- Real-field sampled benchmark: 15,694 segments across the 8699-contour CMYK
  preview produced the same total step count (`15,704`) and zero per-segment
  mismatches. Probe time fell from `8.838` to `2.673 s`, a `3.31x` speedup.
- A 100-contour exact compensated move build fell from `4.891` to `2.423 s`,
  a `2.02x` end-to-end speedup for that slice; both produced 7,871 moves.
- A 5,000-segment synthetic varying-field check had zero missed subdivisions
  at 0.25-of-tolerance thresholds across three tolerances. A smaller committed
  200-segment regression plus explicit flat and fallback tests protect the
  behavior.
- The full converter suite passes `494` tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Changing the global sample count from 16 to 4 was rejected because a
  sharply varying field can hide curvature between coarse samples.
- Returning after the coarse probe without a conservative margin was rejected
  because it would consume too much of the path tolerance on near-threshold
  segments.
- Replacing the local-affine field with a coarse lattice lookup was deferred;
  it needs its own interpolation-error validation and profile-load strategy.

## Risks and follow-up

- The four-point early exit is still a sampled method. The 75 % unused
  tolerance margin and 16-point fallback make it conservative, but a
  pathological field could place all material curvature between the sampled
  points. Future profiles should continue to run the varying-field regression.
- Exact planning remains dominated by the repeated local-affine interpolation
  in fallback segments and emitted points. A triangulated surface or verified
  lookup table remains the next algorithmic opportunity.
- A complete dense save has not yet been profiled end to end after this
  optimization; the recorded benchmark isolates walk planning and a
  100-contour slice.

## Files

- `software/converter_core/bed_compensation.py`: adaptive probe and fixed-probe
  comparison path.
- `software/tests/test_bed_compensation.py`: flat fast-exit, varying fallback,
  and randomized equivalence coverage.
- `software/README.md` and `docs/project/ROADMAP.md`: current behavior,
  measured gains, and remaining optimization work.
