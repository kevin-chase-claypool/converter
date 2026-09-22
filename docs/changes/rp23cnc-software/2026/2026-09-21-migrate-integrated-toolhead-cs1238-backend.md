---
id: RPSW-20260921-002
date: 2026-09-21
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - CS1238
  - load-cell
  - force-control
  - safety-gates
related:
  - ADR-006
  - E-07C
  - E-08C
  - E-09C
---

# Migrate Integrated Toolhead to CS1238 Backend

## Summary

The dual-core Pro Micro toolhead source now uses CS123x/CS1238 acquisition on
the existing GP0/GP1 harness instead of the failed HX711 path.

## Reason

The installed HX711 failed the E-07 transfer test. The active qualification
plan uses the CS1238 and the installed 300 g load cell with known precision
masses, so the later force-control source must not retain HX711 raw counts,
filtering, or library dependencies.

## Implementation

- Configures CS1238 channel A, gain 128, and 640 SPS through CS123x 1.1.0.
- Reads only after `DT`/`DRDY` is ready, keeps the magnetic-scan power-down
  boundary, and reports CS1238 telemetry/status names.
- Replaces the old median-plus-EMA chain with a candidate 16-sample raw moving
  average. E-08C must still verify installed rate and noise before this window
  becomes an accepted control choice.
- Resets former HX711 raw thresholds and adds a required calibrated force sign.
  A compile-time assertion prevents enabling the pressure-calibration gate
  while any required CS1238 value remains a placeholder.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\\pen_pressure\\pro_micro_rp2350_toolhead` — passed.
- Source inspection confirmed no HX711 include, object, telemetry field, or
  online status remains in the integrated controller.

## Struggles and rejected approaches

Retaining the old HX711 raw thresholds or their filter would falsely imply
that the CS1238 counts have the same polarity, scale, noise, or latency. Those
values were therefore intentionally removed rather than translated.

## Risks and follow-up

This is not hardware validation. E-07C must verify the received CS1238 board
and bridge excitation; E-08C must measure installed sampling behavior; E-09C
must establish the raw-to-grams relation; a guarded actuator-response test
must establish contact, target, release, and hard-limit values. All motion
gates remain disabled until then.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/`: CS1238 acquisition,
  filtering, telemetry, and safety placeholders.
- `firmware/README.md`: current integrated source state.
- `firmware/pen_pressure/README.md`: GP0/GP1 and CS1238 operating contract.
- `docs/integration/INTERFACES.md`: interface ownership and naming.
