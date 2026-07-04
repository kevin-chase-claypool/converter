---
id: HW-20260704-003
date: 2026-07-04
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
  - docs/changes/rp23cnc-software/2026/2026-07-04-magnetic-homing-calibration-plan.md
  - docs/electronics_layout_and_wiring.html
tags:
  - tmag5273
  - magnetic-calibration
  - sensor-mount
  - homing
related:
  - RPSW-20260704-001
---

# Fixed TMAG5273 Height

## Summary

Corrected the magnetic calibration plan to state that the TMAG5273 Z height is
fixed by the toolhead mount and heat-set inserts.

## Reason

The previous saturation-handling guidance suggested increasing sensor height,
but the planned sensor mount is static in Z. Calibration mitigations must use
the available variables instead of implying an impossible adjustment.

## Implementation

Updated the homing and magnetic calibration plan to treat sensor Z height as
non-adjustable unless the mount is redesigned. Replaced height-adjustment
mitigation with scan-window, threshold, magnet strength, magnet geometry, and
mount-redesign options.

## Verification

- Searched the repository for sensor-height references and updated the
  calibration guidance that implied adjustable Z.

## Struggles and rejected approaches

Rejected runtime Z-height adjustment because the TMAG5273 is fixed to the
toolhead with heat-set inserts.

## Risks and follow-up

If measured magnetic footprints are unusable at the fixed height, the project
must change magnet geometry or redesign the sensor mount before recording
calibration constants.

## Files

- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: records fixed sensor
  height and feasible saturation mitigations.
- `docs/changes/rp23cnc-software/2026/2026-07-04-magnetic-homing-calibration-plan.md`:
  updates the original change note's residual risk.
- `docs/electronics_layout_and_wiring.html`: clarifies that sensor-height
  verification refers to a fixed height.
