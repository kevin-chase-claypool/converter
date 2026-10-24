---
id: RPSW-20261023-001
date: 2026-10-23
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
related:
  - RPSW-20261013-001
  - ADR-004
---

# Raise the M5 pen-clearance pulse to 130 ms

## Summary

`PEN_CLEAR_EXTRA_LIFT_MS` is raised from 90 ms to **130 ms** of full-drive UP
after the M5 force-release point. At the last measured actuator rate, this
targets about **2.28 mm** above the release point, 0.70 mm more than the prior
setting.

## Reason

The operator still observed insufficient pen clearance between moves with the
90 ms setting. This is a normal M5 height requirement, so changing the
converter's `Pen up ms` wait would not help: that setting controls how long the
host waits for clear-ready, not how far the actuator retracts.

## Implementation

- `toolhead_config.h` now sets `PEN_CLEAR_EXTRA_LIFT_MS` to `130`.
- The existing sequence is unchanged: prove force release, drive UP for the
  clearance interval, stop and sleep the driver, verify clear state, settle for
  300 ms, and refresh the clear-state tare.
- The clearance state still stops immediately if GP2 `LIFT_HOME` asserts.
- `PEN_CLEAR_VALID` remains true because this increases clearance above the
  T-01H-accepted 57 ms behavior; it does not alter release detection.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\pen_pressure\pro_micro_rp2350_toolhead`
  completed successfully: 83,048 bytes program storage and 16,280 bytes global
  dynamic memory.
- Source inspection confirmed M5 uses the constant only after normal
  `RELEASE_TO_CLEAR` and retains the GP2 stop guard.

The hardware checks remain open: measured 130 ms pen-tip gap, at least 30
no-drag M3/M5 cycles with representative X/Y travel, and first-try M3 contact
after the larger warm-seek travel.

## Struggles and rejected approaches

- Changing the converter's `pen_up_ms` was rejected because it changes wait
  duration rather than physical lift height.
- Reaching GP2 `LIFT_HOME` on every M5 was rejected because that adds a long
  full retract and unnecessary switch cycles to every stroke.

## Risks and follow-up

- The 2.28 mm value is an estimate from the E-09F rate, not a direct
  measurement of this mechanism at 130 ms.
- The larger gap increases each warm M3 approach by about 0.70 mm. The bounded
  seek budget and learned warm-seek average are expected to absorb it, but the
  next bench run must confirm first-try contact and no timeout.
- If drag remains at 130 ms, stop increasing the pulse blindly and separate
  actuator clearance from pen-tip geometry, clamp height, bed-height variation,
  and M3 contact acquisition.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  selects the new M5 clearance and records the change history.
- `firmware/README.md`, `firmware/pen_pressure/README.md`,
  `firmware/pen_pressure/CONTROL_STRATEGY.md`,
  `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`, and
  `software/README.md`: keep the current M5 timing, clearance estimate, host
  wait distinction, and open acceptance checks synchronized.
