---
id: RPSW-20260924-001
date: 2026-09-24
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - p100
  - magnetic-homing
  - e-18
  - m-08
  - commissioning
---

# Enable the integrated toolhead magnetic commissioning gate

## Summary

Set `MAGNETIC_CALIBRATION_VALID = true` in the integrated toolhead firmware so
the dual-core arm/scan path can run the E-18/M-08 verification and the P100/P113
magnetic registration. Before this, the production toolhead refused the P100
arm and every `G65 P113` aborted with `P100 READY acknowledgement missing`.

## Reason

P100 asserts the arm on GP28 and then waits for the toolhead to answer on
GP27/PRB. `MagneticHomingController::prerequisitesReady()` requires
`MAGNETIC_CALIBRATION_VALID`; it was `false`, so the toolhead entered
`FAULT` ("magnetic readiness prerequisites not met") and never asserted GP27,
which surfaced as `P100 READY acknowledgement missing` and `error 39`. The
magnetic interface had already passed the motor-inert GP28->GP27 handshake
(E-18), F-08 PRB capture, and the 2026-09-11 P113/Q0 centroid raster plus A
registration, so the production gate was the only remaining block.

## Implementation

- `toolhead_config.h`: `MAGNETIC_CALIBRATION_VALID` changed `false -> true`
  with a dated comment. No other gate changed (`LIFT_REFERENCE_VALID` and
  `PEN_CLEAR_VALID` remain false).

## Verification

- Compile-only at this point: no `static_assert` depends on the flag.
- PENDING: the integrated-firmware E-18/M-08 run must confirm arm/release/
  re-arm, TMAG `detected=0->1->0`, the P100 Q5 centroid raster, and a clean
  `G65 P113` registration. Record the MPos/G54 result before calling it verified.

## Struggles and rejected approaches

Running E-18/M-08 with the ungated `p100_handshake_test` firmware was rejected
as the release path because it is not the production dual-core firmware; the
goal is to verify the exact integrated build that will run in production.

## Risks and follow-up

The arm still requires, at run time: TMAG online, a fresh far-field baseline, a
LIFTED pen with the LIFT_HOME switch active, and no pressure/driver fault. Keep
the pen, toolhead, and magnet path under supervision until the integrated run
is recorded. Revert this flag immediately if the integrated arm/scan faults.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: gate enablement.
