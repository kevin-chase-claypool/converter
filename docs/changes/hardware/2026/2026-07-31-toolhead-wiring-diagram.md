---
id: HW-20260731-001
date: 2026-07-31
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - toolhead-wiring-diagram.svg
  - toolhead-wiring-diagram-viewer.html
  - toolhead-wiring-diagram.png
  - docs/hardware/WIRING_TABLE.md
tags:
  - wiring
  - toolhead
  - rp2350
  - drv8833
  - hx711
  - tmag5273
related:
  - F-05
  - E-07
  - E-08
  - E-09
---

# Toolhead Wiring Diagram

## Summary

Added a top-down toolhead wiring diagram for the SparkFun Pro Micro RP2350,
DRV8833, TMAG5273 Qwiic sensor, HX711, load cell, N20 lift actuator, and DIN rail
harness inputs.

## Reason

The toolhead prototype now needs a readable wiring artifact that shows exact
connection locations without ambiguous split wires or wire crossings.

## Implementation

The diagram assigns prototype RP2350 pins for the first bench firmware:
`GP4/GP5` drive DRV8833 `IN1/IN2`, `GP6` drives DRV8833 `EEP`/sleep enable,
`GP7` reads DRV8833 `ULT`/fault, `GP2/GP3` connect to HX711 `DT/SCK`, and Qwiic
`GPIO17/GPIO16` connects to TMAG5273 `SDA/SCL`. The wiring table now records
these as prototype assignments rather than verified machine wiring.

## Verification

- Rendered `toolhead-wiring-diagram.png` from the SVG through Chrome headless.
- Parsed `toolhead-wiring-diagram.svg` with Python XML parsing.
- Visual inspection confirmed the updated diagram uses separated wiring lanes
  without wire-to-wire crossings.

## Struggles and rejected approaches

The first generated layout crossed power and sensor wires, and one intermediate
layout aligned RP2350 signal labels poorly with the DRV8833 terminals. Those
layouts were replaced with a rerouted no-crossing layout.

## Risks and follow-up

The assignments remain unverified until the DRV8833 module label orientation,
HX711 operation at 3.3 V, load-cell wire colors, RP23CNC M3/M5 interface
circuit, and prototype firmware are bench-tested.

## Files

- `toolhead-wiring-diagram.svg`: editable wiring diagram.
- `toolhead-wiring-diagram-viewer.html`: browser viewer for the SVG.
- `toolhead-wiring-diagram.png`: rendered preview image.
- `docs/hardware/WIRING_TABLE.md`: authoritative prototype pin assignments.
