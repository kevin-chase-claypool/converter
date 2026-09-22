---
id: RPSW-20260922-025
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
  - force-control
  - n20
  - surface-touch
related:
  - RPSW-20260922-024
---

# Add Two-Touch Home Approach

## Summary

M3 from full GP2 retract now locates paper with a light first touch, backs off,
and performs a separate fine approach for drawing force.

## Reason

Bench evidence showed the toolhead can traverse home-to-paper distance and
reach appropriate contact force, but asking a single final approach to both
detect paper and establish preload permits contact dynamics to affect the
drawing-force decision.

## Implementation

The first surface seek uses 25 ms pulses while distant and 5 ms pulses near an
approximately 5 g threshold. A single 10 ms UP back-off follows. The second
stage uses only 5 ms DOWN pulses to the 30 g lower edge of the existing 30–40
g hold band. Surface detection and force tuning have independent pulse/time
bounds; all sensor, driver, GP2, and 60 g hard-force protections remain.

## Verification

- Arduino CLI compile passed for the SparkFun Pro Micro RP2350 target.
- The relevant physical trace and rationale are recorded in
  `docs/report/lab-notes/2026-09-22-t-02-home-contact-seek-setup.md`.

## Struggles and rejected approaches

The single-touch 35 g approach was rejected for this startup path because it
couples long unloaded travel with the final drawing-force landing. Increasing
the hard limit would not resolve that coupling.

## Risks and follow-up

The 5 g first touch, 10 ms back-off, and 30 g tune threshold are supervised
bench candidates. Run T-02 and stationary T-03 with a reachable cutoff before
using the production M3/M5 path or drawing on paper.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  two-touch state sequence.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  staged touch constants.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: current behavior contract.
