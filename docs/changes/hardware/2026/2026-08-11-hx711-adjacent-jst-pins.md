---
id: HW-20260811-002
date: 2026-08-11
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/hardware/WIRING_TABLE.md
  - firmware/pen_pressure
tags:
  - rp2350
  - hx711
  - jst
  - pin-assignment
related:
  - E-07
  - E-08
---

# Moved HX711 to adjacent GP0/GP1 pins

## Summary

Reassigned the HX711 interface from GP2/GP3 to the adjacent GP0/GP1 pins on
the SparkFun Pro Micro RP2350.

## Reason

The planned six-pin PC817 JST harness crowds the former GP2/GP3 location. GP0
and GP1 are otherwise unused in the current toolhead design and make the HX711
signal pair cleaner. They do not make the HX711's 3.3 V power conductor
adjacent; that remains a separate local power branch.

## Implementation

- `GP0` is HX711 `DOUT`/`DT`.
- `GP1` is HX711 `SCK`.
- Updated both sensor and integrated-toolhead Arduino sketches, wiring table,
  interface record, and prototype pin reference.

## Verification

- No current project assignment uses GP0 or GP1.
- Firmware compilation and E-07/E-08 are still required after wiring the
  changed pins.

## Struggles and rejected approaches

Keeping GP2/GP3 would preserve the original sketch constants but would crowd
the physical connector area without a functional benefit.

## Risks and follow-up

Do not use GP0/GP1 for an added UART or I2C peripheral without first moving the
HX711 assignment. Validate the actual assembled connector and run the HX711
bench tests before force-control work.

## Files

- `docs/hardware/WIRING_TABLE.md`: authoritative physical pin reassignment.
- `firmware/pen_pressure/`: matching Arduino pin constants and reference.
