---
id: RPSW-20260704-002
date: 2026-07-04
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/README.md
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
tags:
  - homing
  - calibration
  - toolhead
  - safety
related:
  - RPSW-20260704-001
---

# Pen-Up Calibration Workflow

## Summary

Made pen/toolhead lift an explicit precondition for RP23CNC homing and magnetic
bed-calibration scans.

## Reason

Homing and magnetic calibration move the gantry and rotating bed for reference
finding. Those moves should not depend on pen contact and should not risk
dragging the pen across the bed.

## Implementation

Updated the firmware overview and homing/calibration plan to command `M5`, wait
for a TBD verified lift dwell, and confirm physical clearance before X/Y homing,
bed-center scans, or A/theta index scans.

## Verification

- Documentation-only change reviewed against the existing homing/calibration
  responsibility split.

## Struggles and rejected approaches

None.

## Risks and follow-up

The actual lift dwell remains `TBD` until the toolhead lift timing is measured.
Bench tests must verify that reset, alarm, and E-stop states leave the toolhead
safe before integrated homing.

## Files

- `firmware/README.md`: added the pen-up precondition to the homing/calibration
  integration contract.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: updated the startup
  workflow to begin with `M5` and a verified lift-clearance check.
