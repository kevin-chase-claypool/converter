---
id: RPSW-20260922-014
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - staged M3/M5 mechanical-preload controller
tags:
  - supervised-bench
  - mechanical-preload
  - moving-average-force-control
related:
  - RPSW-20260922-013
  - E-09C
  - E-09E
---

# Enable the mechanical-preload supervised bench build

## Summary

Enabled the staged mechanical-preload path for the user's supervised bench
test. This is not a production authorization.

## Reason

The user confirmed that the fixed 100 ms move is only for the initial drawing
preload/air gap, while the CS1238 moving average must guide the pen force after
the timed M3 move. The GP2 switch provides the coarse maximum-UP limit.

## Implementation

The checked-in test build now sets:

- `MECHANICAL_PRELOAD_MODE = true`
- `ACTUATOR_DIRECTION_VALID = true` from the E-09E direction check
- `PRESSURE_CALIBRATION_VALID = true` from the cap-free E-09C fit

`LIFT_REFERENCE_VALID`, `PEN_CLEAR_VALID`, `MAGNETIC_CALIBRATION_VALID`, and
`GP27_NORMAL_STATUS_ENABLED` remain false. M3 performs the 100 ms DOWN preload,
then the 16-sample CS1238 moving average applies bounded force corrections.
M5 performs the 100 ms UP air-gap move and stops if GP2 reaches `lift_home=1`.

The integrated sketch now accepts the same `?`, `p`, `t`, `e`, `l`, `a`, and `c`
commands on both native USB and the GP20/GP21 UART1 service link, so the
externally powered bench setup can be controlled through the UART adapter.

## Verification

The integrated sketch compiled successfully for
`rp2040:rp2040:sparkfun_promicrorp2350` after the gate change.

## Struggles and rejected approaches

Raw CS1238 seeking is not used to find initial paper contact because the bench
trace reached a nominal raw band while the pen remained physically air-gapped.

## Risks and follow-up

This build must be run with the physical cutoff reachable and with the pen
clear at boot. If the first supervised M3/M5 cycle is safe, record the filtered
force telemetry and any corrections. Revert `MECHANICAL_PRELOAD_MODE` and the
two test-valid flags before production firmware work unless the commissioning
evidence is formally accepted.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: enabled
  supervised test gates.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  timed preload, moving-average correction, and GP2 upper-limit behavior.
