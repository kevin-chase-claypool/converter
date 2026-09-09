---
id: RPSW-20260908-002
date: 2026-09-08
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - pro_micro_rp2350_toolhead
  - GP20/GP21 service UART
tags:
  - toolhead
  - uart
  - telemetry
  - diagnostics
related:
  - RPSW-20260908-001
  - HW-20260908-004
---

# Fix integrated service-UART telemetry suppression

## Summary

Restored integrated toolhead telemetry through the GP20/GP21 FTDI service
interface and added a deterministic UART-ready startup line.

## Reason

The motor-safe T-01G diagnostic produced clean output on the installed
interface, but the integrated sketch did not. That ruled out the physical
switch, Pro Micro, adapter, ground, and monitor configuration as the source of
the integrated symptom.

## Implementation

The integrated telemetry writer no longer requires its entire formatted record
to fit in `Serial2.availableForWrite()` before starting a write. A service UART
FIFO may be smaller than the complete record, making that predicate permanently
false. The sketch now uses `Serial2.write()` for every complete valid record
and writes `Theta toolhead service UART ready` immediately after configuring
UART1 on GP20/GP21. Native USB `Serial` remains the command interface.

## Verification

`arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350
firmware\\pen_pressure\\pro_micro_rp2350_toolhead` and `git diff --check`
passed. With the corrected sketch installed, COM8 at 115200 reported the ready
line and recurring complete telemetry records.

## Struggles and rejected approaches

The initial suspicion that the switch, UART wiring, adapter, or board had been
damaged was rejected after the isolated T-01G sketch cleanly reported both
switch states on the same path. The earlier `Serial1` mapping mistake had
already been corrected to `Serial2`; this was a separate record-size/FIFO gate.

## Risks and follow-up

The UART result does not validate sensor initialization or powered motion. The
motor commissioning gates remain false; this change must not be treated as
authorization for motion.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: direct service-UART telemetry and ready line.
- `firmware/README.md`: service-UART current state.
- `firmware/pen_pressure/README.md`: UART behavior and maintenance constraint.
- `docs/report/lab-notes/2026-09-08-t-01g-lift-home-switch-installation.md`: bench diagnosis and correction.
- `docs/project/ENGINEERING_LOG.md`: failure and recovery record.
