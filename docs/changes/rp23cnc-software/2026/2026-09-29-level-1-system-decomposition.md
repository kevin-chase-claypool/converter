---
id: RPSW-20260929-003
date: 2026-09-29
category: rp23cnc-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - docs/architecture/SYSTEM_ARCHITECTURE.md
  - docs/integration/INTERFACES.md
  - docs/decisions/ADR-008-top-level-system-decomposition.md
  - docs/report/README.md
tags:
  - system-architecture
  - systems-integration
  - interfaces
  - documentation
  - project-management
related:
  - docs/architecture/SYSTEM_DATA_FLOW_RECORD.md
  - ADR-008-top-level-system-decomposition.md
---

# Define the level-1 system decomposition

## Summary

The architecture document now defines the plotter as a level-0 system of
interest with eight level-1 systems: five along the mission chain (host planning
and operator, motion control, motion and actuation, toolhead and tool, sensing
and feedback) and three cross-cutting systems (power and energy, safety and
fault handling, structure, cabling, and EMC). Every interface in the interface
document now names the two systems it joins.

## Reason

The previous subsystem table cut the machine by folder and physical assembly, so
a contract such as the M3/M5 tool signal could not be traced to one owner on
each side. The Systems Integration in Robotics report needs a decomposition
whose top level is defensible, and future impact analysis needs stable boundary
names.

## Implementation

Rewrote the Subsystems section of `docs/architecture/SYSTEM_ARCHITECTURE.md` as
a level-0 statement, a level-1 table with responsibility, seams, and integration
evidence for each system, a worked cross-system tradeoff (bed rotation versus
cable wrap), and the former table retained as the physical realization view.
Corrected the physical view's force-sensor entry from HX711 to CS1238, which is
the installed backend since the 2026-09-21 migration.

Added a Seam ownership section to `docs/integration/INTERFACES.md` that maps each
contract to its two systems, pointed the report outline in
`docs/report/README.md` at the architecture document, and added
`ADR-008-top-level-system-decomposition.md`.

## Verification

- Documentation-only change; no code, wiring, or configuration changed.
- Retained statements were compared against the file's previous revision.
- `python tools\docs_index.py --write` and `--check` passed.
- `git diff` reviewed for scope before staging.

## Struggles and rejected approaches

Cutting the top level by component (driver, sensor, motor) was rejected because
components are not independently integrable. Keeping only the folder-aligned
physical table was rejected because it leaves seam ownership undefined.

## Risks and follow-up

- The engineering log's newest entries are still written above the log's
  separator, so the generated topic index does not reach them. This entry
  follows the existing convention, and the roadmap's Known technical debt item
  tracks the repair.
- Documents under `software/`, `firmware/`, and `docs/` still describe their own
  scopes; they should name their level-1 system the next time each is edited.

## Files

- `docs/architecture/SYSTEM_ARCHITECTURE.md`: level-0 and level-1 systems,
  seams, worked tradeoff, and physical realization view.
- `docs/integration/INTERFACES.md`: seam ownership table.
- `docs/report/README.md`: report outline pointed at the system names and seams.
- `docs/decisions/ADR-008-top-level-system-decomposition.md`: decision record.
- `docs/project/ENGINEERING_LOG.md`: dated entry for this session.
- `docs/project/ROADMAP.md`: refreshed count on the existing engineering-log
  debt item.
