---
id: RPSW-20260924-004
date: 2026-09-24
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - toolhead
  - force
  - calibration
---

# Raise the toolhead force envelope 5 g

## Summary

Moved the contact reference, hold target, and hard limit up 5 g together:
target 35 -> 40 g, contact reference 35 -> 40 g, hard limit 60 -> 65 g.

## Reason

The operator reported the pen sometimes losing contact with the paper during
printing. Raising the whole envelope by 5 g gives the hold more downward
authority to resist lift-off while keeping the relationship between the target,
the +/- 10 g band, and the hard ceiling intact.

## Implementation

- `toolhead_config.h`: `CONTACT_RAW_DELTA` 176357 -> 201551 (35 -> 40 g),
  `TARGET_FORCE_RAW_DELTA` 176357 -> 201551, `HARD_FORCE_RAW_DELTA`
  302326 -> 327520 (60 -> 65 g). The +/- 10 g band and 10 g headroom are
  unchanged, so the held band moves from 25-45 g to 30-50 g and the target
  stays below the safety clamp (max target is now 45 g).

The 65 g ceiling remains inside the E-09C 0-90 g calibration range.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- Static checks: the `HARD_FORCE_RAW_DELTA > CONTACT_READY_TOLERANCE_RAW +
  HOLD_BAND_HEADROOM_RAW` assert still holds, and `activeTargetForceRaw()` no
  longer clamps the 40 g target (max 45 g).
- Bench confirmation is outstanding: re-flash and run a print to confirm the
  pen no longer lifts off, and that the higher ceiling does not reintroduce
  hard-limit faults.

## Risks and follow-up

- Raising the hard limit to 65 g gives the pen 5 g more authority to push
  through paper and mechanical stops; it is within calibration but reduces the
  headroom margin the ceiling provides. Revert if it brings back
  `hard force limit exceeded` faults or if the extra pressure harms the pen.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
