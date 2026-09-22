---
id: RPSW-20260922-001
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp
tags:
  - cs1238
  - e-09c
  - force-profile
  - pen-pressure
  - calibration
related:
  - docs/report/lab-notes/2026-09-22-e-09c-cs1238-known-mass-calibration.md
  - docs/testing/TEST_PLAN.md
---

# Stage E-09C CS1238 force profile

## Summary

Staged the measured 2026-09-22 known-mass CS1238 result as a candidate 35–70 g
integrated toolhead force profile without enabling motor or force control.

## Reason

The previous integrated source contained deliberate zero placeholders and could
not represent the completed known-mass calibration in later guarded testing.

## Implementation

- Recorded E-09C fitted zero, sign, contact/target/hard raw deltas, ready band,
  and clear band in `toolhead_config.h`.
- Made clear-band checks reference the fresh boot tare rather than a historical
  fixed raw zero, while retaining the fitted zero as calibration evidence.
- Added a one-COM-port saved-run correction workflow for constant fixture mass
  and a direct installed-pen kitchen-scale raw-direction check. It retains raw
  records, records mass-label corrections, and never commands the N20.
- Kept all existing commissioning gates false.

## Verification

- Reviewed 19 raw captures plus generated calibration/residual figures.
- RP2350 source compilation and static checks are required before flashing the
  integrated sketch; no actuator was energized in this milestone.

## Struggles and rejected approaches

The weight fixture loads the motor mount downward while the pen sees upward
reaction. The source therefore uses the user's selected opposite-direction
assumption and treats it as a candidate, rather than claiming a precision
mechanical equivalence.

The original run also had a 2.5 g pen cap present at every entered `0–90 g`
point. It must be added to each physical mass label; subtracting it would make
the already-present fixture load disappear from the fit. The staged historical
zero was corrected accordingly, but the raw source data remains unmodified.

## Risks and follow-up

Confirm raw sign at the installed pen and perform T-01/T-01H before enabling
`PRESSURE_CALIBRATION_VALID`, actuator, pen-clear, or GP27 readiness gates.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: staged
  candidate raw profile.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.*`:
  fresh-tare clear check.
- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/known_mass_calibration_gui.py`:
  fixture-mass correction and pen-scale raw-direction check.
- `docs/report/lab-notes/2026-09-22-e-09c-cs1238-known-mass-calibration.md`:
  bench evidence.
