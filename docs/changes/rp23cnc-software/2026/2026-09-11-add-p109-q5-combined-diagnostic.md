---
id: RPSW-20260911-009
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/grblhal/macros/P109.macro
tags:
  - P100
  - P109
  - Q5
  - diagnostic
  - handshake
  - raster
  - safety
related:
  - RPSW-20260911-007
  - RPSW-20260911-008
---

# Add P109 Q5 Combined Diagnostic

## Summary

Added a Q5-order preposition-plus-handshake diagnostic that stops before the
first G38 raster command.

## Reason

P107 proved Q5's preposition independently and P108 proved its handshake
independently. The observed extra X/Y limit approaches must now be tested
against their exact combined order before blaming the raster.

## Implementation

P109 copies Q5's released baseline, G53 southwest-corner preposition, and
Aux0/PRB handshake. It deliberately omits all G38, centroid, G54, and A
operations and emits stage messages that survive the controller's rolling
console buffer.

## Verification

- Static inspection: P109 has one G53 X/Y move; no `$H`, G38, G54 write, or A
  command.
- `python tools\\validate_homing_macro.py`: P100 remains valid.
- Installed execution passed after fresh Q2. P109 moved continuously from
  `MPos:-10.000,-436.000` to `MPos:-280.000,-266.000`, completed its P
  readiness/release transition, stayed out of `Home`, and printed completion.

## Risks and follow-up

P109 commands one known-safe automatic XY move. Its passed result proves the
complete Q5 sequence before its first G38 command does not cause the observed
limit approaches. The next diagnostic must isolate the first G38 probe row
rather than repeat the full Q5 raster.

## Files

- `firmware/grblhal/macros/P109.macro`: combined Q5-stage diagnostic.
- `firmware/grblhal/macros/README.md`: P109 operator contract.
- `docs/testing/TEST_PLAN.md`: staged diagnostic sequence.
- `docs/report/lab-notes/2026-09-11-p109-q5-combined-diagnostic.md`: bench
  procedure and stop condition.
