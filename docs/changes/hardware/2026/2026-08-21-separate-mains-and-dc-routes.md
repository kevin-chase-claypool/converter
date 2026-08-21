---
id: HW-20260821-001
date: 2026-08-21
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - MEISHILE S-120-12
  - HCDC HD064RT
tags:
  - mains
  - dc-power
  - wiring-segregation
  - e-11
related:
  - docs/report/lab-notes/2026-08-20-e-11-main-supply-no-load-path-test.md
---

# Separate Mains and DC Routes

## Summary

Rerouted the main-supply mains-input and DC-output conductors so their runs do
not overlap in the supply/fuse-block area.

## Reason

The earlier layout permitted an insulated crossover. Although a brief,
well-supported crossover can be acceptable, physical separation provides the
clearer and more maintainable mains/extra-low-voltage arrangement.

## Implementation

The project owner rerouted the conductors to eliminate the overlap. The
authoritative wiring table and E-11 note now record the routing state.

## Verification

- Owner visual inspection confirmed the mains-input and DC-output runs no
  longer overlap.
- The prior no-load path result remains 12.05 VDC at the HD064RT input and one
  output pair.

## Struggles and rejected approaches

The prior crossover was rejected in favor of completely separate runs. No
electrical fault was reported.

## Risks and follow-up

This routing update does not verify PE bonding, fitted fuse ratings, conductor
strain relief, supply adjustment range, or loaded behavior. Complete those
E-11 checks before connecting a motion-driver or toolhead load.

## Files

- `docs/hardware/WIRING_TABLE.md`: current power-route state.
- `docs/report/lab-notes/2026-08-20-e-11-main-supply-no-load-path-test.md`:
  dated bench evidence and follow-up.
