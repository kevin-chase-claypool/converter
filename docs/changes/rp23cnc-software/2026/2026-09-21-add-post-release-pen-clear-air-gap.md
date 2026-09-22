---
id: RP23CNC-20260921-008
date: 2026-09-21
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
tags:
  - pen-clear
  - air-gap
  - n20
  - cs1238
  - t-01h
related:
  - docs/testing/TEST_PLAN.md
---

# Add post-release pen-clear air-gap pulse

## Summary

Normal M5 source behavior now verifies the CS1238 no-contact release band
before running a separate temporary 500 ms N20 lift pulse to create pen-tip
clearance for between-line travel.

## Reason

An unloaded load cell does not prove an air gap. The clearance motion must be
sequenced after confirmed release, rather than being a fixed retract followed
by a later release check.

## Implementation

- Preserved the boot/recovery `LIFTING` sequence as a bounded 700 ms lift.
- Added `RELEASE_TO_CLEAR`, which retracts until the existing filtered
  no-contact tolerance and debounce-window criteria pass or faults at its
  bounded timeout.
- Added `CLEARANCE_LIFT`, which continues the same retract direction for
  `PEN_CLEAR_EXTRA_LIFT_MS = 500` before rechecking release and permitting
  `CLEAR_READY`.
- Kept every actuator, calibration, `PEN_CLEAR_VALID`, and GP27 gate false.

## Verification

- RP2350 Arduino compilation passed.
- No N20, load cell, paper, or controller hardware was energized by this
  source-only change.

## Struggles and rejected approaches

The earlier staged code used one fixed lift duration and then verified release.
That could not establish that the extra travel occurred after release, so it
was not suitable for defining an explicit air-gap pulse.

## Risks and follow-up

The 500 ms value is a temporary requested starting point, not a measured gap.
T-01H must measure its pen-tip clearance and verify at least 30 contact/clear
cycles before it can be accepted or any relevant gate can be enabled.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: staged
  timing constants.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.*`:
  explicit normal-M5 states.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: state-sequence source of truth.
- `docs/testing/TEST_PLAN.md`: T-01H evidence requirements.
