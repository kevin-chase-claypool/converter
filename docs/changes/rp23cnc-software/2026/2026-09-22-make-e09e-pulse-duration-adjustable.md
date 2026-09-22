---
id: RPSW-20260922-004
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
status: implemented
components:
  - firmware/pen_pressure/e09e_cs1238_pen_scale_pulse
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger
tags:
  - e-09e
  - n20
  - pulse-duration
  - safety
related:
  - RPSW-20260922-003
---

# Make E-09E pulse duration adjustable

## Summary

Added an operator-selectable N20 pulse duration to the E-09E kitchen-scale
test, bounded to 10–100 ms by both the Windows interface and firmware.

## Reason

The operator needs to adapt pulse size to the installed mechanism while using
the kitchen-scale display as the force reference.

## Implementation

- Added a 10–100 ms pulse-duration spinbox to the pen-scale check UI.
- Parsed `PULSE DOWN <ms>` and `PULSE UP <ms>` commands in E-09E.
- Rejects durations outside 10–100 ms on the Pro Micro even if a malformed or
  non-UI serial command is received.

## Verification

- Recompile E-09E for the SparkFun Pro Micro RP2350 target.
- Run the Windows calibration application unit checks and documentation index.

## Struggles and rejected approaches

Unbounded free-form duration is rejected because this is a supervised bench
fixture and a long pulse could exceed the intended contact-force range before
the operator can observe the scale.

## Risks and follow-up

Start at 10 ms and wait for a settled scale indication after every pulse.
Increasing the duration is not production calibration and does not relax the
physical cutoff, fault, arm-budget, or driver-sleep safeguards.

## Files

- `firmware/pen_pressure/e09e_cs1238_pen_scale_pulse/e09e_cs1238_pen_scale_pulse.ino`:
  command parser and hardware-side range enforcement.
- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/known_mass_calibration_gui.py`:
  bounded duration control.
