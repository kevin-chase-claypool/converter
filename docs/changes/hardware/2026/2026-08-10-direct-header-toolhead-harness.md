---
id: HW-20260810-005
date: 2026-08-10
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - hardware/pc817-interface
  - firmware/pen_pressure
tags:
  - jst
  - harness
  - rp2350
  - pc817
related:
  - E-18
---

# Direct-Header Toolhead Harness

## Summary

Reassigned PC817 signals to GP29, GP28, and GP27 so its tool-side harness uses
one physically consecutive six-position Pro Micro header run. Kept the
DRV8833 logic signals on consecutive GP4–GP7 for a separate four-position
harness.

## Reason

The project owner requested the minimum clean, board-specific JST harnesses
with every connector position directly adjacent on the Pro Micro header.

## Implementation

`J-PC817` is `GND`, `RST` NC, `3V3`, GP29, GP28, GP27; `J-DRV` is GP4–GP7.
Firmware, KiCad net labels, and wiring documentation use the new pin map.

## Verification

- Regenerated the v2 KiCad PCB and schematic from its generator.
- Firmware compilation and E-18 harness re-test remain required.

## Struggles and rejected approaches

- The earlier GP8/GP9/GP20 map could not form one direct, consecutive PC817
  header. RST cannot be used and is an intentional NC connector position.

## Risks and follow-up

- The prior PC817 bench evidence used the old pins; repeat U1/U2/U3/isolation
  checks after repinning before attaching RP23CNC.
- Genuine JST-XH is 2.50 mm pitch and must not be forced into 2.54 mm holes.

## Files

- `hardware/pc817-interface/PRO_MICRO_JST_HARNESS.md`: physical harness map.
- `hardware/pc817-interface/pc817-perfboard-v2-minwire.*`: new GPIO net labels.
- `firmware/pen_pressure/`: new GPIO constants.
