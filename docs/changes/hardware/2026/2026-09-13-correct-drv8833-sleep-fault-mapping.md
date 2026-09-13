---
id: HW-20260913-001
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - hardware/pc817-interface
  - firmware/pen_pressure
tags:
  - drv8833
  - toolhead
  - wiring
  - pen-pressure
related:
  - docs/testing/TEST_PLAN.md
  - docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md
---

# Correct confirmed DRV8833 sleep/fault mapping

## Summary

The installed DRV8833 harness remains physically unchanged: `GP6` connects to
`EEP`, and `GP7` connects to `ULT`. Firmware now assigns `EEP` as the
low-true sleep input and `ULT` as the low-true fault output.

## Reason

The owner confirmed the silkscreen on the installed board: pin 1 is
`SLEEP`/`EEP`, and pin 6 is `FAULT`/`ULT`. Earlier project records assigned
those two labels the opposite roles. The E07B service sketch accepted commands
but did not move the replacement N20, so the incorrect enable/fault pin roles
had to be removed before further pressure testing.

## Implementation

- Preserved the existing soldered harness; no physical wire move is required.
- Updated the staged actuator sketches and integrated toolhead configuration
  to drive GP6 high for driver enable and read GP7 as an active-low fault.
- Updated the wiring table, BOM, test plan, and roadmap. Earlier contrary
  mapping statements are explicitly superseded instead of silently erased.

## Verification

- Owner-confirmed installed-board label image: `EEP` = SLEEP, `ULT` = FAULT.
- Source mapping was updated in E05, E07B, bench-motor, and integrated
  toolhead firmware.
- Compilation and powered E-14C/T-01 verification remain required after the
  E07B reflash.

## Struggles and rejected approaches

Earlier records relied on an opposite module-label interpretation. Rewiring
was rejected because the existing physical harness matches the owner-confirmed
board labels; correcting the firmware is the smaller, reversible change.

## Risks and follow-up

Do not resume automatic force testing until E07B has been reflashed and a
guarded `u`/`d` pulse proves that the driver enables and the fault input is
inactive. Record J2 bridge state and the repeat evidence in E-14C.

## Files

- `firmware/pen_pressure/*`: corrected DRV8833 sleep/fault pin roles.
- `docs/hardware/WIRING_TABLE.md`: canonical as-built mapping.
- `docs/hardware/BOM.md`: corrected installed-module description.
- `docs/testing/TEST_PLAN.md`: reopened E-14B/E-14C until the corrected map is
  function-tested.
