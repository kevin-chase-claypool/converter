---
id: RPSW-20260921-001
date: 2026-09-21
category: rp23cnc-software
affected_categories:
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e07d_cs1238_known_mass_calibration
  - docs/hardware/WIRING_TABLE.md
tags:
  - cs1238
  - load-cell
  - calibration
  - known-mass
related:
  - E-07C
  - E-07D
---

# Replace dual-ADC fixture with Pro Micro known-mass calibration

## Summary

Replaced the unbuilt Pico 2/INA101 dual-sensor fixture with a single-Pro-Micro
CS1238 known-mass calibration method for the installed 300 g load cell.

## Verification

`arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350
firmware\pen_pressure\e07d_cs1238_known_mass_calibration` passed. No hardware
has been wired or loaded.

## Risks and follow-up

Use 0–70 g known masses in the installed force direction, with repeated load
and unload passes. The target 40–60 g band is not enabled for force control
until raw data, fit residuals, noise, and actuator response are recorded.
