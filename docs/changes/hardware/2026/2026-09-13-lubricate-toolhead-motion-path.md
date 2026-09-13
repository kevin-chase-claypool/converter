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
- One 10 ms lift pulse reduced the physical scale from 33.7 g to 0.4 g, then
  1.2 g on the third stationary reading. Corresponding deltas were `-21011`,
  `-22650`, and `-26409`.

## Struggles and rejected approaches

Lubrication improves friction but is not treated as proof that the load-cell
force path is correct. The earlier persistent zero-force offset remains open.

## Risks and follow-up

The release behavior is markedly improved, but the 0.4--1.2 g residual is not
yet an approved clear band. Establish repeatable clear threshold, target force,
and pulse/dwell limits before enabling force control.

## Files

- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`: lubrication evidence and pending zero-reference check.
