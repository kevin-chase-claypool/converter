---
id: HW-20260905-005
date: 2026-09-05
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB V1.01
  - Y-axis TB6600 and 17HS15-1504S-X1 motor
  - GT2 gantry drive
tags:
  - y-axis
  - rate
  - acceleration
  - commissioning
related:
  - M-02
  - HW-20260905-004
  - docs/report/lab-notes/2026-09-05-m-02-y-axis-rate-ramp.md
---

# Verify the Y-axis rate and acceleration baseline

## Summary

The unloaded Y axis passed the stepped bidirectional rate check without
skipped steps, stalls, or jerking. The operator selected `$111 = 1500` mm/min
and `$121 = 500` mm/sec^2 as the preliminary Y-axis settings for continued
commissioning.

## Reason

The X/Y gantry had passed low-speed direction and return checks, but Y needed
an unloaded rate/acceleration check before coordinated motion and toolhead
testing.

## Implementation

With the pen retracted, the operator ran matched `Y5`/`Y-5` moves at `F60`,
`F120`, `F240`, `F360`, and `F500` in `G94` millimeter feed mode. After those
steps passed, `$111` was raised from the initial `500` to `1500` mm/min and
`$121` from `10` to `500` mm/sec^2`; the resulting motion was reported smooth.

## Verification

- Every conducted stepped Y move completed successfully in both directions.
- No skipped steps, stalls, or jerking were observed.
- The post-change motion at `$111=1500` and `$121=500` was acceptable for
  continued commissioning.
- M-02 passed for the conducted unloaded Y-axis check and preliminary settings.

## Struggles and rejected approaches

The first `G1 Y5 F60` attempt returned grblHAL error 22 because the feed-rate
modal state was not valid. Establishing `G21` and `G94` before retrying fixed
the issue; all subsequent stepped commands were accepted.

## Risks and follow-up

The selected values are preliminary unloaded settings, not a final plotter
rate under pen load. A longer constant-speed move, coordinated X/Y/A test,
and toolhead-loaded validation remain.

## Files

- `docs/report/lab-notes/2026-09-05-m-02-y-axis-rate-ramp.md`: records the
  commands, settings, error recovery, and result.
- `docs/testing/TEST_PLAN.md`: records Y's M-02 evidence and remaining X work.
- `docs/integration/INTERFACES.md`: records the current Y commissioning
  baseline.
- `firmware/README.md`: updates the motion commissioning status.
- `firmware/grblhal/config/build-record.md`: records the bench settings as
  preliminary, not final production limits.
- `docs/project/ENGINEERING_LOG.md`: records the completed Y milestone.
