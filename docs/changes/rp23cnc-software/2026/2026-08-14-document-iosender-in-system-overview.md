---
id: RPSW-20260814-006
date: 2026-08-14
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
status: implemented
components:
  - README.md
  - docs/START_HERE.md
  - docs/architecture/SYSTEM_ARCHITECTURE.md
tags:
  - iosender
  - system-overview
  - gcode
related:
  - firmware/grblhal/config/build-record.md
---

# Document ioSender in the system overview

## Summary

The system overview now shows ioSender as the host-side operational bridge
between saved converter G-code and grblHAL on RP23CNC.

## Reason

The prior overview incorrectly implied the host converter sent G-code directly
to firmware, omitting the sender used for streaming, configuration, console,
jogging, and machine status.

## Implementation

Updated the root overview, onboarding flow, and architecture subsystem table.
ioSender is described as a G-code sender/operator console, not as part of the
converter or motion controller.

## Verification

Reviewed the corrected flow against the installed RP23CNC/grblHAL and ioSender
bring-up workflow. Documentation index validation is required before commit.

## Struggles and rejected approaches

None.

## Risks and follow-up

The overview does not select USB versus Ethernet as the permanent operational
connection; that remains a machine commissioning decision.

## Files

- `README.md`: primary system-overview correction.
- `docs/START_HERE.md`: onboarding flow correction.
- `docs/architecture/SYSTEM_ARCHITECTURE.md`: explicit operator-console role.
