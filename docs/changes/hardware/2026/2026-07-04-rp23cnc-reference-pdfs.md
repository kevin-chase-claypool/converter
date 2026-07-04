---
id: HW-20260704-002
date: 2026-07-04
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - docs/hardware/references
  - firmware/grblhal/UPCOMING_CODING_STEPS.md
  - docs/hardware/BOM.md
tags:
  - rp23cnc
  - rp23u5xbb
  - references
  - manual
related:
  - RPSW-20260609-001
---

# RP23CNC Reference PDFs

## Summary

Archived local copies of the RP23CNC user manual and RP23U5XBB assembly
instructions so controller bring-up can reference stable offline documents.

## Reason

The bring-up plan depended on upstream PDF links only. Local copies make the
reviewed source material available in the repository alongside the board
inspection notes, wiring table, and firmware plan.

## Implementation

Downloaded the upstream PDFs into `docs/hardware/references/` and updated the
BOM and RP23U5XBB bring-up plan to link to the archived files while retaining
the upstream source links.

## Verification

- `Get-ChildItem docs\hardware\references` confirmed both archived PDFs exist.
- `Get-FileHash ... -Algorithm SHA256` completed for both archived PDFs.

## Struggles and rejected approaches

None.

## Risks and follow-up

The archived PDFs are snapshots. Check the upstream RP23CNC repository before
changing pin assignments, soldering assumptions, or firmware options, and
supersede these archives if upstream publishes a relevant revision.

## Files

- `docs/hardware/references/RP23CNC-user-manual.pdf`: archived upstream manual.
- `docs/hardware/references/RP23U5XBB-assembly-instructions.pdf`: archived
  upstream assembly instructions.
- `docs/hardware/BOM.md`: source links now include the archived PDFs.
- `firmware/grblhal/UPCOMING_CODING_STEPS.md`: bring-up source references now
  include the archived PDFs.
