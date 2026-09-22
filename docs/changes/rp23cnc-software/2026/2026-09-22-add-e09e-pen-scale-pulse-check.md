---
id: RPSW-20260922-003
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e09e_cs1238_pen_scale_pulse
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger
tags:
  - cs1238
  - n20
  - kitchen-scale
  - e-09e
  - pen-pressure
related:
  - docs/testing/TEST_PLAN.md
  - RPSW-20260922-002
---

# Add E-09E installed-pen scale pulse check

## Summary

Added a dedicated, operator-supervised CS1238/N20 test mode that lets a
kitchen scale serve as the installed pen-force reference without needing a
precision scale-positioner.

## Reason

The E-09C downward weight fixture establishes CS1238 sensitivity, but cannot
independently prove that the real upward pen-tip reaction has the selected raw
direction. The available kitchen scale can provide that reference if the N20
approach is deliberately bounded and supervised.

## Implementation

- Added E-09E native-USB test firmware. It requires clear-state tare plus an
  explicit `ARM`, permits only individual 10–100 ms pulses, checks `ULT`, sleeps
  the driver after every pulse, blocks lift at GP2 `LIFT_HOME`, and retains
  raw CS1238 `CAPTURE` support.
- It has no M3/M5, GP27, continuous drive, force seeking, or closed-loop
  control.
- Extended the existing one-COM-port Windows application with enabled-only-for-
  E-09E arm, toward-scale, away, read, and stop controls. The operator watches
  the unconnected kitchen-scale display, waits after each pulse, and records a
  raw trace at the chosen stable scale force.

## Verification

- `arduino-cli compile --build-path work\e09e-pulse-build --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\pen_pressure\e09e_cs1238_pen_scale_pulse`
  passed: 62,316 bytes program / 10,908 bytes globals.
- `python -m py_compile known_mass_calibration_gui.py` and
  `python -m unittest test_known_mass_calibration.py` passed.

## Struggles and rejected approaches

An automatic force stop is intentionally not implemented: the kitchen scale
has no PC interface, while the CS1238 is the channel being verified. Stopping
from the CS1238-derived estimate would be circular and cannot validate the
scale-to-CS1238 relationship.

## Risks and follow-up

The first real pulse must re-confirm the recorded direction with clear travel,
6 V current limiting, and a reachable physical cutoff. Stop at the scale
reading; do not exhaust the 30-pulse budget near contact. This test does not
authorize production force control, M3/M5 behavior, or the existing controller
gates.

## Files

- `firmware/pen_pressure/e09e_cs1238_pen_scale_pulse/e09e_cs1238_pen_scale_pulse.ino`:
  bounded CS1238/N20 pulse test.
- `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/pc_logger/known_mass_calibration_gui.py`:
  guided E-09E controls and raw capture.
- `firmware/pen_pressure/README.md`,
  `firmware/pen_pressure/e07d_cs1238_known_mass_calibration/README.md`, and
  `docs/testing/TEST_PLAN.md`: current workflow and safety boundary.
