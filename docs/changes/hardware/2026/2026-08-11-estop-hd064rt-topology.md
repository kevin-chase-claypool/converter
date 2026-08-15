---
id: HW-20260811-001
date: 2026-08-11
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: superseded
components:
  - docs/hardware/ESTOP_TOPOLOGY.md
  - docs/hardware/POWER_DISTRIBUTION.md
  - docs/hardware/WIRING_TABLE.md
tags:
  - emergency-stop
  - power-distribution
  - hd064rt
  - rp23cnc
related:
  - docs/testing/TEST_PLAN.md
  - HW-20260814-005
---

# Reconciled E-stop and HD064RT topology (superseded)

> Superseded by `HW-20260814-005`: the project uses the RP23CNC Halt input
> only. K1/D4 and relay-operated motor-energy removal are excluded.

## Summary

Recorded the installed HCDC HD064RT as the post-relay fused distribution point
for the X, Y, A, and toolhead-motor branches. The newly purchased mxuteuk 2NC
mushroom E-stop now has separate assignments for RP23CNC Halt and K1 relay-coil
interruption.

## Reason

Earlier advice incorrectly introduced redundant inline fuse holders despite the
installed eight-channel DIN distribution module. The safety and power topology
needed a single authoritative record before further parts or wiring decisions.

## Implementation

- Added `ESTOP_TOPOLOGY.md` with the net-level plan, component roles, HD064RT
  allocation, and E-19 verification procedure.
- Updated the power plan, master wiring table, BOM, integration invariants,
  test plan, and recommended test sequence.
- Kept unknown physical terminal labels, K1 part selection, wire gauges, and
  measured fuse values explicitly TBD.

## Verification

- Reviewed the RP23CNC user manual: its E-stop/Halt input is opto-isolated and
  requires the isolated 12 V control-input supply.
- Reviewed the HD064RT supplied identification and available product data:
  5-32 V operation, eight outputs, 20 A aggregate specification, and factory
  3 A fuses.
- No power has been applied to the documented topology; E-19 is required.

## Struggles and rejected approaches

The five-holder inline-fuse proposal was rejected because it duplicated the
installed HD064RT and conflicted with the existing documented DIN distribution
approach.

## Risks and follow-up

Select K1 and FMAIN/FCTRL parts only after confirming the physical terminal
layout and measuring branch current. Complete E-19 before connecting motors or
calling the arrangement operational.

## Files

- `docs/hardware/ESTOP_TOPOLOGY.md`: authoritative E-stop topology.
- `docs/hardware/POWER_DISTRIBUTION.md`: power-plan reconciliation.
- `docs/hardware/WIRING_TABLE.md`: planned safety connections.
- `docs/hardware/BOM.md`: received/purchased and required components.
- `docs/testing/TEST_PLAN.md`: E-19 test definition.
