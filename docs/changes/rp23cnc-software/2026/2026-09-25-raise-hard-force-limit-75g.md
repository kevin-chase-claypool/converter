---
id: RPSW-20260925-004
date: 2026-09-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - toolhead
  - force
  - hard-limit
---

# Raise the hard-force limit to 75 g

## Summary

Raised `HARD_FORCE_RAW_DELTA` from 65 g to 75 g (327520 -> 377908 raw), giving
the force envelope more headroom below the safety ceiling.

## Reason

The operator asked for more headroom above the 40 g target. The target and band
are unchanged (40 g, +/- 10 g), so the urgent relief at 55 g and the new 75 g
ceiling leave 20 g of headroom instead of 10 g.

## Implementation

- `toolhead_config.h`: `HARD_FORCE_RAW_DELTA` 327520 -> 377908 (65 g -> 75 g).
  The E-09C scale is 5,038.77 raw/g and its calibration covered 0-90 g, so
  75 g remains inside the measured range.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- Static checks: the `HARD_FORCE_RAW_DELTA > CONTACT_READY_TOLERANCE_RAW +
  HOLD_BAND_HEADROOM_RAW` assert still holds, and `activeTargetForceRaw()` no
  longer clamps the 40 g target (max target is now 55 g).

## Risks and follow-up

- 75 g is above the original 60 g selection and the 70 g candidate, but still
  inside the 0-90 g calibration. It gives the pen 15 g more authority than the
  original design, so it is worth watching for paper tearing or pen damage on
  fragile tools.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `firmware/pen_pressure/CONTROL_STRATEGY.md`
