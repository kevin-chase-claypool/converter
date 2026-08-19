---
id: HW-20260819-004
date: 2026-08-19
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/WIRING_TABLE.md
  - docs/hardware/POWER_DISTRIBUTION.md
  - docs/hardware/ESTOP_TOPOLOGY.md
  - docs/hardware/BOM.md
tags:
  - hcdc
  - hd064rt
  - power-distribution
  - fuse
  - tb6600
  - rp23cnc
related:
  - HW-20260819-002
  - HW-20260819-003
---

# Record HD064RT Output Allocation

## Summary

Recorded the actual eight-channel HCDC HD064RT distribution layout: RP23CNC is
on `OUT1`, the Pololu D36V50F6 is on `OUT4`, and the X, Y, and A TB6600 drivers
are on `OUT6`, `OUT7`, and `OUT8`, respectively. `OUT2`, `OUT3`, and `OUT5`
are intentionally unused.

## Reason

The earlier plan used `OUT1`–`OUT4` for the three TB6600s and the Pololu.
That does not match the project owner's actual DIN distribution layout and
would make both troubleshooting and fuse replacement error-prone.

## Implementation

The master table now ties the RP23CNC `FCTRL` branch to `OUT1` and each driver
to its actual output. It also records the selected starting fuse values: 2 A
for `OUT1` and `OUT6`–`OUT8`, plus 3 A intended for `OUT4`. These are planned
values, not claims that the physical fuses have already been fitted.

## Verification

Project-owner physical-layout report. Documentation indexes were regenerated
and validated. No continuity, fuse-marking inspection, current measurement, or
powered test was performed in this change.

## Struggles and rejected approaches

The previous sequential output assignment was retained only as a historical
plan. It was replaced rather than treating it as an alternate wiring option,
because the output numbers identify distinct physical fused branches.

## Risks and follow-up

With the machine de-energized, inspect and record each installed fuse marking,
then verify output polarity and conductor terminations. Before powered use,
complete the driver, regulator, current-budget, and E-19 checks. Leave the
three unused outputs open and marked unused.

## Files

- `docs/hardware/WIRING_TABLE.md`: authoritative branch conductor and fuse record.
- `docs/hardware/POWER_DISTRIBUTION.md`: current distribution narrative and table.
- `docs/hardware/ESTOP_TOPOLOGY.md`: controller branch and fused-output allocation.
- `docs/hardware/BOM.md`: installed distribution module allocation.
