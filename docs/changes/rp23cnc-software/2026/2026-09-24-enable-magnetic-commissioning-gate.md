---
id: RPSW-20260924-001
date: 2026-09-24
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
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

- No `static_assert` depends on the flag, so the gate change is verified by
  behavior, not compilation.
- 2026-09-24, integrated-firmware E-18/M-08/M-09 run. The operator confirmed
  `commission=[dir:1 pressure:1 lift:0 mag:1]` in the toolhead service stream,
  which proves the gated build was the one running, then issued `G65 P113`.
- Arm/release/re-arm: every `M65 P0`/`M64 P0` pair cycled
  `DISARMED -> READY_ACK -> WAIT_REARM -> SCAN_ACTIVE -> DISARMED`. The earlier
  `P100 READY acknowledgement missing` abort no longer occurs.
- TMAG detection: `delta` `0.257 -> 3.117 -> 30.287 -> 41.853` mT with the
  `MAG_DETECTED` status bit set (`0x000001ef`), returning to `0.019-0.092` mT
  far-field with the bit clear.
- P100 Q0 completed the center raster, the centroid approach, the outer
  two-footprint A survey, and both deferred `G54` writes, printing
  `P100 outer magnet registered as G54 A0`,
  `P100 center registered so G54 X0 Y0 is pen-at-center`,
  `P100 HOME + REGISTER complete`, and
  `P113 HOME + REGISTER wrapper complete`.
- Recorded result: TMAG centroid `MPos:-232.138,-219.475`; `G54` work offset
  `-232.136,-189.980,0.000,5649.193`; outer A footprints `1264.951/1369.576`
  and `5597.106/5701.281`, spacing `4331.930` A motor degrees against the
  `4320 +/- 15` gate.
- Evidence: `docs/report/lab-notes/2026-09-24-e-18-m-08-p113-integrated-registration.md`.

## Struggles and rejected approaches

Running E-18/M-08 with the ungated `p100_handshake_test` firmware was rejected
as the release path because it is not the production dual-core firmware; the
goal is to verify the exact integrated build that will run in production.

## Risks and follow-up

The arm still requires, at run time: TMAG online, a fresh far-field baseline, a
LIFTED pen with the LIFT_HOME switch active, and no pressure/driver fault.
Those conditions were met for the run above; keep the toolhead, pen, and magnet
path under supervision until the visual pen-centered check is recorded.
Revert this flag immediately if the integrated arm/scan faults.

Two robustness gaps were exposed and are not fixed here:

1. An earlier attempt in the same session faulted at exactly `MAG_MAX_ARM_TIME_MS`
   (`300000` ms) after `SCAN_ACTIVE` began, so the arm watchdog - not a `P100`
   validation - aborted it. The raster consumed roughly 172 s before it first
   reached the magnet, leaving little of the window for the rest of Q0.
2. The A spacing gate consumed 79.5% of its `+/- 15` degree budget, and the last
   two independent measurements agree at about `+11.9` degrees. That leaves
   only ~3 degrees of margin before `P100 A index spacing validation failed`.

Both are recorded in `docs/project/ROADMAP.md` for follow-up.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: gate enablement.
