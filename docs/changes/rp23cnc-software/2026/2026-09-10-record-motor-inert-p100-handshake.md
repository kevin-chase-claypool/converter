---
id: RPSW-20260910-001
date: 2026-09-10
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - Pro Micro RP2350 handshake diagnostic
  - RP23CNC Aux0/LIMA harness
tags:
  - p100
  - magnetic-homing
  - e-18
  - f-08
  - safety
related:
  - RPSW-20260909-002
---

# Record motor-inert P100 handshake evidence

## Summary

The installed motor-inert diagnostic passed the active-low RP23CNC Aux0/U2/GP28
two-phase handshake and the local TMAG magnetic detection transition without
configuring or writing any actuator-related pin.

## Reason

Replacement-N20 selection pauses actuator-dependent work, but F-08/E-18 need
safe evidence for the existing controller-to-toolhead magnetic protocol.

## Implementation

No source or controller configuration changed. The owner connected the existing
blue `A_HOME` conductor from J1.6 to temporary RP23CNC `LIMA SIG` and flashed
the existing `p100_handshake_test` diagnostic.

## Verification

- J1.4 `AUX0` measured 9.33 V released and 0.15 mV asserted relative to J1.5
  `CTRL_GND`.
- COM8 recorded `DISARMED → READY_ACK → WAIT_REARM → SCAN_ACTIVE → DISARMED`.
- In scan state, the center magnet produced `detected=0 → 1 → 0`.
- J1.6 `A_HOME` sank to 0 V during readiness.
- No motor or machine axis command was issued.

Full evidence: `docs/report/lab-notes/2026-09-10-e-18-motor-inert-p100-handshake.md`.

## Struggles and rejected approaches

An initial apparent GP28 polarity inversion was investigated through perfboard
continuity and diode orientation checks. The reassembled board subsequently
passed its expected active-low behavior. No firmware polarity workaround was
accepted because it would have obscured a possible physical defect.

## Risks and follow-up

ioSender did not expose a controller-visible LIMA state, so the controller's
interpretation and released level remain unverified. This does not pass direct
PRB/G38 testing, permit the LIMA-to-PRB retermination, or unlock P100 Q3/Q4.

## Files

- `docs/report/lab-notes/2026-09-10-e-18-motor-inert-p100-handshake.md`: bench evidence.
- `docs/hardware/WIRING_TABLE.md`: current LIMA connection and path status.
- `docs/testing/TEST_PLAN.md`: E-18 partial result.
- `firmware/pen_pressure/README.md`: current magnetic-path status.
