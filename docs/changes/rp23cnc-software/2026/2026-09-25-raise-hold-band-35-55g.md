---
id: RPSW-20260925-005
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
  - hold-band
---

# Move the hold band to 35-55 g

## Summary

Raised the target and contact reference from 40 g to 45 g, moving the +/- 10 g
hold band to 35-55 g.

## Reason

The operator wanted the band shifted up 5 g, keeping the same width. With the
band symmetric about the target, 35-55 g means a 45 g target.

## Implementation

- `toolhead_config.h`: `TARGET_FORCE_RAW_DELTA` and `CONTACT_RAW_DELTA` 201551 ->
  226745 (40 g -> 45 g). `CONTACT_READY_TOLERANCE_RAW` (+/- 10 g) and
  `HARD_FORCE_RAW_DELTA` (75 g) are unchanged.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- Static checks: the target stays below the safety clamp (max target is now
  55 g) and the hard-limit assert still holds.

## Risks and follow-up

- Urgent relief is target + 15 g, so it moves from 55 g to 60 g. That leaves
  15 g of headroom to the 75 g ceiling (it was 20 g).
- The higher target presses harder, so it trades a little more friction and
  ink for a firmer hold.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `firmware/pen_pressure/CONTROL_STRATEGY.md`
