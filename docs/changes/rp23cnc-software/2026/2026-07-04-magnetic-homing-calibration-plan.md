---
id: RPSW-20260704-001
date: 2026-07-04
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: planned
components:
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
  - firmware/grblhal/README.md
  - firmware/grblhal/UPCOMING_CODING_STEPS.md
  - firmware/README.md
  - docs/integration/INTERFACES.md
  - docs/hardware/WIRING_TABLE.md
  - docs/testing/TEST_PLAN.md
tags:
  - homing
  - tmag5273
  - rp2040
  - magnetic-calibration
  - grblhal
related:
  - RPSW-20260609-001
---

# Magnetic Homing Calibration Plan

## Summary

Documented the planned two-stage homing and magnetic bed-calibration approach:
grblHAL/RP23CNC handles X/Y/A motion and conventional digital homing, while a
TMAG5273 Hall sensor read by an RP2040 adapter provides magnetic scan readings
for the center and outer bed magnets.

## Reason

The rotating-bed plotter needs repeatable X/Y machine homing, bed-center
calibration, and theta/A index detection. The selected TMAG5273 is an I2C 3D
Hall sensor, while grblHAL's normal homing path expects physical or digital
home/limit inputs.

## Implementation

Added `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md` as the source of
truth for the unverified plan. It defines the responsibility split, the
host-coordinated scan architecture, saturated-field edge-centering method, and
the planned use of the RP23CNC Ethernet path after W5500 bring-up.

Updated firmware, interface, wiring, and test-plan documents to reflect the
TMAG5273/RP2040 adapter, center magnet, outer theta-index magnet, optional
conditioned `A_HOME` signal, and new verification tests.

## Verification

Documentation-only update. Hardware behavior, sensor thresholds, magnet
geometry, RP2040 output-driver design, RP23CNC input polarity, and scan
repeatability remain unverified.

`python tools\docs_index.py --write` and `python tools\docs_index.py --check`
must pass before this session is complete.

## Struggles and rejected approaches

Directly reading the TMAG5273 from a grblHAL plugin was rejected for first
bring-up because it adds custom real-time firmware complexity before a specific
grblHAL limitation has been proven.

Treating the center magnet as a theta reference was rejected because a magnet on
the bed rotation axis can locate center but cannot define angular phase.

## Risks and follow-up

The plan depends on a repeatable saturated or thresholded magnetic footprint
with visible edges. If the magnetic footprint fills the scan window or is
distorted by nearby ferromagnetic material, the fixed sensor mount, magnet
geometry, scan window, or thresholds must change before constants are recorded.
The TMAG5273 Z height is not an operational adjustment because the sensor is
fixed to the toolhead with heat-set inserts.

The RP2040 adapter output must not be wired directly to RP23CNC until the
opto-isolated input requirements and a switch-like output driver are verified.

## Files

- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: new current-state
  plan for homing and magnetic bed calibration.
- `firmware/README.md`: links the firmware overview to the homing/calibration
  plan.
- `firmware/grblhal/README.md`: updates the grblHAL to-do list with the
  planned TMAG5273/RP2040 approach.
- `firmware/grblhal/UPCOMING_CODING_STEPS.md`: keeps magnetic calibration out
  of custom grblHAL code until a limitation is proven.
- `docs/integration/INTERFACES.md`: documents the host, grblHAL, RP2040, and
  TMAG5273 logical interfaces.
- `docs/hardware/WIRING_TABLE.md`: adds unverified magnetic adapter and magnet
  placement wiring/mechanical placeholders.
- `docs/testing/TEST_PLAN.md`: adds verification rows for the magnetic adapter,
  center scan, and theta-index scan.
