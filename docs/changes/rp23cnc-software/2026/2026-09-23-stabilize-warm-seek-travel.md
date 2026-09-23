---
id: RPSW-20260923-013
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
  - sensor-health
  - learning
related:
  - RPSW-20260923-009
  - RPSW-20260923-007
  - RPSW-20260923-011
  - RPSW-20260923-012
---

# Stabilize warm-seek travel and stop motor-driven sensor-noise faults

## Summary

The warm-seek coarse budget no longer oscillates between zero and one pulse,
and a `CS1238 reading implausible` fault is no longer raised from conversions
taken while the motor is PWM-driving the CS1238 interface. Telemetry now
carries a `t_ms` timestamp and the last dropped raw value so pen-up-to-band
latency and the dropped samples are visible in the log.

## Reason

The 2026-09-23 split-settle bench log showed the warm seek alternating between
17 pulses (fine-only) and 5 pulses (one coarse pulse), with `warm_ema` pinned
around 12-13 instead of converging. The same run then faulted with
`CS1238 reading implausible` after only three rejected conversions, even
though the last valid reading was clean.

Two causes were identified. First, the coarse budget truncated
`(warm_ema - reserve) / ratio` to an integer, so the EMA flipped across a
single-pulse cliff: a zero-budget pass re-measured the full fine-only distance
and pushed the EMA up, a one-budget pass measured a short coarse-assisted
travel and pushed it back down. The ratio of 5 also under-credited each coarse
pulse: the same ~1 mm clearance took 17 fine-only pulses but only 1 coarse +
3-4 fine pulses, so one coarse pulse actually covers ~13-14 fine pulses, not 5.

Second, `serviceCs1238()` samples the bit-banged GP0/GP1 interface even while
the DRV8833 is PWM-driving, and motor PWM is a known source of transient CS1238
glitches. Three consecutive motor-driven glitches during the first seek pulse
tripped the three-in-a-row sensor-health fault and stopped the machine.

## Implementation

- `toolhead_config.h`: `SEEK_WARM_COARSE_RATIO` 5 -> 13 and
  `SEEK_WARM_FINE_RESERVE` 8 -> 4, with a note that the ratio is
  stiction-dominated and must be re-measured after the linear-rail carriage /
  bearing swap.
- `pressure_controller.cpp`: the coarse budget now rounds to the nearest pulse
  instead of truncating, removing the 0/1 cliff.
- `pressure_controller.h` / `pressure_controller.cpp`: added a `motor_driving_`
  flag set by `motorDrive()` and cleared by `motorStop()` /
  `setDriverEnabled(false)`, and `cs1238_last_rejected_raw_`. The implausible
  streak is reset while the motor is driving, so motor-PWM glitches are dropped
  without counting toward the fault; a genuinely dead sensor still faults via
  the read-timeout/online path.
- `pro_micro_rp2350_toolhead.ino`: `SNAPSHOT`/`FAULT_EVENT`/`LIVE` records add
  `t_ms` and `cs1238_last_reject`; `STATE_EVENT` records add `t_ms`.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 81960 bytes program storage and 16220 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench verification is required. Expected: after the first fine-only warm
  pass, `warm_ema` stabilizes near the measured fine-pulse travel and warm M3s
  settle at one coarse pulse plus a few fine pulses (no 5/17 alternation);
  normal seeks no longer raise `CS1238 reading implausible` from motor noise.

## Struggles and rejected approaches

A pure hysteresis threshold without correcting the ratio was rejected: the
under-credited coarse travel would still decay the EMA, so the oscillation
would only slow down rather than stop. Hard-coding the ratio to an "ideal" 5
was also rejected because the measured coarse-to-fine distance is
stiction-dominated; 13 reflects the current mechanism and is documented for
re-measurement after the carriage swap.

## Risks and follow-up

`SEEK_WARM_COARSE_RATIO = 13` is valid for the current stiction-limited
mechanism. Once the carriage/bearing is replaced and stiction drops, the ratio
is expected to fall toward ~5 and the reserve/rounding should be re-tuned from
a fresh bench log. Suppressing the implausible streak during motor drive means
a sensor fault that only manifests under drive is caught by the read-timeout
path rather than the three-sample streak; the hard-force guard remains
independent and active. Confirm on the bench that the fault no longer fires
during ordinary seek before drawing.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: coarse ratio and reserve.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`: `motor_driving_` and last-reject state.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: rounded budget and gated implausible streak.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: `t_ms` and `cs1238_last_reject` telemetry.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`: document the corrected learning and sensor-noise handling.
