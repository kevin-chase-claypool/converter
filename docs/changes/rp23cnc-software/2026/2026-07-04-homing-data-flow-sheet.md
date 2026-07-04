---
id: RPSW-20260704-003
date: 2026-07-04
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - docs/homing_data_flow.html
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
  - firmware/grblhal/UPCOMING_CODING_STEPS.md
  - docs/HANDOFF.md
  - docs/architecture/SYSTEM_ARCHITECTURE.md
tags:
  - homing
  - data-flow
  - grblhal
  - tmag5273
  - toolhead
related:
  - RPSW-20260704-001
  - RPSW-20260704-002
  - HW-20260704-003
---

# Homing Data Flow Sheet

## Summary

Added a standalone HTML data-flow sheet for the intended normal startup homing
workflow.

## Reason

The homing design spans ioSender, grblHAL on RP23CNC, the RP2040/TMAG5273
magnetic adapter, and the toolhead controller. The project needed a single
operator-facing and engineering-facing sheet that states what each component
must provide.

## Implementation

Created `docs/homing_data_flow.html` with a normal startup homing overview that
uses straight, routed connectors and explicitly exits at the
homing-complete/ready state, a bed-center calibration flowchart, an A-axis
magnetic homing subflow using two required bed revolutions, step-by-step normal
startup homing table, per-microcontroller requirements, setup-calibration versus
normal startup homing responsibilities, verification gates, and open TBDs. Added
matching color references in the normal startup overview and colored frames
around the bed-center and A-axis detailed flows so their ownership inside the
overall homing process is visible. Consolidated the RP2040 and TMAG5273 into one
ordered magnetic-adapter box in the normal overview, from fixed-height magnetic
sensing through I2C interpretation, threshold filtering, and A_HOME output.
Re-routed the normal startup overview into a grid with separated connector lanes
for status, home inputs, A_HOME, magnetic field, STEP/DIR, and homing-complete
paths. Added explicit exit bubbles to the bed-center calibration and A-axis
magnetic homing subflow diagrams. Clarified that <code>M5</code> is a command
interpreted by grblHAL, which then sets a spindle/tool output pin state used as
the toolhead LIFT signal, rather than text output sent onward. Reworded TMAG5273
references from fixed-Z language to fixed installed sensor height so the sheet
does not imply a Z-axis sensor; the unused Z axis exists only because the grblHAL
builder uses a four-axis configuration to expose A with X/Y. Added a separate
abort/fault data flow covering motion stop, lifted toolhead state, RP2040
diagnostics, ioSender reporting, and explicit user recovery before retrying.
Matched the `Abort if` box outlines in the bed-center and A-axis subflow diagrams
to the red abort/fault data-flow frame. Set the abort exit text to the standard
light SVG text color and made the A-axis compute-to-move connector a straight
horizontal arrow from the right side of the compute-index box into the center of
the move-to-index box. Synchronized the highest-priority interface, firmware, and
test-plan documents with the validated-A_HOME normal homing workflow. Also
synchronized the grblHAL upcoming coding steps, handoff, and system architecture
documents with the same Z-unused four-axis configuration, spindle/tool output
state, setup-calibration, abort-recovery, and normal-startup `A_HOME` contract.
Linked it from the grblHAL homing and magnetic calibration plan.

## Verification

- Documentation-only change; reviewed for consistency with the current
  fixed-height TMAG5273 and pen-up homing requirements.

## Struggles and rejected approaches

None.

## Risks and follow-up

The sheet documents the intended simplified normal startup workflow, the
bed-center calibration scan, and the A-axis magnetic homing subflow. The normal
A scan requires two full bed revolutions (`8640` A motor degrees), records two
entry/exit pairs, validates agreement, and averages the two computed centers.
It still depends on
hardware verification of the RP23CNC input circuit, RP2040 output driver,
magnetic thresholds, A offset, accepted magnet-field width,
center-agreement tolerance, center-scan edge repeatability, and toolhead lift
timing.

## Files

- `docs/homing_data_flow.html`: new data-flow and requirements sheet.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: links to the data-flow
  sheet from the current homing plan.
- `firmware/grblhal/UPCOMING_CODING_STEPS.md`: aligns grblHAL bring-up steps
  with validated `A_HOME`, fixed-height magnetic setup calibration, and unused Z.
- `docs/HANDOFF.md`: updates RP23CNC setup handoff tasks with the current
  normal startup homing and abort/fault contract.
- `docs/architecture/SYSTEM_ARCHITECTURE.md`: adds the magnetic homing adapter
  subsystem and clarifies grblHAL ownership of startup homing.
