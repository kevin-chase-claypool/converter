---
id: HW-20260904-003
date: 2026-09-04
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - RP23CNC
  - X TB6600
  - Y TB6600
  - A TB6600
  - docs/hardware/WIRING_TABLE.md
tags:
  - tb6600
  - signal-wiring
  - wire-gauge
  - x-axis
  - y-axis
  - a-axis
related:
  - HW-20260904-002
  - E-03
---

# Record TB6600 signal harness wiring

## Summary

Recorded the owner-reported completion of the three short RP23CNC-to-TB6600
signal harnesses.

## Reason

The project needed a current wiring record before the installed-driver signal
test. The owner selected 24 AWG conductors for the approximately six-inch
harnesses and common-ground jumpers.

## Implementation

- Black conductors carry the axis-local common `G` and are distributed to
  `PUL-`, `DIR-`, and `ENA-` through the common block.
- Yellow carries `En` to `ENA+`.
- White carries `Dir` to `DIR+`.
- Blue carries `Stp` to `PUL+`.
- The same convention is used for X, Y, and A.

## Verification

The owner reports all signal pins and their common returns are physically
wired. Functional input behavior remains unverified; E-03 must still be
performed with the motors disconnected and with the documented polarity
confirmed.

## Struggles and rejected approaches

None for the physical installation. A separate black common-return color was
retained so the blue step wire cannot be confused with signal ground.

## Risks and follow-up

Before applying motor power, perform power-off continuity and short checks at
each driver. Then run E-03 one axis at a time; do not promote these rows to
passed until the installed TB6600 inputs respond correctly.

## Files

- `docs/hardware/WIRING_TABLE.md`: records 24 AWG signal colors and wired,
  unverified status for MOT-001 through MOT-008.
