---
id: HW-20260906-002
date: 2026-09-06
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB V1.01
  - X-axis TB6600 and 17HS15 motor
  - GT2 gantry drive
tags:
  - x-axis
  - rate
  - acceleration
  - dimensional-calibration
  - commissioning
related:
  - M-02
  - M-03
  - HW-20260905-005
  - HW-20260905-006
---

# Verify X-axis rate and dimensional calibration

## Summary

The unloaded X axis completed five matched 50 mm forward/reverse moves at
`F1500` with `$110=1500` mm/min and `$120=500` mm/sec^2. It returned exactly
to its reference mark. A separate 100 mm caliper check established and
verified `$100=79.71303` steps/mm.

## Reason

X had passed low-speed direction and return checks but still required a
repeatable working-motion setting and a measured physical travel calibration
before pen-free coordinated X/Y/A testing.

## Implementation

The reusable rate program is
[`docs/testing/gcode/x-axis-rate-repeat.gcode`](../../../testing/gcode/x-axis-rate-repeat.gcode).
It contains only pen-free relative X moves and restores absolute mode. The
calibration correction used the measured-scale relationship
`new_steps_per_mm = old_steps_per_mm * commanded_distance / measured_distance`.

## Verification

- Five `X50`/`X-50` pairs at `F1500` were smooth and returned exactly to the
  reference mark.
- `$100=80.000000` yielded 100.36 mm for a commanded 100 mm move.
- `$100=79.71303` yielded exactly 100 mm, and the matched reverse move returned
  exactly to the reference mark.
- M-02 and M-03 passed for their documented unloaded X-axis scopes.

## Struggles and rejected approaches

The initial 10 mm measurement was inaccurate and produced a provisional
`$100=88.88889`. It was rejected in favor of the longer 100 mm caliper result,
which was then independently verified.

## Risks and follow-up

The selected maximum rate/acceleration remains a preliminary unloaded setting;
no temperature observation was recorded in this X session. Homing/limits,
pen-free coordinated X/Y/A motion, and pen-loaded validation remain open.

## Files

- `docs/testing/gcode/x-axis-rate-repeat.gcode`: reusable pen-free M-02 test.
- `docs/report/lab-notes/2026-09-06-m-02-x-axis-rate-ramp.md`: M-02 evidence.
- `docs/report/lab-notes/2026-09-06-m-03-x-axis-dimensional-calibration.md`:
  M-03 evidence and calibration calculation.
- `docs/testing/TEST_PLAN.md`: current test-status summary.
- `docs/integration/INTERFACES.md`, `firmware/README.md`, and
  `firmware/grblhal/config/build-record.md`: current controller settings.
