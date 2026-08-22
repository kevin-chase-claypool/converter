---
id: HW-20260822-002
date: 2026-08-22
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - RP23CNC-to-toolhead PC817 harness
  - drag chains
tags:
  - toolhead
  - optocoupler
  - drag-chain
  - wiring
related:
  - docs/report/lab-notes/2026-08-22-toolhead-pc817-drag-chain-routing.md
---

# Route toolhead PC817 harness

## Summary

The five planned controller-side PC817 conductors have been routed through the
toolhead drag chains.

## Reason

The moving toolhead needs the isolated M3/M5, `HOME_ARM`, and reverse
`A_HOME` paths physically available before their endpoint and functional tests.

## Implementation

The routed harness comprises controller `5V`, spindle `ENA`, `Aux 0`,
controller-side `GND`, and `LIMA`/`A_HOME`. The PC817 J1 pin mapping remains
unchanged, and its unused J1.3 is not assigned.

## Verification

Owner report of completed drag-chain routing only. No electrical verification
or energized behavior is claimed.

## Struggles and rejected approaches

None reported.

## Risks and follow-up

The controller-side `ENA`, `Aux 0`, and `LIMA` endpoints remain deliberately
unconnected pending F-05/E-18. Verify each conductor end-to-end and prove
`CTRL_GND` is isolated from `TOOL_GND` before any powered connection.

## Files

- `docs/hardware/WIRING_TABLE.md`: records the routed harness and its current
  verification boundary.
- `docs/report/lab-notes/2026-08-22-toolhead-pc817-drag-chain-routing.md`:
  records the physical-routing milestone.
