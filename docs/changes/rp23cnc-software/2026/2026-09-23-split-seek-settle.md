---
id: RPSW-20260923-012
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
  - contact-seek
  - latency
related:
  - RPSW-20260923-006
---

# Split the seek settle by proximity to the target

## Summary

The M3 seek now uses a 100 ms settle while the force is far below the target
band and the full 300 ms settle only within about 10 g of the contact
threshold. The contact decision itself still uses the full settle.

## Reason

Every pulse paid the 300 ms settle even though only the last one or two pulses
make a decision near the band. The early pulses only answer "am I still far
away", which the measured settle curve shows a 100 ms read answers within about
1 g — negligible against a 20 g decision margin.

## Implementation

- `toolhead_config.h`: added `HOME_SEEK_SHORT_SETTLE_MS` (100 ms) and
  `HOME_SEEK_FULL_SETTLE_NEAR_RAW` (50,388 raw, about 10 g).
- `pressure_controller.cpp`: `HOME_SEEK_CONTACT` now selects the settle based on
  how close the normalized force is to the contact threshold, and passes that
  settle into the pulse pacing. The contact threshold itself is unchanged.

The 60 g hard-force guard reads the filtered sample independently of the
settle, so it is unaffected. The coarse/fine force gates still end the coarse
phase early if the pen reaches paper sooner than expected.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 81800 bytes program storage and 16220 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench confirmation is required. Expected: warm M3 drops toward roughly
  1.1-1.4 seconds, with the contact declaration and held force unchanged.

## Struggles and rejected approaches

Lowering the single settle constant further was rejected: the 300 ms value is
the measured mechanical settle, and a shorter value on the contact decision
would reintroduce the mid-transient reads that caused the early overshoots.

## Risks and follow-up

The short settle only applies where the decision margin is large. If the force
per pulse ever rises sharply near the band, the "near" margin keeps the full
settle in force for that final stage. The 10 g near-margin is a bench
candidate; if the contact declaration begins overshooting, widen it.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: short settle and near-margin constants.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: proximity-based settle selection.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`: describe the split settle.
