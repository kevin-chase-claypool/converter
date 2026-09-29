# ADR-008: Cut the top-level architecture along integration seams

- Status: accepted
- Date: 2026-09-29

## Context

The project was documented by folder and by physical assembly. The previous
subsystem table mixed functional responsibilities (host converter, motion
controller) with equipment (stepper power stage, sensors), so it did not answer
at a consistent level which system owns an interface. The Systems Integration
in Robotics report needs a defensible highest-level decomposition, and the
project needs stable boundary names for seam ownership.

## Decision

Define level 0 as the plotter system of interest. Define eight level-1 systems:
five along the mission chain - 1 Host planning and operator, 2 Motion control,
3 Motion and actuation, 4 Toolhead and tool, 5 Sensing and feedback - and three
cross-cutting systems - 6 Power and energy, 7 Safety and fault handling, 8
Structure, cabling, and EMC. Retain the previous subsystem table as the physical
realization view. Every seam in `docs/integration/INTERFACES.md` names its two
systems, and a boundary change updates the architecture document, the interface
document, the ADR set, and a categorized change note together.

## Consequences

- Components such as the TB6600 drivers, CS1238, and TMAG5273 are level-2 items
  inside a system, not systems themselves.
- Every interface contract has a named owner pair, so impact analysis starts
  from the seam rather than from the folder layout.
- The report can present the five-system mission chain plus the three enabling
  systems, with the rotating-bed cable-wrap tradeoff as a worked cross-system
  example.
- The physical view is retained, so existing change notes and links that use
  the old names still resolve.
- Subsystem documents should state which level-1 system they belong to when
  they are next edited.
