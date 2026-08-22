---
id: RPSW-20260822-002
date: 2026-08-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - SparkFun Pro Micro RP2350 toolhead controller
  - TMAG5273 magnetic sensing
  - pen-pressure control
tags:
  - toolhead
  - rp2350
  - tmag5273
  - documentation-correction
related:
  - RPSW-20260822-001
  - E-18
  - ADR-002
---

# Correct RP2350 Toolhead Ownership

## Summary

Corrected current-state documents that still described a separate RP2040
magnetic adapter. The installed SparkFun Pro Micro RP2350 toolhead controller
owns both the pen-pressure system and TMAG5273 magnetic sensing/output.

## Reason

The separate RP2040 adapter was an earlier architecture. Retaining it in
current documentation incorrectly implied another MCU, connection, and
responsibility boundary that do not exist in the installed design.

## Implementation

Updated the firmware, architecture, interface, wiring, testing, handoff, and
current visual-overview documents to name the Pro Micro RP2350 as the TMAG5273
reader and magnetic-output owner. Historical change notes, engineering-log
entries, and dated lab evidence retain their original terminology when it
accurately describes the design or hardware used at that time.

Accepted ADR-002 and completed the corresponding roadmap item: the installed
Pro Micro RP2350 is the selected combined toolhead controller. This decision
does not select `LIMA` versus `PRB` for GP27/U3.

## Verification

- Searched current-state documents and overview artifacts for stale
  `RP2040 adapter`, `RP2040/TMAG5273`, and `Pro Micro RP2040` ownership claims.
- Parsed the changed HTML overview files and the photo-style SVG wiring view.
- Ran the documentation index generator and validator.

## Struggles and rejected approaches

Rejected rewriting dated historical records because doing so would erase the
project's actual architecture evolution and could misstate which board was
used for an earlier bench test.

## Risks and follow-up

The naming correction does not verify GP27 output behavior, RP23CNC input
compatibility, or the proposed PRB/G38 path. Those remain under E-18 and F-08.

## Files

- `README.md`: corrects the top-level subsystem summary.
- `firmware/README.md`, `firmware/grblhal/README.md`, and
  `firmware/pen_pressure/README.md`: align the firmware indexes and current
  controller responsibilities.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: corrects the primary
  magnetic-calibration ownership model.
- `docs/architecture/SYSTEM_ARCHITECTURE.md`: merges magnetic sensing into the
  Pro Micro RP2350 toolhead-controller subsystem.
- `docs/hardware/WIRING_TABLE.md`: explicitly records one combined toolhead
  controller without changing wiring.
- `docs/integration/INTERFACES.md`: corrects the controller ownership boundary.
- `docs/testing/TEST_PLAN.md`: renames E-18 for the installed RP2350 design.
- `docs/decisions/ADR-002-toolhead-placement.md`: accepts the installed Pro
  Micro RP2350 controller placement.
- `docs/project/ROADMAP.md`: closes the obsolete controller-placement decision.
- Current HTML/SVG overview artifacts: remove the depicted separate adapter and
  label the installed SparkFun Pro Micro RP2350 correctly.
