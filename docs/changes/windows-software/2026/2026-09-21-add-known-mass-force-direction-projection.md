---
id: WINSW-20260921-002
date: 2026-09-21
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/known_mass_calibration_gui.py
tags:
  - cs1238
  - known-mass
  - force-direction
  - pen-force
  - calibration
  - e-09c
related:
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration/README.md
  - docs/testing/TEST_PLAN.md
---

# Add known-mass force-direction projection

## Summary

The CS1238 known-mass application now preserves the downward motor-mount weight
fit and separately presents an approximate upward pen-tip force projection.

## Reason

The practical precision-weight fixture loads the motor mount downward, while
paper normally applies an upward reaction at the pen. Treating their signed raw
values as identical would mislabel the result and could select the wrong side
of the no-contact raw value for an initial pen-force target.

## Implementation

- Added a per-run force-direction interpretation with the default **Opposite:
  upward pen-tip reaction** and a deliberate same-direction alternative.
- Stored the interpretation in run metadata and each point summary row.
- Kept the raw CSV and measured downward OLS fit unchanged.
- Added a separate, clearly warned projection fit and graph for estimated
  40–60 g upward pen force.
- Prevented mixing directional interpretations in one run.

## Verification

- `python -m unittest test_known_mass_calibration.py` — deterministic signed
  same/opposite projection checks passed.
- Python syntax compilation passed.

## Struggles and rejected approaches

The software cannot infer whether the two physical load paths are mechanically
identical. It therefore does not claim a precision correction; it retains the
measured curve and marks the pen-force calculation as an explicit assumption.

## Risks and follow-up

Confirm the selected raw direction once using the installed pen before using
the estimate. Do not copy any coefficient or candidate raw band into force
control until E-09C and later actuator checks are accepted.

## Files

- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/known_mass_calibration_gui.py`:
  UI, stored metadata, signed projection, and graph.
- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/README.md`:
  practical fixture instructions.
- `docs/testing/TEST_PLAN.md`: E-09C scope and required direction check.
