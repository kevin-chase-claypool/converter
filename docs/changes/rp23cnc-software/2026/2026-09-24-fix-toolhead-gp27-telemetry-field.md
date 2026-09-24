---
id: RPSW-20260924-002
date: 2026-09-24
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - telemetry
  - magnetic-homing
  - e-18
---

# Report magnet detection instead of a compile flag in the `ready=[...]` field

## Summary

The toolhead snapshot's `ready=[...]` block no longer prints a misleading
`gp27:` value. It now prints `det:` with the live `STATUS_MAG_DETECTED` bit.

## Reason

During E-18 the operator saw `mag=READY_ACK ... ready=[contact:0 clear:0
gp27:0]` and read `gp27:0` as "the magnetic GP27 output is low". It was not:
the field was wired to `GP27_NORMAL_STATUS_ENABLED`, a compile-time constant
that is false by design, so it always printed `0` regardless of the real
GP27 magnetic output.

## Implementation

- `pro_micro_rp2350_toolhead.ino`: the snapshot format now emits
  `ready=[contact:%d clear:%d det:%d]`, and `det` is
  `statusFlag(STATUS_MAG_DETECTED)` (the shared atomic magnet-detected state)
  rather than the `GP27_NORMAL_STATUS_ENABLED` constant.

## Verification

- Compile-time only: format string and argument count match (three `%d` /
  three arguments). No parsing depends on the old field name. Historical lab
  notes keep the old `gp27:` captures as evidence and are unchanged.

## Struggles and rejected approaches

Reporting the raw GP27 pin was considered, but `output_active_` lives in the
core-1 magnetic controller; `STATUS_MAG_DETECTED` is already a shared atomic
the telemetry path can read safely.

## Risks and follow-up

None functional. Confirm GP27 to the controller through ioSender `Pn:P` as
before; `det:` now makes the magnet detection visible in the toolhead snapshot
too.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: telemetry field.
