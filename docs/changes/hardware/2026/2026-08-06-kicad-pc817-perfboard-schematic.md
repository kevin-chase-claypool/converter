---
id: HW-20260806-002
date: 2026-08-06
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - PC817C perfboard interface
  - RP23CNC command outputs
  - SparkFun Pro Micro RP2350
tags:
  - kicad
  - optocoupler
  - perfboard
  - a-home
related:
  - HW-20260806-001
  - HW-20260803-003
---

# KiCad PC817C interface and active-low correction

## Summary

Created a KiCad schematic source and exact 14 × 6 all-through-hole perfboard
placement/underside-wire map for a three-channel PC817C interface in the
40.16 × 22.65 mm reserved envelope, plus a matching active-low firmware
contract for its two controller-to-toolhead channels.

## Reason

The project owner selected perfboard construction. Standard perfboard uses a
2.54 mm grid, so the prior 1.25 mm JST-GH SMT connector concept cannot be
mounted directly. The received B07WFGTNQC board does not document a 3.3 V-safe
output-side operating range for RP2350 inputs.

## Implementation

`hardware/pc817-interface/pc817-interface.sch` defines U1 (`ENA` to GP8), U2
(`AUX0` to GP10), and U3 (GP9 to `A_HOME`). U1/U2 source LED current from the
controller 5 V rail through 680 ohm resistors and require the controller output
to sink current. Each output uses a local 10 kohm 3.3 V pullup and 47 nF filter.
Thus, U1/U2 assertions pull GP8/GP10 LOW; the firmware now uses `INPUT` rather
than its conflicting internal pull-downs and reads both signals active-low.
U3 uses a 390 ohm GP9 LED resistor. Reverse clamps are axial 1N4148 for a
perfboard build or SOD-123 1N4148W for the PCB. C3 is a 100 nF local 3.3 V
decoupling capacitor.

`hardware/pc817-interface/PERFBOARD_BUILD.md` defines the actual build: DIP-4
PC817Cs, axial DO-35 1N4148s, ¼ W axial resistors, radial capacitors, 2.54 mm
six-position screw terminals, and insulated underside point-to-point wires. The former
unrouted SMD PCB placement is explicitly superseded and is not a construction
or fabrication file.

`hardware/pc817-interface/pc817-perfboard-v1.2.kicad_pcb` is the matching KiCad
PCB Editor assembly view. It has no copper routes by design: its ratsnest is a
visual check against the perfboard underside-wire list.

`hardware/pc817-interface/pc817-perfboard-v1.2.kicad_sch` is the KiCad 9-native
companion schematic used by that board's Open Schematic action. The legacy
conversion exposed three 1.27 mm diode-wire gaps; those were repaired on D1–D3,
and KiCad 9 ERC then completed with zero violations.

`hardware/pc817-interface/pc817-perfboard-wiring-schematic.svg` provides a
viewable electrical map of all three signal paths. It explicitly distinguishes
the controller and toolhead domains, labels U3 pin 3 as `CTRL_GND`, and keeps
R6 as DNP pending E-18; it is an explanatory diagram, not a replacement for
the KiCad schematic or perfboard connection list.

`hardware/pc817-interface/pc817-perfboard-callouts.svg` overlays construction
callouts on the exact 14 × 6 component-side layout, including connector domain,
all three paths, diode stripe direction, R6's E-18 gate, and underside wiring.

`hardware/pc817-interface/pc817-perfboard-interconnections.svg` adds a
translucent-board overlay for all named underside nets. It is a connectivity
map—not a physical wire-routing prescription—and preserves the intentionally
open R6/A_HOME link.

`hardware/pc817-interface/pc817-clean-schematic.svg` is the complementary
no-overlap conventional schematic. It separates each path into its own row and
uses named nets rather than cross-board wires, while retaining the R6/E-18
safety gate.

R6 is explicitly `0R DNP`. RP23CNC V1.0 schematic page 4 later established
that `LIMA` is a 12 V active-low, switch-to-`GND1` input with a 2 kΩ resistor
and an optocoupler LED, drawing about 5.3 mA when asserted. The purchased
PC817C parts have only a 50% guaranteed CTR at 5 mA, so U3 is not guaranteed
to sink that input current. The reverse `A_HOME` link is now blocked until a
controller-side output driver or high-CTR optocoupler is verified. The schematic
keeps controller and toolhead grounds electrically separate.

## Verification

- Converted the legacy source in KiCad 9 and checked the native companion with
  KiCad 9 ERC: zero violations.
- Audited PC817 pin assignment: pin 1 LED anode, pin 2 LED cathode, pin 3
  phototransistor emitter, and pin 4 collector. U1/U2 have collector at GP8/
  GP10 and emitter at toolhead ground, giving the documented active-low result.
- Reviewed all harness labels against `WIRING_TABLE.md` and retained every
  controller voltage/polarity item as TBD pending bench evidence.

## Struggles and rejected approaches

The KiCad 10 CLI `sch upgrade` command does not import a legacy `.sch` file; it
only upgrades native syntax. The design is therefore supplied as a valid legacy
source that the KiCad editor imports and saves natively. An earlier PCB draft
was not routed because scripted routing produced invalid crossings. It is now
superseded because the project owner chose a fully through-hole perfboard build.

## Risks and follow-up

Before construction, dry-fit the headers around the perfboard mounting holes
and measure the RP23CNC ENA and Aux0 source/sink behavior, their M3/M5 and
M64/M65 states, and actual PC817 LED current. Do not fit R6 until a revised
or qualified U3 output stage is bench-proven against the documented 12 V /
2 kΩ `LIMA` input. The 2.54 mm header series remains TBD; JST families do not
directly fit this 2.54 mm perfboard.

## Files

- `hardware/pc817-interface/pc817-interface.sch`: original KiCad legacy
  schematic source.
- `hardware/pc817-interface/pc817-perfboard-v1.2.kicad_sch`: KiCad 9-native,
  ERC-clean companion schematic for the current perfboard board.
- `hardware/pc817-interface/pc817-perfboard-wiring-schematic.svg`: viewable
  electrical wiring diagram for the three isolated paths.
- `hardware/pc817-interface/pc817-perfboard-callouts.svg`: annotated
  component-side perfboard build map.
- `hardware/pc817-interface/pc817-perfboard-interconnections.svg`:
  translucent-board underside-net overlay.
- `hardware/pc817-interface/pc817-clean-schematic.svg`: no-overlap electrical
  schematic for the three isolated paths.
- `hardware/pc817-interface/PERFBOARD_BUILD.md`: exact component and
  underside-net construction map.
- `hardware/pc817-interface/pc817-perfboard-layout-v1.png`: visual build map.
- `hardware/pc817-interface/pc817-perfboard-v1.2.kicad_pcb`: through-hole KiCad
  assembly layout; deliberately unrouted.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`:
  GP8/GP10 active-low and external-pullup handling.
- `hardware/pc817-interface/README.md`: perfboard construction and conversion guidance.
- `docs/hardware/BOM.md`: parts and selection status.
- `docs/hardware/WIRING_TABLE.md`: authoritative harness mapping and safety gates.
