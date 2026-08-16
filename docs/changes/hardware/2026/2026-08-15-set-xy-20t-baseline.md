---
id: HW-20260815-003
date: 2026-08-15
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/integration/INTERFACES.md
  - firmware/grblhal/UPCOMING_CODING_STEPS.md
tags:
  - x-axis
  - y-axis
  - gt2
  - calibration
related:
  - HW-20260815-002
---

# Set X/Y 20T baseline

## Summary

Recorded the confirmed 20-tooth GT2 X/Y motor pulleys and the resulting initial
grblHAL calibration values.

## Reason

The pulley tooth count determines X/Y steps per millimeter and was the missing
mechanical parameter required to make the 16-microstep baseline actionable.

## Implementation

At 2 mm GT2 pitch, 200 full steps per revolution, and 16 microsteps, each
20-tooth pulley travels 40 mm per motor revolution. The calculated initial
values are `$100=80.000000` and `$101=80.000000` steps/mm.

## Verification

The project owner confirmed that both X and Y use 20-tooth pulleys. M-03 must
still measure travel and correct the calculated values if necessary.

## Struggles and rejected approaches

No pulley tooth count had been documented earlier, so a numerical X/Y setting
was intentionally withheld rather than assuming a common pulley size.

## Risks and follow-up

Do not treat the calculation as precision calibration. Verify belt tension and
measure a sufficiently long commanded X/Y travel during M-03.

## Files

- `docs/integration/INTERFACES.md`: confirmed X/Y mechanics and settings.
- `docs/hardware/BOM.md`: motor/pulley allocation.
- `docs/testing/TEST_PLAN.md`: M-03 initial values.
- `firmware/grblhal/UPCOMING_CODING_STEPS.md`: controller configuration.
- `docs/project/ENGINEERING_LOG.md`: dated project-owner evidence.
