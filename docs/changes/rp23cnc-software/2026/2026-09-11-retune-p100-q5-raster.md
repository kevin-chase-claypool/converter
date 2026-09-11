---
id: RPSW-20260911-013
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
  - tools/validate_homing_macro.py
tags:
  - P100
  - Q5
  - raster
  - scan-feed
  - safety
related:
  - RPSW-20260911-012
---

# Retune P100 Q5 Raster Density

## Summary

P100 Q5 now uses 5 mm row pitch and requests `F2000` instead of 10 mm and
`F1000`.

## Reason

The operator requested twice the magnetic crossing speed and twice the Y-axis
sample density for the verified 100 mm center-magnet survey.

## Implementation

The raster now traverses 21 inclusive Y rows over the existing 100 mm square.
Each 100 mm G38 crossing requests 2000 mm/min, which is half the prior
crossing time. The doubled row count keeps total crossing time comparable while
providing denser chord observations. The static validator enforces both values.

## Verification

- `python tools\\validate_homing_macro.py` verifies the exact pitch and feed
  constants plus the existing P100/P111/P112 safety invariants.
- Installed Q5 execution at the new settings: pending.

## Struggles and rejected approaches

Raising `$110` and `$111` was not included: their installed 1500 mm/min limits
have not yet passed a loaded-rate test. Consequently grblHAL may cap the
requested F2000 rate.

## Risks and follow-up

Run a supervised Q5 and inspect reported status feed. Retain the new settings
only if magnetic chord capture and the calculated centroid remain valid. Q3,
Q4, and Q0 remain locked.

## Files

- `firmware/grblhal/macros/P100.macro`: Q5 pitch and requested G38 feed.
- `tools/validate_homing_macro.py`: exact-constant regression check.
- `firmware/README.md`: current motion-controller state.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: scan contract.
