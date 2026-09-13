---
id: HW-20260913-012
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - hardware/toolhead
tags:
  - toolhead
  - lubrication
  - leadscrew
  - force-testing
related:
  - HW-20260913-011
---

# Lubricate toolhead motion path

## Summary

The owner lubricated the toolhead motion path after the observed leadscrew and
spring-housing interference. A subsequent 10 ms down-force point was stable
while stationary.

## Reason

Variable down-force and history-dependent HX711 readings followed a visible
brief leadscrew/spring hang-up. Lubrication was applied to reduce friction and
binding before further guarded characterization.

## Implementation

The owner greased the moving toolhead mechanism. No wiring, GPIO role, or
firmware mapping changed.

## Verification

- From tare raw 215937, one 10 ms down pulse produced 33.7 g.
- Three stationary readings were `hx_delta=-323079`, `-322781`, and
  `-322551`, a 528-count span over about five seconds.
- Release and post-release zero-reference verification remain pending.

## Struggles and rejected approaches

Lubrication improves friction but is not treated as proof that the load-cell
force path is correct. The earlier persistent zero-force offset remains open.

## Risks and follow-up

Release the current 33.7 g load with one bounded up pulse, then test whether
the physical 0 g condition returns to a stable near-tare HX711 value. Do not
enable force control until the zero-reference result passes.

## Files

- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`: lubrication evidence and pending zero-reference check.
