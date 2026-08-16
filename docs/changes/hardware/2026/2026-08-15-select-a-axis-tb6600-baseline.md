---
id: HW-20260815-002
date: 2026-08-15
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/integration/INTERFACES.md
  - docs/hardware/BOM.md
  - docs/testing/TEST_PLAN.md
  - firmware/grblhal/UPCOMING_CODING_STEPS.md
tags:
  - a-axis
  - tb6600
  - microstepping
  - calibration
related:
  - HW-20260815-001
---

# Select A-axis TB6600 baseline

## Summary

Selected the A-axis initial TB6600 configuration from the observed 12:1
motor-to-bed reduction: 8 microsteps and 1.5 A per phase.

## Reason

The bed needs twelve motor revolutions for one bed revolution. That reduction
already creates 0.01875 degree nominal bed increments at 8 microsteps, so a
higher microstep setting has no demonstrated benefit and would increase step
pulse demand while reducing incremental torque.

## Implementation

The received driver table's 8-microstep row is `SW1 OFF`, `SW2 ON`, `SW3 OFF`.
The motor-rated 1.5 A row is `SW4 ON`, `SW5 ON`, `SW6 OFF`. For the existing
motor-shaft-degree A convention, the initial grblHAL A steps-per-unit value is
`4.444444`; 4,320 commanded A degrees equal one bed revolution.

## Verification

Arithmetic check: 200 full steps/revolution × 8 microsteps = 1,600 pulses per
motor revolution; 1,600 × 12 = 19,200 pulses per bed revolution. M-04 and
M-05 remain required physical verification.

## Struggles and rejected approaches

An initial thought to use an extreme microstep setting was rejected. The
existing 12:1 reduction provides the needed resolution; 16 or 32 microsteps
would make the most-traveled axis more pulse-rate-sensitive with no measured
plot-quality gain.

## Risks and follow-up

Confirm the printed switch table on each received driver and change switches
only while the relevant driver is unpowered. Set and verify current before
motor power, then test M-04/M-05 before using A in coordinated motion.

## Files

- `docs/integration/INTERFACES.md`: explicit A-axis numerical contract.
- `docs/hardware/BOM.md`: TB6600 baseline in the received-part record.
- `docs/testing/TEST_PLAN.md`: E-04, M-04, and M-05 criteria.
- `firmware/grblhal/UPCOMING_CODING_STEPS.md`: initial A setting and required tests.
- `docs/project/ROADMAP.md`: Phase 3 baseline reminder.
- `docs/project/ENGINEERING_LOG.md`: dated decision record.
