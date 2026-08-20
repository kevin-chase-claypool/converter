---
id: HW-20260820-001
date: 2026-08-20
category: hardware
affected_categories:
  - hardware
status: verified
components:
  - MEISHILE S-120-12
  - HCDC HD064RT
tags:
  - power-supply
  - fuse-block
  - e-11
  - voltage
related:
  - docs/report/lab-notes/2026-08-20-e-11-main-supply-no-load-path-test.md
---

# Record Main Supply No-Load Path Test

## Summary

Recorded a partial no-load E-11 check of the main 12 V supply through the
HD064RT distribution block.

## Reason

The project owner measured the energized fuse-block input and one output pair
before connecting downstream motion or toolhead loads.

## Implementation

The master wiring table now records the measured supply-to-distribution result,
and E-11 carries the partial result and remaining acceptance conditions.

## Verification

- Fuse-block input measured 12.05 VDC.
- One fuse-block output pair measured 12.05 VDC.
- Observed polarity agreed with the block markings.

## Struggles and rejected approaches

No electrical anomaly was reported. Meter model/accuracy and output-pair
identifier were not recorded, so the measurement is retained as partial
evidence rather than a complete characterization.

## Risks and follow-up

Complete the remaining E-11 checks before connecting loads: supply-terminal
measurement, label photo, protective-earth/chassis continuity, and no-load
`+V ADJ` range. Branch-fuse verification and loaded supply tests remain open.

## Files

- `docs/report/lab-notes/2026-08-20-e-11-main-supply-no-load-path-test.md`:
  dated bench evidence.
- `docs/testing/TEST_PLAN.md`: E-11 partial status.
- `docs/hardware/WIRING_TABLE.md`: authoritative power-path result.
