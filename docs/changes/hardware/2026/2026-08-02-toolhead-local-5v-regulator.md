---
id: HW-20260802-001
date: 2026-08-02
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/hardware/BOM.md
  - docs/hardware/WIRING_TABLE.md
  - docs/integration/INTERFACES.md
  - docs/testing/TEST_PLAN.md
  - docs/electronics_layout_and_wiring.html
  - docs/full_wiring_diagram.html
  - toolhead-wiring-diagram.svg
  - toolhead-wiring-diagram.png
tags:
  - power
  - toolhead
  - regulator
  - drag-chain
related:
  - E-14
  - E-15
  - E-15A
---

# Toolhead Local 5 V Regulator And 6 V Rail

## Summary

Added the purchased Pololu S7V8F5 5 V step-up/step-down regulator, selected the
Pololu D36V50F6 fixed 6 V regulator for the toolhead power rail, and clarified
the RP23CNC-side toolhead interface shown on the toolhead wiring diagram.

## Reason

The toolhead architecture now uses one 6 V power pair through the drag chain and
generates 5 V locally on the toolhead. The DIN-side 6 V regulator was changed
from the adjustable B085T73CSD module to the fixed-output Pololu D36V50F6.

## Implementation

The BOM records the Pololu S7V8F5 as purchased for local RP2350 logic power and
the Pololu D36V50F6 as the selected DIN-side 12 V-to-6 V regulator. The wiring
table now routes the D36V50F6 6 V output to both DRV8833 motor power and the
S7V8F5 regulator input, then routes the S7V8F5 5 V output to the SparkFun Pro
Micro RP2350. The integration contract now identifies the 6 V, local 5 V, and
3.3 V sensor power ownership. The wiring table and interface contract also now
record the prototype TMAG5273 path as TMAG5273 -> Pro Micro RP2350 -> `GP9`
conditioned `A_HOME` output -> RP23CNC input, gated by RP23CNC `Aux 0` ->
5 V-to-3.3 V interface -> Pro Micro `GP10` `HOME_ARM` so a passing bed magnet
does not assert the A limit/home input during normal
printing. The toolhead diagram now separates DIN rail power from control
signals: the DIN rail power block contains only 6 V/GND distribution, the
RP23CNC/RP23U5XBB block contains `AUX 0 OUT / HOME_ARM`, `SPINDLE ENA OUT`,
and `A LIMIT / HOME IN`, and the 5 V-to-3.3 V level-shifter/opto block protects
the Pro Micro `GP10` and `GP8` inputs. The RP23CNC `SPINDLE ENA OUT` path goes
through the level shifter to Pro Micro `GP8`, the `A_HOME` return path goes from
Pro Micro `GP9` to the RP23CNC A limit/home input, and the DIN power block uses
separate `6V_TO_DRV`,
  `GND_TO_DRV`, `6V_TO_S7V8F5`, and `GND_TO_S7V8F5` rows so power wires do not
  visually split from one terminal. The explanatory full-system and toolhead
  diagrams were updated to show the selected regulator chain and
  RP23CNC/control-side interface.

## Verification

- Updated the authoritative BOM and wiring table.
- Updated E-14/E-15 to verify the D36V50F6 and added E-15A for S7V8F5 output,
  thermal behavior, and RP2350 reset margin under actuator activity.
- Parsed `toolhead-wiring-diagram.svg` as XML.
- Rendered `toolhead-wiring-diagram.png` from the updated SVG and visually
  checked the upper-left regulator/controller interface area, including the
  separate RP23CNC block.
- Ran `python tools\docs_index.py --write` and
  `python tools\docs_index.py --check`.

## Struggles and rejected approaches

The existing fixed 5 V buck modules remain spares. The adjustable B085T73CSD
modules also remain available for bench use, but they are superseded for the
final toolhead 6 V rail by the fixed-output Pololu D36V50F6.

## Risks and follow-up

The Pololu regulators have not been bench-tested in this machine. E-14, E-15,
and E-15A must pass before the RP2350, HX711, TMAG5273, or actuator are powered
from the final toolhead harness. The `GP9` `A_HOME` firmware threshold logic,
RP23CNC `Aux 0` arm workflow, level-shifter/opto wiring, output driver, and
RP23CNC input interface remain unverified and must not be wired directly.

## Files

- `docs/hardware/BOM.md`: added the purchased Pololu S7V8F5, selected the Pololu D36V50F6, and superseded the fixed 5 V buck for toolhead logic.
- `docs/hardware/WIRING_TABLE.md`: added local 6 V-to-5 V wiring rows, updated the TMAG5273-to-RP23CNC homing path, and revised the revision entry.
- `docs/integration/INTERFACES.md`: documented toolhead power ownership and the Pro Micro mediated TMAG5273 homing path.
- `docs/testing/TEST_PLAN.md`: added E-15A regulator characterization.
- `docs/electronics_layout_and_wiring.html`: updated conceptual toolhead power flow.
- `docs/full_wiring_diagram.html`: updated legacy full-system diagram wording.
- `toolhead-wiring-diagram.svg`: updated the top-down toolhead diagram with the local regulator.
- `toolhead-wiring-diagram.png`: rendered preview of the updated SVG.
