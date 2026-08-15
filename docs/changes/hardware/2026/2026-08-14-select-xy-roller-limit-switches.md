---
id: HW-20260814-004
date: 2026-08-14
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - docs/hardware/BOM.md
  - docs/hardware/WIRING_TABLE.md
tags:
  - limit-switch
  - homing
  - safety
  - rp23cnc
related:
  - docs/report/lab-notes/2026-08-14-f-03-rp23cnc-step-dir-output.md
---

# Select X/Y Roller-Lever Limit Switches

## Summary

Selected HiLetgo KW12-3 SPDT roller-lever microswitches for the X and Y
physical home/limit functions.

## Reason

F-04 cannot begin until its physical X/Y switch hardware is identified. The
chosen part provides both normally-open and normally-closed contacts, allowing
the project to use a normally-closed, wire-break-detecting circuit after the
RP23CNC opto-input polarity is verified.

## Implementation

Use the terminals explicitly marked `COM` and `NC`; leave `NO` unconnected.
Do not connect either switch to the controller until F-04 confirms the exact
X/Y input terminal labels and grblHAL inversion required by the actual
RP23CNC input circuit.

## Verification

The Amazon listing identifies the KW12-3 as an SPDT roller-lever limit switch
with one normally-open and one normally-closed contact. F-04 must still verify
each received switch using an ohmmeter and then test controller behavior.

## Struggles and rejected approaches

The existing wiring table contained no selected X/Y switch. Installing a
temporary arbitrary jumper on a 12 V opto-isolated limit input was rejected:
it would not prove the final physical switch polarity or fail-safe behavior.

## Risks and follow-up

The controller-side input-pair silkscreen, input polarity, required grblHAL
inversion, wire routing, and final mounting position remain unverified.

## Files

- `docs/hardware/BOM.md`: records the selected X/Y switch part.
- `docs/hardware/WIRING_TABLE.md`: records planned `COM`/`NC` contacts while
  preserving F-04 as the controller-wiring gate.
