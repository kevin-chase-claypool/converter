---
id: RPSW-20260922-026
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
  - docs/testing/TEST_PLAN.md
tags:
  - cs1238
  - tare
  - lift-home
  - gp2
related:
  - RPSW-20260922-025
---

# Tare After Lift-Home Release

## Summary

The integrated M3 path now samples its live CS1238 zero only after GP2 changes
from pressed/home to released during the initial downward approach.

## Reason

The first two-touch run reported about 12 g while GP2 was pressed, exceeding
the 5 g surface threshold before motion began. The GP2 hard-home position
therefore applies a mechanical preload and is not a usable force zero.

## Implementation

M3 from GP2 ignores force while it uses coarse DOWN pulses to leave the switch.
At the first released sample it stops and sleeps for one second, takes the
64-sample tare, and resumes the light surface touch automatically. A boot or
recovery snapshot at GP2 reports `tare_valid=0` by design. Normal M3 from the
ordinary M5-clear position still requires the existing valid tare.

## Verification

- Arduino CLI compile passed for the SparkFun Pro Micro RP2350 target.
- The failed GP2-preload trace and corrective rationale are recorded in
  `docs/report/lab-notes/2026-09-22-t-02-home-contact-seek-setup.md`.

## Struggles and rejected approaches

Waiting longer while GP2 remained pressed was rejected: the trace showed that
the home switch position itself, rather than only startup motion, changes the
load-cell reading.

## Risks and follow-up

The one-second released-state settle is a supervised bench candidate. Confirm
post-release tare stability and the two-touch outcome under T-02 before
testing moving-force T-03 or production M3/M5 integration.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  GP2-release tare state.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  tare-settle value.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: current tare contract.
