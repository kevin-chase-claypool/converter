---
id: HW-20260810-001
date: 2026-08-10
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - hardware/pc817-interface
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - pc817
  - perfboard
  - isolation
  - kicad
  - gpio20
related:
  - HW-20260806-001
---

# Minimum-wire PC817 interface

## Summary

Replaced the invalid recovered PC817 route with a compact all-through-hole
KiCad 10 design optimized for the fewest practical perfboard connections. The
design retains three isolated channels, corrects `HOME_ARM` from unavailable
GP10 to exposed GPIO20, and incorporates the latest bench evidence.

## Reason

The original hand-built board required dense point-to-point wiring and then
failed an idle-pullup test. Its recovered KiCad route also contained shorts and
opens. A clean rebuild needed fewer connections and an electrically checked
source of truth.

## Implementation

Connector pins are ordered by channel row. U1/U2 retain normal orientation;
reverse-direction U3 is rotated 180 degrees. D1/D2 stand vertically, C3 is
removed, and R6 remains a conditional test link. The resulting PCB uses 38
segments totaling 161.83 mm and no vias, versus 110 segments / 337.35 mm in
the recovered route. Optional C3 rail bypassing is omitted because the nearby
Pro Micro already decouples the rail; it can be restored directly across J2 if
bench noise requires it. The matching firmware input moved from GP10 to GPIO20.

## Verification

- KiCad 10.0.5 ERC: 0 violations.
- KiCad error-level DRC: 0 violations and 0 unconnected items.
- KiCad schematic parity: 0 issues.
- Exported-netlist audit: all 46 schematic component pins matched their PCB
  reference/pad/net assignments; both connector NC pins remain isolated.
- Arduino CLI compile for `rp2040:rp2040:sparkfun_promicrorp2350`: passed;
  73,212 bytes program storage and 11,708 bytes dynamic memory.
- U3 bench evidence: about 12 V idle and 0.2 V asserted with a 12 V / 2.2 kΩ
  simulated controller load.
- U1 bench evidence: 54.7 mV asserted after repairing its missing LED-cathode
  connection. The final GP8 test passed after the missing tool-side 3.3 V/GND
  links were installed: 3.311 V unloaded, then HIGH/LOW as ENA was
  opened/grounded.
- U2 bench evidence: a disconnected wire was repaired after initial failure;
  GPIO20 then changed HIGH/LOW as AUX0 was opened/grounded.
- Final isolation test: `CTRL_GND` to `TOOL_GND` had no continuity.

## Struggles and rejected approaches

The recovered v1 route was rejected because DRC had already demonstrated
shorts/opens. Keeping all three optocouplers visually identical was rejected
because U3 carries the signal in the opposite direction and caused long
cross-board runs. Optional C3 was omitted to minimize wiring; C1/C2 remain as
signal filters and the nearby Pro Micro provides local rail decoupling.

## Risks and follow-up

The PCB files and the hand-built board are electrically bench-verified, but
physical manufacturing clearances and the exact received screw-terminal body
should be dry-fit. The direct-wire/0 Ω R6 link is valid for the tested U3
sample; repeat the U3 load test if that part is replaced. Full E-18 remains
incomplete because actual RP23CNC ENA/Aux0 behavior, Qwiic readings, and the
installed-system test remain open.

## Files

- `hardware/pc817-interface/pc817-perfboard-v2-minwire.*`: current KiCad design.
- `hardware/pc817-interface/PERFBOARD_BUILD.md`: construction and test map.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: GPIO20 correction.
- `docs/hardware/WIRING_TABLE.md`: current wiring authority and bench status.
- `docs/report/lab-notes/2026-08-10-e-18-pc817-interface-bench-test.md`: measurements.
