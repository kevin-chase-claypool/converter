# ADR-002: Defer final toolhead controller placement

- Status: proposed
- Date: 2026-06-06

## Context

The desired toolhead uses a DC gearmotor, DRV8833, HX711/load cell, and TMAG5273.
RP2350 has two cores, but motion timing and grblHAL maintainability are higher
priority than using both cores merely because they exist.

## Proposed decision

Prototype the toolhead control loop independently. Integrate it into RP23CNC
only if all of these are true:

1. Required pins are available and electrically compatible.
2. The upstream driver has a maintainable plugin or multicore extension point.
3. Sensor/control work does not affect motion jitter or real-time command latency.
4. Fault behavior remains deterministic.

Otherwise use a separate MCU and a small ENGAGE/LIFT/READY/FAULT interface.

## Evidence needed

- RP23CNC pin audit.
- HX711 sample-rate and noise measurements.
- Toolhead control-loop timing.
- Step-jitter and command-latency measurements with the toolhead active.
