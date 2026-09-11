---
id: RPSW-20260911-010
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - firmware/grblhal/macros/P110.macro
tags:
  - P100
  - P110
  - Q5
  - G38
  - probe
  - diagnostic
  - safety
related:
  - RPSW-20260911-009
---

# Add P110 Q5 First G38 Row Diagnostic

## Summary

Added a single clear-row G38 diagnostic for the first remaining Q5 motion
family after pre-raster Q5 stages passed.

## Reason

P109 proved Q5's full preposition and handshake without a `Home` state. The
only untested Q5 operation before the reported unexpected behavior is its
G38-based raster.

## Implementation

P110 performs the established Q5 setup and readiness sequence, then executes
the first expected-clear G38.3 row, G53 X `-280..-180` at Y `-266`. It returns
to G90 and releases Aux0 before reporting its result. It has no G54, centroid,
or A command.

## Verification

- Static inspection: one 100 mm X-only G38.3, no `$H`, centroid, G54 write,
  or A command.
- `python tools\\validate_homing_macro.py`: P100 remains valid.
- Installed execution passed after fresh Q2. The row traveled east from the
  southwest corner at `MPos:-280.000,-266.000` to the southeast corner at
  `MPos:-180.000,-266.000`, returned clear `[PRB:-180.000,-266.000:0]`, and
  printed `P110 complete: clear first G38.3 row passed`. It did not enter
  `Home` or approach a limit switch.

## Risks and follow-up

P110 commands one bounded probe move through the verified scan rectangle.
Its passed result proves Q5's initial clear-row probe transition is not a
homing cycle. The remaining scope is the full raster loop, including rows that
encounter the center magnet.

## Files

- `firmware/grblhal/macros/P110.macro`: first-row G38 diagnostic.
- `firmware/grblhal/macros/README.md`: P110 operator contract.
- `docs/testing/TEST_PLAN.md`: staged diagnostic sequence.
- `docs/report/lab-notes/2026-09-11-p110-q5-first-g38-row-diagnostic.md`:
  bench procedure and stop condition.
