---
id: WSW-20260905-005
date: 2026-09-05
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - docs/HANDOFF.md
  - software/README.md
  - firmware/README.md
  - firmware/grblhal/README.md
  - firmware/grblhal/UPCOMING_CODING_STEPS.md
  - firmware/pen_pressure/README.md
  - firmware/pen_pressure/CONTROL_STRATEGY.md
tags:
  - documentation
  - consolidation
  - source-of-truth
  - grblhal
  - toolhead
related:
  - docs/project/ROADMAP.md
  - docs/integration/INTERFACES.md
  - docs/testing/TEST_PLAN.md
---

# Consolidate current documentation ownership

## Summary

Eliminated redundant current-state narratives while retaining historical plans
and links at their stable paths.

## Reason

A read-only documentation audit found overlapping live task lists, duplicated
toolhead behavior descriptions, and an obsolete converter default-Z warning in
the historical handoff.

## Implementation

The converter README and integration interface now own live G-code behavior.
The pen-pressure README owns implementation/status while `CONTROL_STRATEGY.md`
owns behavior and tuning policy. The roadmap and test plan own active RP23CNC
work; the June grblHAL bring-up plan and code-simplification plan are explicitly
marked historical. Historical files remain in place to preserve references from
change notes and the engineering log.

## Verification

- Reviewed the current documentation map, core subsystem documents, and all
  incoming Markdown references to the consolidated files.
- Ran documentation index write/check and local Markdown-link validation.

## Struggles and rejected approaches

Deleting historical plan files was rejected because many dated records link to
their existing paths. Marking them as archived retains evidence without
presenting them as active work.

## Risks and follow-up

The 2026 engineering log remains intentionally large because its entries are
current-year history. Archive completed calendar years when the repository
policy allows; do not delete chronological evidence during ordinary cleanup.

## Files

- `docs/HANDOFF.md`: historical converter rationale, no longer a live contract.
- `software/README.md` and `docs/integration/INTERFACES.md`: live converter
  contract ownership.
- `firmware/README.md` and `firmware/grblhal/README.md`: current controller
  status and source links.
- `firmware/grblhal/UPCOMING_CODING_STEPS.md` and
  `docs/SIMPLIFICATION_PLAN.md`: archived historical plans.
- `firmware/pen_pressure/README.md` and
  `firmware/pen_pressure/CONTROL_STRATEGY.md`: separated implementation/status
  from behavioral design/tuning ownership.
