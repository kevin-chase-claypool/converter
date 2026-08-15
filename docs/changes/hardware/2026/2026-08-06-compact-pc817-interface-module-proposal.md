---
id: HW-20260806-001
date: 2026-08-06
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
components:
  - PC817C interface module
  - RP23CNC command outputs
  - SparkFun Pro Micro RP2350
tags:
  - optocoupler
  - pcb-layout
  - toolhead
  - a-home
related:
  - HW-20260803-003
status: superseded
---

# Compact PC817 interface module proposal

## Summary

Added a PNG placement-and-schematic reference for a proposed three-channel
PC817C interface module constrained to the reserved `40.16 × 22.65 mm`
toolhead envelope. The board uses side-entry (90°) 1.25 mm JST GH connectors on
both short edges. This concept is superseded by the KiCad perfboard schematic
in `HW-20260806-002` after the build method changed to perfboard.

## Reason

The received B07WFGTNQC module does not document a 3.3 V output-side operating
range suitable for the RP2350. The installation has a small rectangular space
beside the Pro Micro and needs two incoming controller commands plus the reverse
`A_HOME` interface in one compact, cable-friendly board.

## Implementation

`pc817-three-channel-module-proposal.png` shows two RP23CNC-to-Pro-Micro
channels with local 3.3 V pullups and RC filtering, and a reverse Pro Micro
`GP9` channel intended to act as a switch-like RP23CNC A limit/home input. The
third-channel `R6` link is marked DNP (do not populate), preserving a safe open
state before controller-input verification. The purchased BOJACK PC817C DIP-4
pack (ASIN B08CXRHDHP) supplies the three optocouplers. Its listing states a
50% minimum CTR at 5 mA, so the draft specifies `680 Ω` for controller-side
LED paths and `390 Ω` for the GP9 LED path, subject to source/sink testing. The
reproducible PNG renderer is `tools/render_pc817_module.py`. Each optocoupler
LED has a reverse-parallel `1N4148W` protection diode in the SOD-123 package;
do not substitute the similarly named `1N4148WS`, which has a SOD-323 footprint.

## Verification

- Rendered the PNG with the bundled Python/Pillow runtime at 300 DPI metadata.
- Visually checked the 40.16 × 22.65 mm board outline, three DIP-4 PC817C
  packages, two side-entry connector positions, passives, and the non-populated
  `R6` marker.
- Confirmed JST GH is a 1.25 mm series with a side-entry SMT option; use
  `SM05B-GHS-TB(LF)(SN)` or an electrically/mechanically compatible part.

## Struggles and rejected approaches

The generic optocoupler board was not accepted as a direct 3.3 V GPIO solution:
its published output range begins at 3.6 V. A first direct-drive concept also
omitted the separate controller `+5V` feed required to let ENA/Aux0 operate as
low-side-sink inputs; the proposed circuit uses that feed and retains logic
polarity.

## Risks and follow-up

This is a superseded placement-feasibility diagram, not Gerbers or a fabrication
release. The 1.25 mm JST-GH connector selection is unsuitable for ordinary
2.54 mm perfboard.
Bench-test RP23CNC ENA and Aux0 voltage/current/polarity, then validate the
RP23CNC A limit/home input in E-18 before fitting `R6` or connecting `A_HOME`.
Confirm the actual 90° connector and wire harness fit against the CAD enclosure
before board manufacture.

## Files

- `pc817-three-channel-module-proposal.png`: proposed schematic and compact PCB placement reference.
- `tools/render_pc817_module.py`: reproducible PNG renderer.
- `docs/hardware/BOM.md`: records the board as proposed, not selected.
- `docs/hardware/WIRING_TABLE.md`: preserves the historical proposed concept; current wiring points to the KiCad perfboard schematic.
