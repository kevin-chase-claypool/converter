# TRACE_SETTLE_MS tuning (E-07B fast trace)

Date: 2026-09-13
File: `e07b_hx711_actuator_steps.ino`

## What this is

`TRACE_SETTLE_MS` is the dwell the `r` (fast trace) command waits after each
10 ms actuator pulse, before sampling the HX711 and moving to the next pulse.
It only affects the `r` command's 12-down/12-up trace; it does not touch
manual `d`/`u` steps, `a` auto-approach, or either meter mode.

This is a bench diagnostic setting for characterizing the force sensor and
mechanism. It is not a production hold time and should not be reused as one
without separate justification.

## Why it changed

The original value (500 ms) was outrunning both the external digital scale's
own display/settle behavior and the mechanism's own backlash/creep. Readings
taken from phone video against the serial log at 500 ms could not be trusted
per-pulse: the scale was still moving when the next pulse fired.

## History this session

| Settle time | How it got there | Result |
|---|---|---|
| 500 ms (original) | — | Per-pulse video reads unreliable; scale not settled between pulses. |
| 1200 ms | Code edit (this file, by Claude) | Visibly better plateau stability, but video alignment still not achievable with confidence (timestamp overlay was only 1-second resolution). |
| ~1690 ms | Hand-edited on the bench | Same limitation; second-resolution timestamps still too coarse to align individual pulses. |
| ~2620 ms | Hand-edited on the bench | Clean plateaus visible on video; also surfaced a possible nonlinear/compressing HX711 response at higher loads (delta kept climbing while the scale reading had plateaued). Camera handheld and lost the release moment to blur. |
| 4000 ms | Hand-edited on the bench | First video with a millisecond-precision timestamp overlay and a good head-on camera angle. See "What we confirmed" below. |

The `.ino` file itself lagged behind the bench during this process: it was
last synced to 1200 ms, while the physical board had already moved on to
4000 ms through direct hand edits. This change brings the source back in
sync with what is actually flashed and in use, and rewrites the stale
in-code comment (which still referenced the 1200 ms reasoning) to match.

## What we confirmed at 4000 ms

Using a video with a millisecond-resolution wall-clock overlay and a
near-head-on camera angle (earlier videos were shot at a steep, foreshortened
angle that made the digits unreadable at fine time resolution), the release
portion of one trace was sampled at 0.5 s resolution and showed two sharp,
essentially-instantaneous drops in the displayed grams, separated by a flat
hold of about 3.5-4 seconds:

- 40.4 g holds, then drops to 29.6 g in well under 0.5 s
- 29.6 g holds for ~3.5 s, then drops to 0.7 g in well under 0.5 s
- 0.7 g holds flat for the remainder of the recording (22+ s, no further drift)

That ~4-second spacing matches `TRACE_SETTLE_MS` (4000 ms + firmware
overhead, ~4138 ms per the logged `t_ms` deltas). The same trace's serial log
shows two consecutive large drops in the same position in the UP sequence
(UP6 to UP7, then UP7 to UP8), each ~4.14 s apart in `t_ms`, with everything
before them relatively flat and everything after oscillating near zero. The
step count, position in the sequence, and timing all line up. This is the
first trace where a specific video moment and a specific log line could be
matched with real confidence, rather than by shape alone.

## Open items this does not resolve

- The counts-to-grams relationship is not stable run to run. Two traces with
  DOWN-phase peak deltas within 1% of each other (-545,600 and -542,719
  counts) read roughly 41 g and roughly 55-58 g respectively on the external
  scale. Do not treat any single trace's counts as calibrated grams.
- The post-release residual (near-zero but nonzero HX711 delta / scale
  reading after full retraction) is inconsistent in behavior across runs:
  sometimes it drifts for many seconds afterward, sometimes it settles to a
  small flat offset and holds. Both have been observed; neither has been
  reproduced enough times to call it characterized.
- Two trace attempts this session were aborted partway (5 of 12 DOWN steps)
  because the pen was not clear of the scale before `r` was issued. These
  were operator restarts, not faults or hangs, and needed no firmware
  change.

## Files touched

- `e07b_hx711_actuator_steps.ino`: `TRACE_SETTLE_MS` source now matches the
  flashed value (4000 ms); in-code comment rewritten to describe the actual
  tuning history and evidence instead of the stale 1200 ms rationale.
- This file: written alongside the source to record why and what changed.
