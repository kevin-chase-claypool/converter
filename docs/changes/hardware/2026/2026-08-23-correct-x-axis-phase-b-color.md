---
id: HW-20260823-003
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - X-axis motor cable
  - X TB6600 phase wiring
tags:
  - stepper
  - wiring
  - x-axis
  - coil-pair
related:
  - HW-20260823-002
---

# Correct X-axis Phase B cable color

## Summary

The X-axis shielded cable uses white, not blue, for the driver-side `B-`
conductor.

## Reason

The owner corrected the previously recorded X-axis Phase B color.

## Implementation

X TB6600 connections are `A+` black, `A-` green, `B+` red, and `B-` white.
The white cable conductor continues to the motor's blue B- lead. The X cable
remains the sole motor run with a grounded sheath; Y and A retain their
unshielded black/green and red/blue pair convention.

## Verification

Owner correction only. Final conductor continuity, shield bond, and motor
direction verification remain open.

## Struggles and rejected approaches

The prior X cable entry incorrectly copied the motor-side blue lead onto the
driver-side cable color instead of recording the white splice conductor.

## Risks and follow-up

With power removed, verify red/white continuity through the X Phase B run and
the white-to-blue motor splice before energizing the driver.

## Files

- `docs/hardware/WIRING_TABLE.md`: corrects X `B-` to white.
- `docs/hardware/BOM.md`: records the X cable-side splice color.
- `docs/testing/TEST_PLAN.md`: records the X cable color in E-01.
