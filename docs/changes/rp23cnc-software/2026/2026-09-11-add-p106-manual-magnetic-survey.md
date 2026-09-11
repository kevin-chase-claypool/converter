---
id: RPSW-20260911-005
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P106.macro
tags:
  - P100
  - Q3
  - P106
  - magnetic-survey
  - safety
related:
  - RPSW-20260911-004
---

# Add P106 Manual Magnetic Survey

## Summary

Added a three-minute, no-motion diagnostic that enters the same magnetic scan
state P100 Q3 will use, allowing the operator to manually jog across the
candidate rectangle and observe P blank/red transitions.

## Reason

The Q3 candidate rectangle, pitch, feed, and pen offset are recorded, but Q3
must first prove that its corners are clear and the center magnet produces the
expected detected/clear transitions. Existing P105 holds only READY_ACK, which
is deliberately red and cannot distinguish magnetic detection.

## Implementation

P106 releases for a five-second baseline, performs `M65 -> M64 -> M65` within
the toolhead's re-arm window, waits 0.1 s for scan activation, holds for 180 s,
and releases Aux0 automatically. It sends no axis move, spindle command, or
probe move. Its explicit status message defines P blank as clear and P red as
detected.

## Verification

- Source inspection: P106 has only Aux0 commands, dwells, messages, and a
  macro return; no `G0`, `G1`, `G38`, `M3`, or `M5` command.
- Controller filesystem execution: pending.

## Struggles and rejected approaches

P105 was rejected for this purpose because its single arm remains in
READY_ACK, where P red is the acknowledgement rather than a magnetic result.

## Risks and follow-up

The first operator must begin P106 at a magnetically clear point so the
baseline can be reacquired. P106 does not authorize Q3 or automatic motion.

## Files

- `firmware/grblhal/macros/P106.macro`: timed scan-state survey.
- `firmware/grblhal/macros/README.md`: operator contract.
- `docs/testing/TEST_PLAN.md`: Q3 prerequisite.
