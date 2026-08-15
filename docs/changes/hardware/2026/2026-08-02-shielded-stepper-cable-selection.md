---
id: HW-20260802-002
date: 2026-08-02
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/BOM.md
  - docs/hardware/WIRING_TABLE.md
tags:
  - stepper
  - cable
  - shielding
  - drag-chain
related:
  - E-01
---

# Shielded Stepper Cable Selection

## Summary

Recorded the purchased KWANGIL 20 AWG 4C AMESB shielded cable as the selected
replacement cable for NEMA17 stepper phase wiring.

## Reason

The plotter drag chains may carry NEMA17 motor wiring near toolhead power and
RP23CNC control signals. A shielded four-conductor cable with a drain wire gives
the stepper wiring a cleaner physical shield termination than a generic
unshielded automotive cable or shielded cable without an explicit drain.

## Implementation

The BOM now records the KWANGIL 20 AWG 4C AMESB shielded cable as purchased.
The wiring table now states that each NEMA17 motor should use one four-conductor
cable with the four internal conductors assigned only to `A+`, `A-`, `B+`, and
`B-`. The shield/drain is bonded to PE/chassis at the TB6600/DIN-rail end only,
with the motor end cut back and insulated.

## Verification

- Reviewed the Amazon listing text identifying `OS+Drain+TC BRD`.
- Updated the authoritative BOM and wiring table.
- Documentation index generation and validation were run after the update.

## Struggles and rejected approaches

Plain four-conductor automotive cable was rejected for the stepper runs because
it did not appear to be twisted or shielded. The previously discussed MOOKEERF
shielded cable remained ambiguous about a separate drain wire, so the KWANGIL
AMESB cable was selected instead.

## Risks and follow-up

The received cable still needs inspection before installation. Confirm jacket
markings, conductor colors, drain-wire continuity to shield, flex suitability in
the drag chain, strain relief, and isolation from DC `-V`. Coil pairs still must
pass E-01 before cutting or splicing motor leads.

## Files

- `docs/hardware/BOM.md`: added the purchased shielded stepper cable and source link.
- `docs/hardware/WIRING_TABLE.md`: added stepper cable assignment and shield/drain bonding guidance.
