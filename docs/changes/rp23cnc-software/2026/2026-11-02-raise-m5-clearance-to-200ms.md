---
id: RPSW-20261102-001
date: 2026-11-02
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
tags:
  - toolhead
  - pen-clear
  - m5
  - clearance
  - drag
  - owner-override
related:
  - RPSW-20261023-001
  - ADR-004
---

# Raise the M5 pen-clearance pulse to 200 ms

## Summary

`PEN_CLEAR_EXTRA_LIFT_MS` is raised from 130 ms to **200 ms** of full-drive UP
after the M5 force-release point. At the last measured actuator rate, this
targets about **3.50 mm** above release, 1.23 mm more than the prior value.

## Reason

The project owner explicitly directed the clearance pulse to be 200 ms after
the 130 ms setting remained unsatisfactory.

## Implementation

- `toolhead_config.h` now sets `PEN_CLEAR_EXTRA_LIFT_MS` to `200`.
- The normal M5 sequence is unchanged: confirm force release, drive UP for the
  clearance interval, stop and sleep the driver, wait 300 ms, take a fresh
  64-sample clear-state tare, and reach `LIFTED`/clear-ready.
- The clearance move still stops immediately if GP2 `LIFT_HOME` asserts.
- `PEN_CLEAR_VALID` remains true because this increases clearance above the
  T-01H-accepted 57 ms behavior; it does not alter release detection.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\pen_pressure\pro_micro_rp2350_toolhead`
  completed successfully: 83,048 bytes program storage and 16,280 bytes
  global dynamic memory.
- Source inspection confirms M5 applies the constant only after force
  release and retains the GP2 stop guard.

The hardware checks remain open: measured 200 ms pen-tip gap, at least 30
no-drag M3/M5 cycles with representative X/Y/A travel, first-try M3 contact
after the larger warm-seek travel, confirmation that GP2 is not pressed during
ordinary M5, and the 100-pulse/60-second seek budget.

## Struggles and rejected approaches

The 2026-10-29 drag evidence recommended measuring the installed build and
resolving pen-tip/clamp geometry before increasing the pulse again. The owner
overrode that recommendation and selected 200 ms so a significantly larger
clearance can be evaluated directly.

Changing the converter's `pen_up_ms` was not used because it controls the host
wait, not physical lift height. Using every M5 to retract fully to GP2 remains
rejected because it adds a long full retract and unnecessary switch cycles to
every stroke.

## Risks and follow-up

- The 3.50 mm value is an estimate from the E-09F rate, not a direct
  measurement at 200 ms.
- The larger gap increases each warm M3 approach. The bounded seek budget and
  learned warm-seek average must still acquire paper without timeout.
- If drag remains, separate actuator clearance from pen-tip geometry, clamp
  height, bed-height variation, and M3 contact acquisition instead of
  increasing the pulse blindly again.

Run `samples/gcode/pen-clear-no-drag-30.gcode` after flashing and capture the
normal-M5 force trace plus measured pen-tip gap.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  selects the 200 ms clearance pulse and records its history.
- `firmware/README.md`, `firmware/pen_pressure/README.md`,
  `firmware/pen_pressure/CONTROL_STRATEGY.md`,
  `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`,
  `docs/project/ROADMAP.md`, and `software/README.md`: keep current timing,
  host/controller behavior, and the open physical acceptance checks aligned.
