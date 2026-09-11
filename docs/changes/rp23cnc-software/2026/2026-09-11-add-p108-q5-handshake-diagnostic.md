---
id: RPSW-20260911-008
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/grblhal/macros/P108.macro
tags:
  - P100
  - P108
  - Q5
  - handshake
  - diagnostic
  - safety
related:
  - RPSW-20260911-007
---

# Add P108 Q5 Handshake Diagnostic

## Summary

Added a no-axis-motion diagnostic for Q5's readiness handshake.

## Reason

P107 passed its one preposition move without entering `Home`, while the
operator had observed three X/Y limit approaches before Q5 began its raster.
The next remaining Q5 stage is its Aux0/probe readiness handshake.

## Implementation

P108 duplicates the Q5 `M64 -> M65 -> M64 -> M65 -> M64` protocol, including
the READY_ACK and release checks, but has no `$H`, G0/G1/G38, A-axis, or G54
write. It emits short messages that survive the controller's rolling console
buffer.

## Verification

- Static inspection: P108 contains no axis-motion G-code or `$H`.
- `python tools\\validate_homing_macro.py`: P100 remains valid.
- Installed execution passed. P108 remained `Idle` throughout, asserted and
  released `P` as expected, printed its completion message, and made no axis
  motion or `Home` transition.

## Struggles and rejected approaches

The full Q5 trace was not retained by the controller's approximately
250-line rolling console. P107 first eliminated the preposition move. P108
now avoids raster status traffic entirely.

## Risks and follow-up

P108 should never move an axis. Its passed result rules out the standalone
Aux0 readiness handshake as the source of the reported limit approaches. The
combined preposition-plus-handshake sequence remains to be checked before any
further Q5 raster.

## Files

- `firmware/grblhal/macros/P108.macro`: handshake-only diagnostic.
- `firmware/grblhal/macros/README.md`: P108 operator contract.
- `docs/testing/TEST_PLAN.md`: staged diagnostic sequence.
- `docs/report/lab-notes/2026-09-11-p108-q5-handshake-diagnostic.md`:
  bench method and stop condition.
