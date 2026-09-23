---
id: RPSW-20260922-034
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - t02
  - contact-seek
  - settle
  - cs1238
  - force-control
related:
  - RPSW-20260922-032
---

# Settle the home contact seek on settled force

## Summary

The integrated toolhead now waits for the full 500 ms sensing settle before it
reads force during the T-02 home contact seek, force tune, and post-clear tare.
Contact is no longer declared from the post-drive mechanical transient.

## Reason

T-02 kept faulting on the same mechanism even though E-09F had already held
repeatably at 40.0 g / 40.4 g on the same load cell and motor. The difference
was timing: the integrated build read force 50 ms after a pulse, where E-09F
used 500 ms. E-09F's own lab note states the immediate post-drive reading is a
settling transient, not a valid force value. Reading it produced the observed
overshoot past the 60 g hard limit, the 45,706-195,497 raw contact-reference
scatter, and the false post-clear contact readings.

## Implementation

- `toolhead_config.h`: raised `HOME_SEEK_SETTLE_MS`, `HOME_TUNE_SETTLE_MS`, and
  `PEN_CLEAR_TARE_SETTLE_MS` from 50 ms to 500 ms. Recomputed
  `HOME_SEEK_TIMEOUT_MS` and `HOME_TUNE_TIMEOUT_MS` from 8 s / 7 s to 60 s so
  the bounded pulse sequences remain permissible, and extended the surface
  confirmation timeout to cover the settle plus three windows. Added a
  compile-time check for the tune timeout.
- `contact_seek_policy.h`: reordered the decision helper so a threshold
  crossing is only `CONTACT_FOUND` after the just-finished pulse has settled.
  Updated the constexpr regression cases to pin that behavior.
- `pressure_controller.cpp`: the first-touch confirmation now waits for the
  sensing settle before sampling the three confirmation windows, instead of
  reading the 0-150 ms post-pulse transient.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 82256 bytes program storage and 16220 bytes dynamic memory.
- `contact_seek_policy.h` static assertions pass, including a case that a
  threshold crossing during the settle returns `WAIT` rather than
  `CONTACT_FOUND`.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

The two-touch structure was retained rather than rewritten to E-09F's
single-approach form: the 500 ms settle is the dominant, highest-confidence
lever, and a full rearchitecture cannot be validated without the bench. The
relative first-touch reference and the ±5 g hold band are left unchanged; they
are T-03 concerns once the seek transition is stable.

## Risks and follow-up

The seek is now deliberately slower because settle time dominates each bounded
pulse; a supervised one-shot T-02 run is still required on hardware. The
absolute 60 g hard-force guard is unchanged. T-01J must still validate the
seek and clearance for each installed tool.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: settle and budget constants.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/contact_seek_policy.h`: settle-before-contact decision order and regression cases.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: settle-gated first-touch confirmation.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: align the documented seek timing with the code.
