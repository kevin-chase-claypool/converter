---
id: RPSW-20260922-002
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration
tags:
  - cs1238
  - e-09c
  - calibration
  - load-cell
  - pen-pressure
related:
  - docs/report/lab-notes/2026-09-22-e-09c-cap-free-repeat.md
  - RPSW-20260922-001
---

# Replace E-09C profile with cap-free repeat

## Summary

Replaced staged CS1238 force-profile candidates with the cap-free 20-capture
known-mass repeat, while retaining all force and motor commissioning gates
false.

## Reason

The first 2026-09-22 run included a 2.5 g pen cap. A cap-free repeat removes
that fixture ambiguity from the historical raw zero and significantly improved
the fit residual.

## Implementation

- Recorded the cap-free 5,038.77 raw/g, `R²=0.999978`, 0.132 g RMS result.
- Replaced the staged raw zero, contact/target/hard deltas, clear band, and
  ready band in the integrated configuration.
- Kept the explicitly selected opposite-direction assumption and every
  commissioning gate false pending the installed-pen scale check and actuator
  tests.

## Verification

- Reviewed the saved 20-point raw CSV run and generated graph summaries.
- Recompile the integrated RP2350 sketch after the configuration update.

## Struggles and rejected approaches

The prior cap-included run was not deleted or overwritten; it remains as raw
historical evidence rather than the active staged profile source.

## Risks and follow-up

The result proves the downward fixture relationship, not the upward pen-tip
load path. Capture the installed-pen kitchen-scale trace around 50 g before
actuator response and closed-loop commissioning.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: updated
  inactive candidate calibration values.
- `docs/report/lab-notes/2026-09-22-e-09c-cap-free-repeat.md`: bench evidence.
- `docs/testing/TEST_PLAN.md`: active E-09C result and next gate.
