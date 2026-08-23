---
id: HW-20260823-002
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - X-axis motor cable
  - Y-axis motor cable
  - A-axis motor cable
tags:
  - stepper
  - cable
  - shielding
  - wiring
  - x-axis
related:
  - HW-20260819-003
---

# Set X-axis motor shielding plan

## Summary

The X-axis motor run is the only planned motor cable with a grounded sheath.
Y and A remain unshielded and use black/green and red/blue coil pairs.

## Reason

The owner corrected the earlier current-state record, which had assigned the
only shielded motor run to Y.

## Implementation

The X shield/drain is designated to bond at the TB6600/DIN-rail PE/chassis end
only, with the motor end insulated. Y and A retain their four-wire color-pair
convention: black/green is one coil and red/blue is the other. This supersedes
the earlier Y-shielded-cable and red/white-splice record.

## Verification

Owner wiring instruction only. The X cable installation, PE continuity, shield
isolation from DC `-V`, and final phase wiring remain unverified.

## Struggles and rejected approaches

The prior record conflated the planned cable arrangement with the current one;
it was superseded rather than treated as active wiring.

## Risks and follow-up

Before energizing the X driver, verify its completed shield bond to PE/chassis,
its isolation from DC and signal grounds, phase continuity, and motor direction
in E-01/M-01.

## Files

- `docs/hardware/WIRING_TABLE.md`: updates shield ownership and phase pairs.
- `docs/hardware/BOM.md`: updates the selected shielded-cable application.
- `docs/hardware/POWER_DISTRIBUTION.md`: moves the PE shield reference to X.
- `docs/testing/TEST_PLAN.md`: records the remaining X shield-bond check.
