---
id: RPSW-20260924-003
date: 2026-09-24
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - toolhead
  - force-control
  - hard-limit
  - recovery
  - seek
---

# Bound the coarse seek step and auto-recover from hard-limit overshoot

## Summary

Shortened the warm/cold seek's coarse pulse from 25 ms to 10 ms, corrected the
warm travel ratio to match, and made a hard-force-limit overshoot recover
through the normal M5 clearance with a bounded re-seek instead of latching
`FAULT`.

## Reason

On 2026-09-24 the installed carriage (post linear-rail swap) tripped
`hard force limit exceeded` at `force_norm_raw=303061` against a
`hard_limit_raw=302326` (60.1 g vs 60.0 g) two pulses into a warm seek, with
`warm_ema=33`. The warm seek sized a 2-pulse coarse budget, and a single 25 ms
full-drive pulse near contact was worth more than the entire 60 g envelope, so
the 3 g coarse gate (sampled after the prior settle) could not catch it. The
config comment for `SEEK_WARM_COARSE_RATIO` already required re-measuring that
constant after the carriage swap.

Separately, a latched `FAULT` was the wrong outcome for an over-force: it stops
and de-energizes the pen motor, leaving the pen down while grblHAL keeps moving
X/Y/A, so the pen dragged. Recovery required a manual `c`, which retracts all
the way to GP2 and then needs `a`, by which time the gantry had moved on.

## Implementation

- `toolhead_config.h`: `HOME_SEEK_COARSE_PULSE_MS` 25 -> 10, so one coarse step
  moves about 0.18 mm and lands near the 35 g target rather than through the
  60 g limit. `SEEK_WARM_COARSE_RATIO` 13 -> 2, matching the 10 ms / 5 ms pulse
  time ratio. Added `HARD_LIMIT_RECOVERY_MAX = 3`.
- `pressure_controller.cpp`: the hard-limit guard now, while under the retry
  budget, increments `hard_limit_recoveries_` and transitions to
  `RELEASE_TO_CLEAR` (the normal force-verified M5 clearance path) instead of
  `enterFault`. The still-asserted M3 then re-seeks from `LIFTED`. The counter
  resets to zero on every successful contact, and the fault is only latched
  when the budget is exhausted or for a non-force fault.
- `pressure_controller.h` / `.ino`: expose `hardLimitRecoveries()` and report
  it as `recoveries=` in telemetry.

The recovery keeps the coarse/fine bookkeeping consistent by clearing the seek
pulse counters on entry; the warm-seek learned travel is otherwise untouched so
it keeps tracking clearance drift.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly (82128 bytes program / 16228 bytes RAM).
- Static reasoning: a 10 ms pulse moves ~0.18 mm versus ~0.44 mm for 25 ms, so
  a worst-case coarse step near contact is ~half the hard limit, and the
  coarse phase stops at least `SEEK_WARM_FINE_RESERVE` fine pulses before the
  learned contact point.
- Bench confirmation is outstanding: the toolhead must be re-flashed and a
  print run must show no `hard force limit exceeded` faults, warm M3 times
  still inside the converter dwell, and `recoveries=` only rising on genuine
  over-force with the pen re-seeking rather than latching.

## Struggles and rejected approaches

Removing the coarse pulses entirely (fine-only warm seek) was rejected by the
operator because it slows every M3. A force-gate-only change was rejected
because one coarse pulse can jump from below the gate to above the hard limit,
so no gate can catch it. The chosen pulse-width reduction keeps the coarse
phase as a faster-than-fine step while making a single step safe regardless of
the learned ratio.

## Risks and follow-up

- The 10 ms pulse and 2:1 ratio are bench candidates. Re-measure the coarse
  travel and warm-seek pulse count on the installed carriage and update them
  with dated evidence before relying on unattended plotting.
- Auto-recovery still cannot stop the gantry: the pen lifts through the normal
  M5 clearance while grblHAL keeps moving, so a brief drag remains. The durable
  fix is the GP27/`P115` loop so the controller pauses motion on fault; that
  remains commissioning-gated (`GP27_NORMAL_STATUS_ENABLED = false`).
- `cs1238_rejects=4860` was observed in the triggering run; the CS1238 header
  needs re-seating and is tracked separately.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`
- `firmware/pen_pressure/CONTROL_STRATEGY.md`
