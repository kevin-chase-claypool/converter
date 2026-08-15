---
id: HW-20260814-005
date: 2026-08-14
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - docs/hardware/ESTOP_TOPOLOGY.md
  - docs/hardware/WIRING_TABLE.md
  - docs/hardware/BOM.md
tags:
  - estop
  - safety
  - rp23cnc
related:
  - HW-20260814-004
---

# Use the RP23CNC Halt input for the initial E-stop

## Summary

The purchased NC mushroom E-stop will initially use one contact pair to drive
the RP23CNC's dedicated, opto-isolated Halt input. The second NC pair remains
insulated and unused.

## Reason

The RP23CNC manual explicitly supports a 12 V opto-isolated E-stop/Halt
control input. A relay-operated motor-energy-removal branch adds components and
verification scope beyond the controller-supported initial implementation.

## Implementation

Use SW1 NC-A across the identified RP23CNC E-stop/Halt terminal pair with Iso
12 V present. Because the switch is NC, configure the E-stop inversion bit for
NC operation during E-19; the planned value is `$14=6` while the current Feed
Hold/Cycle Start choices remain unchanged. Do not set it until the live test.

K1 and D4 are not part of this project. NC-B remains individually insulated.

## Verification

E-19 is pending. It will meter-check both NC pairs, validate the input state in
ioSender, confirm pressed = Halt, and confirm deliberate Reset/Unlock is needed
after release.

## Struggles and rejected approaches

The prior topology treated a K1 relay as mandatory. That overstated what the
RP23CNC manual requires and risked an unnecessary purchase before the
controller's dedicated Halt input had been used.

## Risks and follow-up

Controller Halt does not physically remove 12 V from motor/tool loads. The
existing main power switch is the deliberate full-power shutdown.

## Files

- `docs/hardware/ESTOP_TOPOLOGY.md`: establishes the initial E-stop design.
- `docs/hardware/WIRING_TABLE.md`: records the active and insulated contacts.
- `docs/hardware/BOM.md`: removes K1 and D4 from the required parts.
