---
id: HW-20260803-003
date: 2026-08-03
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - power-distribution-schematic.svg
  - power-distribution-schematic.png
  - docs/hardware/BOM.md
  - docs/hardware/WIRING_TABLE.md
  - docs/hardware/POWER_DISTRIBUTION.md
  - docs/integration/INTERFACES.md
tags:
  - optocoupler
  - level-shifting
  - toolhead-interface
  - wiring
related:
  - HW-20260803-002
  - HW-20260803-001
---

# B07WFGTNQC Optocoupler Interface

## Summary

Added the B07WFGTNQC 4-channel optocoupler isolation / voltage-converter module
to the current schematic and documentation. The planned use is `CH1` for
RP23CNC `M3/M5` into Pro Micro `GP8` and `CH2` for RP23CNC `HOME_ARM` into Pro
Micro `GP10`.

## Reason

The project selected this module for the RP23CNC-to-Pro-Micro command interface,
so the schematic needed to show its terminals and wiring instead of leaving the
interface as a generic level shifter/opto block.

## Implementation

Updated `power-distribution-schematic.svg` and rendered
`power-distribution-schematic.png` with a separate lower signal-isolation
section. The diagram draws RP23CNC signal-side terminals, the B07WFGTNQC
optocoupler input and output terminals, Pro Micro `3V3`, `GND`, `GP8`, and
`GP10`, and the required S7V8F5 `VOUT/GND` power feed into the Pro Micro
`RAW/5V` and `GND` pins.

Updated the BOM, wiring table, power-distribution document, integration
interface contract, and roadmap to record the module and its verification
requirements.

## Verification

- Opened the Amazon listing for B07WFGTNQC and recorded the listed voltage role.
- Parsed `power-distribution-schematic.svg` as XML.
- Rendered `power-distribution-schematic.png` with Chrome headless.
- Visually inspected the rendered PNG for straight, separated signal lanes and
  the visible S7V8F5 `VOUT/GND` to Pro Micro `RAW/5V/GND` power connection.

## Struggles and rejected approaches

The first expanded render placed the new signal section too close to the power
area. A later bulk coordinate shift distorted labels and terminal locations, so
the SVG was replaced with a clean fixed-coordinate drawing. A later inspection
found the text documentation had the correct S7V8F5-to-Pro-Micro power path, but
the schematic did not show it visually; a dedicated Pro Micro power block was
added.

## Risks and follow-up

The Amazon listing says the output side operates in the 3.6-24 V range, so the
received board must be inspected and tested before connecting it to RP2350 GPIO.
Do not use the same fixed-direction module for the reverse Pro-Micro-to-RP23CNC
`A_HOME` signal unless mixed-direction wiring is proven safe.

## Files

- `power-distribution-schematic.svg`: added B07WFGTNQC signal-isolation section.
- `power-distribution-schematic.png`: rendered updated schematic.
- `docs/hardware/BOM.md`: added B07WFGTNQC as selected signal interface hardware.
- `docs/hardware/WIRING_TABLE.md`: added channel-specific command-signal rows.
- `docs/hardware/POWER_DISTRIBUTION.md`: documented channel use and verification gates.
- `docs/integration/INTERFACES.md`: updated logical interface contract.
- `docs/project/ROADMAP.md`: added optocoupler bench-verification task.
