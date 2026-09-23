---
id: RPSW-20260922-033
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e07b_hx711_actuator_steps
tags:
  - hx711
  - e07b
  - bench-diagnostic
  - historical-evidence
related:
  - RPSW-20260922-032
---

# Record E-07B trace-settle tuning

## Summary

The historical E-07B HX711 fast-trace sketch now carries the `TRACE_SETTLE_MS`
value that was actually used on the bench, together with the tuning record
that explains how it got there.

## Reason

The sketch source had drifted from the bench. It still declared the original
500 ms while the flashed board had been hand-edited up to 4000 ms, and its
in-code comment still justified the superseded 1200 ms choice. At the shorter
dwells the external scale's own settle behaviour and the mechanism's
backlash/creep were unresolved, so per-pulse video readings could not be
reconciled with the serial log.

## Implementation

`firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`
now sets `TRACE_SETTLE_MS = 4000` with a comment recording the 500 -> ~1200 ->
~1690 -> ~2620 -> 4000 ms ladder and its evidence. The new adjacent record
`2026-09-13-trace-settle-ms-tuning.md` keeps the full bench history, the
unreliable readings, and the open questions; the sketch comment points at it.

`TRACE_SETTLE_MS` affects only the `r` fast-trace command's 12-down/12-up
sequence. Manual `d`/`u` steps, `a` auto-approach, and both meter modes are
unchanged.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 65400 bytes program storage and 11136 bytes dynamic memory.
- At 4000 ms the pulses finally appeared on video as discrete steps with a
  flat hold between them (40.4 g holds -> 29.6 g -> 0.7 g). One UP-phase step
  pair matched the corresponding serial `t_ms` deltas at roughly 4138 ms
  spacing, which is 4000 ms plus firmware overhead.
- `python tools\docs_index.py --write` and `python tools\docs_index.py --check`
  pass.

## Struggles and rejected approaches

Two trace attempts were abandoned partway (5 of 12 DOWN steps) because the pen
was not clear of the scale before `r` was issued; those were operator
restarts, not faults or hangs. Video with a one-second-resolution timestamp
overlay and a steep foreshortened camera angle was rejected as unusable for
pulse-level alignment.

## Risks and follow-up

This is a bench-diagnostic dwell on the retired HX711 force path. It is not a
production hold time and must not be reused as one. Counts-to-grams remained
unstable run to run, so no single trace is calibrated grams, and the
post-release residual still has two unreconciled behaviours.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: sync `TRACE_SETTLE_MS` to the flashed 4000 ms and replace the stale 1200 ms comment.
- `firmware/pen_pressure/e07b_hx711_actuator_steps/2026-09-13-trace-settle-ms-tuning.md`: add the bench tuning record the sketch comment references.
