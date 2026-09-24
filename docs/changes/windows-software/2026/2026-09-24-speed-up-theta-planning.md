---
id: WSW-20260924-001
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core
tags:
  - performance
  - theta
  - preview
---

# Speed up the parse/preview pipeline by removing duplicate theta candidates

## Summary

The axis-locked theta candidate generator no longer returns 17 identical winding
copies of each root. The parse + preview path is roughly 4x faster as a result.

## Reason

Profiling the converter's load/plan/preview path showed theta planning was
roughly 85% of the time, concentrated in `axis_locked_theta_candidates`. It
looped `k` from -8 to 8, adding full revolutions to each principal root and then
calling `unwrap_angle(base + k*360, reference)` — which collapses every copy to
the same representative of `reference`. So `candidate_cost` was evaluated ~17
times per root on duplicates that could never win a different cost.

## Implementation

- `kinematics.py`: `axis_locked_theta_candidates` now returns each principal
  root unwrapped once instead of 34 near-duplicates.

The chosen theta is unchanged: the redundant candidates had identical cost, so
the minimum is the same. Output geometry and emitted G-code are unaffected.

## Verification

- `raster-shading-math.svg`: wall-clock parse/plan/preview 0.049 s -> 0.012 s;
  cProfile total 0.205 s -> 0.057 s; `candidate_cost` calls 33,152 -> 1,952.
- A synthetic 2,000-contour file parses in ~0.46 s.
- `test_coordinate_frames.py` (3) and `test_theta_feed.py` (19) pass.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

The remaining time on very large files is the contour-ordering heuristic
(`planned_contours` grid/ring search and 2-opt), which is structural rather than
a single redundant loop; it is left as follow-up rather than reworked blindly.

## Risks and follow-up

Low risk — this removes provably redundant work and does not change results. If
very large artwork still previews slowly, the next target is the
traveling-salesman ordering and the duplicated theta planning between the
ordering pass and `plan_program`.

## Files

- `software/converter_core/kinematics.py`: deduplicate axis-locked theta candidates.
