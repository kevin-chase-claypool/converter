---
id: HW-20260823-001
date: 2026-08-23
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - RP23CNC-to-toolhead PC817 harness
  - RP23CNC controller-side terminals
tags:
  - toolhead
  - optocoupler
  - wiring
  - rp23cnc
related:
  - HW-20260822-002
  - docs/report/lab-notes/2026-08-23-rp23cnc-toolhead-control-partial-termination.md
---

# Partially terminate toolhead-control harness

## Summary

Four controller-side PC817 harness conductors are now wired at the RP23CNC:
`CTRL_5V`, `ENA`, `AUX0`, and `CTRL_GND`.

## Reason

The routed toolhead-control harness needed its supply, command, and isolated
ground conductors landed at the controller before its commissioning checks.

## Implementation

The owner supplied an annotated PC817 board image showing J1.1, J1.2, J1.4,
and J1.5 as the completed controller-side wires. J1.6 `A_HOME` remains
disconnected. No connection was made to RP23CNC `PRB`; that candidate remains
test-gated, with the installed return assignment still `LIMA`.

## Verification

Owner report and annotated image only. No continuity, isolation, polarity,
current, controller-state, or powered-operation test has been run.

## Struggles and rejected approaches

No electrical assumptions were made from the image: it does not show enough
controller-side detail to certify the exact terminal labels or behavior.

## Risks and follow-up

Perform power-off conductor continuity and `CTRL_GND`/`TOOL_GND` isolation
checks, then F-05/E-18. Keep J1.6 disconnected from `PRB`; F-08 is required
before any `LIMA` to `PRB` retermination.

## Files

- `docs/hardware/WIRING_TABLE.md`: records the partial termination state.
- `docs/report/lab-notes/2026-08-23-rp23cnc-toolhead-control-partial-termination.md`:
  records the evidence and verification boundary.
