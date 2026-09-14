---
id: RPSW-20260914-001
date: 2026-09-14
category: rp23cnc-software
affected_categories:
  - hardware
status: implemented
components:
  - firmware/pen_pressure
tags:
  - cs1238
  - load-cell
  - force-control
  - testing
  - motor-inert
related:
  - HW-20260913-013
---

# Add CS1238 motor-inert bring-up firmware

## Summary

Added a dedicated CS1238 diagnostic sketch for replacement-ADC receipt and
qualification. It cannot issue a pen, actuator, motor-driver, M3/M5, or TMAG
command.

## Reason

The HX711 did not classify real pen contact reliably. The CS1238 needs its own
installed data-rate, noise, and force-path qualification before it may affect
force-control design.

## Implementation

`e07c_cs1238_sensor_bringup.ino` uses the CS123x 1.1.0 driver on GP0/GP1 and
channel A at gain 128. Its USB command interface can tare, print raw values,
select 40/640/1280 SPS, emit a 60-second Welford mean/RMS/peak-to-peak window,
and run a channel-internal-short diagnostic. It touches none of GP2 or
GP4--GP7. The default reference mode is explicitly marked as dependent on the
received board; E-07C requires metering the connected load-cell excitation and
bridge resistance before data is accepted.

## Verification

`arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\pen_pressure\e07c_cs1238_sensor_bringup` passed with CS123x 1.1.0.

## Struggles and rejected approaches

Adding CS1238 support directly to the integrated force controller or reusing
the powered E07B actuator sketch was rejected. Either would make receipt
testing capable of moving the pen before the new sensor and breakout reference
circuit are qualified.

## Risks and follow-up

The exact board is not yet inspected or wired. A common TL431-reference CS1238
breakout may need a documented bridge-reference correction for the installed
load cell. E-07C and E-08C must pass before a bounded CS1238 E-09C actuator
trace is written; this implementation authorizes no production control.

## Files

- `firmware/pen_pressure/e07c_cs1238_sensor_bringup/e07c_cs1238_sensor_bringup.ino`: new motor-inert diagnostic.
- `firmware/pen_pressure/README.md`: documents source purpose and reference qualification.
- `firmware/README.md`: points to the safe replacement-ADC entry point.
- `docs/testing/TEST_PLAN.md`: adds bridge-excitation acceptance evidence to E-07C.
