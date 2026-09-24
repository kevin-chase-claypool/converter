---
id: WSW-20260924-004
date: 2026-09-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/kinematics.py
tags:
  - performance
  - theta
  - planner
---

# Eliminate duplicate theta planning during contour ordering

## Summary

The contour-ordering pass no longer runs a full theta simulation to estimate
each contour's exit state. It uses the entry theta plus the final-segment
tangent as a cheap estimate, and the full theta plan is now computed exactly
once, in final order, by `plan_program`. Theta-planning work drops by roughly
half, and planning is about 1.3x faster, with a measured travel penalty under
0.5%.

## Reason

`planned_contours` called `plan_contour_thetas` inside `simulate_contour_exit`
for every contour it picked, purely to chain `previous_theta`/`previous_machine`
into the next contour's entry cost. The 2-opt pass then reordered the contours,
which invalidated that chain, so `plan_program` had to recompute the same thetas
again in final order. Net effect: theta planning ran about twice per contour.

## Implementation

- `kinematics.py`: `simulate_contour_exit` now computes `first_theta` via the
  existing `first_segment_theta` and estimates the exit with a new
  `_last_segment_theta` (final-segment tangent unwrapped near the entry theta)
  instead of a full `plan_contour_thetas` walk.
- `kinematics.py`: `candidate_cost` defers the smoothness/round-bias lookups to
  the tangent-bearing resolvers, which the hotter r-theta path never uses.

## Verification

- `python -m unittest discover -s software/tests -p "test_*.py"`: 22 tests pass.
- On `raster-shading-math.svg` (triangular fill, scale 0.2), the drawn bed-frame
  segments are identical before and after (5900 segments, exact set match);
  `plan_program` drops from 120 ms to 88 ms (1.36x) with total travel +0.49%.
- On a synthetic 300-contour job, `plan_program` drops 66 ms to 49 ms (1.33x)
  with identical travel.

## Struggles and rejected approaches

A cache that reused the ordering-time theta plan was attempted first, but the
2-opt pass reorders most contours, so almost every cached plan was stale and the
win was negligible. Replacing the ordering-time simulation with a cheap estimate
avoids the duplicate work entirely.

## Risks and follow-up

The ordering heuristic now uses an approximate exit orientation, so contour
order can differ slightly from the previous greedy chain. The final exact
planning and the bed-frame 2-opt keep the drawn strokes unchanged; the measured
travel penalty is under 0.5%. If a future job shows a larger travel regression,
`_last_segment_theta` is the single point to refine.

## Files

- `software/converter_core/kinematics.py`: cheap ordering exit estimate + deferred candidate-cost lookups.
