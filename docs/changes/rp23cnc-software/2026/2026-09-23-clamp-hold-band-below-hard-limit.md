---
id: RPSW-20260923-001
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - t02
  - force-control
  - hard-limit
  - safety-margin
related:
  - RPSW-20260922-034
---

# Clamp the hold band below the hard-force limit

## Summary

The relative hold target is now clamped so the top of the acceptance band always
keeps 10 g of margin below the absolute 60 g hard-force limit. A high accepted
first-touch reference can no longer push the band onto the trip point.

## Reason

The 2026-09-23 four-cycle T-02 run passed three cycles and faulted on the
fourth with `hard force limit exceeded` at 303,401 raw against a 302,326 raw
limit. That cycle accepted a 78,727 raw (15.6 g) first touch, which put its
band top at 280,278 raw — only 22,048 raw (4.4 g) below the trip — and
post-hold creep then crossed it. The other three cycles accepted 38,886 /
46,551 / 42,697 raw and had 10-12 g of headroom, so the same creep stayed
under the limit.

The underlying arithmetic is a design defect: the 20 g reference cap, the 35 g
target, and the 5 g tolerance sum to exactly 60 g, so a maximum-reference cycle
would hold with the top of its acceptance band precisely on the hard-force
trip point.

## Implementation

- `toolhead_config.h`: added `HOLD_BAND_HEADROOM_RAW` (50,388 raw, about 10 g)
  and a compile-time check that the hard limit leaves room for the band plus
  its headroom.
- `pressure_controller.cpp`: `activeTargetForceRaw()` now clamps the requested
  `reference + TARGET_FORCE_RAW_DELTA` to
  `HARD_FORCE_RAW_DELTA - CONTACT_READY_TOLERANCE_RAW - HOLD_BAND_HEADROOM_RAW`
  (226,744 raw, about 45 g). The tune threshold and the contact-ready band both
  derive from that clamped value, so they move together.

The 20 g `HOME_SURFACE_REFERENCE_MAX_RAW` cap is unchanged. It is now a
plausibility check rather than the hard-limit guard.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 82272 bytes program storage and 16220 bytes dynamic memory.
- The clamp only binds above a 50,387 raw (10 g) reference, so the three
  passing cycles (38,886 / 46,551 / 42,697 raw) are numerically unaffected.
  The faulting cycle would have been clamped from a 255,084 raw target to
  226,744 raw, moving its band top from 280,278 to 251,938 raw.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

Lowering `HOME_SURFACE_REFERENCE_MAX_RAW` to roughly 12 g was rejected. It
would have converted the fourth cycle from a clamped pass into a
`surface response exceeds low-force contact range` fault, which reduces the
pass rate without improving safety once the target clamp exists.

## Risks and follow-up

The clamp gives the hold loop room to answer the observed post-hold creep; it
does not remove the creep. If a repeat still runs away, the next lever is
letting `HOLD_FORCE` relieve force immediately when it is far above target
instead of waiting out the three-window trend and the 250 ms cadence. The
reference cap should be re-tightened later only if repeat evidence shows high
touches are mis-detections rather than genuine coarse first contacts.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: add the headroom constant and its compile-time check.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: clamp the active target.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: document the band-top margin.
