---
id: HW-20260812-001
date: 2026-08-12
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/WIRING_TABLE.md
  - docs/hardware/BOM.md
tags:
  - hx711
  - load-cell
  - wiring
related:
  - E-07
---

# Recorded load-cell wire mapping

## Summary

Recorded the manufacturer-provided color/function mapping for the selected
uxcell 300 g load cell and its HX711 terminals.

## Reason

The physical load-cell conductors can now be wired without guessing their
excitation and signal functions.

## Implementation

- Red `EXC+` → HX711 `E+`
- Black `EXC-` → HX711 `E-`
- Green `SEN+` → HX711 `A+`
- White `SEN-` → HX711 `A-`

The manufacturer also specifies `0.7 ± 0.15 mV/V` sensitivity and `±0.05% F.S.`
error.

## Verification

This is manufacturer documentation supplied by the project owner. E-07 remains
required to verify the received unit, zero, polarity, and calibration.

## Struggles and rejected approaches

The earlier plan to identify these wires with a meter is no longer the primary
mapping source, but remains a valid check if the received wiring differs.

## Risks and follow-up

Do not treat the documented colors as calibrated force polarity. If increasing
load makes raw readings move opposite the intended convention, resolve it in
the HX711/software calibration stage rather than moving wires without recording
the change.

## Files

- `docs/hardware/WIRING_TABLE.md`: authoritative conductor-to-terminal mapping.
- `docs/hardware/BOM.md`: part specification and remaining verification.
