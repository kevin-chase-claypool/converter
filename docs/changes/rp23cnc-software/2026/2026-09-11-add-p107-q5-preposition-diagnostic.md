---
id: RPSW-20260911-007
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P107.macro
tags:
  - P100
  - P107
  - Q5
  - diagnostic
  - homing
  - safety
related:
  - RPSW-20260911-006
---

# Add P107 Q5 Preposition Diagnostic

## Summary

Added a minimal, bounded-motion diagnostic that separates Q5's first G53 move
from its handshake and raster stages.

## Reason

The operator observed what appeared to be three further X/Y limit-switch
approaches after Q5. The controller's rolling console cannot retain the full
Q5 trace, so repeating the full raster would not produce a sufficiently tight
diagnostic signal.

## Implementation

P107 requires a preceding Q2 and performs only `M5`, a three-second dwell,
and `G53 G0 X-280 Y-266`, the known-safe southwest corner of Q5's measured
scan rectangle. It prints start/completion markers and has no `$H`, probe,
Aux0, A-axis, or coordinate-registration operation.

## Verification

- Static inspection: P107 contains a single G53 X/Y move and no `$H`.
- `python tools\\validate_homing_macro.py`: P100 remains valid.
- Installed execution: pending. Required sequence is Q2, then P107; do not
  repeat Q5 until the P107 result is known.

## Struggles and rejected approaches

The controller's rolling status console overwrites the beginning of a full Q5
raster. Capturing the old Q5 trace is therefore not a reliable feedback loop.
P107 narrows the physical test to the first load-bearing move.

## Risks and follow-up

P107 still commands one automatic XY rapid. Execute only after a fresh Q2 with
the X/Y travel path clear and stop immediately if it enters `Home` or heads
toward an X/Y switch.

## Files

- `firmware/grblhal/macros/P107.macro`: bounded preposition diagnostic.
- `firmware/grblhal/macros/README.md`: P107 operator contract.
- `docs/testing/TEST_PLAN.md`: prescribed diagnostic sequence.
- `docs/report/lab-notes/2026-09-11-p107-q5-preposition-diagnostic.md`:
  bench method and expected result.
