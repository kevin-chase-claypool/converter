---
id: RPSW-20260925-008
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
  - high-speed
---

# Widen the force-hold band to ±15 g (30-60 g)

## Summary

Widened the target-ready hold band from ±10 g (35–55 g) to ±15 g (30–60 g) and
moved the urgent over-force relief trigger from 15 g to 20 g above target, so
high-speed friction spikes no longer lift the pen off the page.

## Reason

At faster print speeds the ±10 g band was still tight enough that transient
friction/rotation forces occasionally crossed the band top and triggered a
retract-only correction, lifting the pen mid-stroke. The wider band lets the
hold tolerate that drift before correcting.

## Implementation

- `toolhead_config.h`: `CONTACT_READY_TOLERANCE_RAW` `50388 -> 75582` (±15 g).
  `HOLD_URGENT_RELIEF_RAW` `75582 -> 100775` (20 g above target), keeping the
  relief trigger 5 g above the new 60 g band top so the relief/stop hysteresis
  is preserved and a retract/rebuild limit cycle cannot return. The 75 g hard
  limit still leaves 10 g of headroom above the 65 g relief trigger.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly. The `HARD_FORCE_RAW_DELTA > CONTACT_READY_TOLERANCE_RAW +
  HOLD_BAND_HEADROOM_RAW` static assertion still holds.

## Struggles and rejected approaches

Keeping the relief trigger at 15 g above target while widening the band to
±15 g was rejected: it would make the relief trigger exactly equal the band
top, removing the 5 g hysteresis and re-introducing the pen-poking limit cycle
the original design removed.

## Risks and follow-up

- This is a supervised bench choice, not a precision setting. Re-check the
  fastest intended feed rate for uncommanded contact loss or hard-limit trips.
- If high-speed drops still occur, the band can go wider, but the hard limit
  (75 g) then constrains the remaining relief/headroom margin.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `firmware/pen_pressure/CONTROL_STRATEGY.md`
- `firmware/pen_pressure/README.md`
