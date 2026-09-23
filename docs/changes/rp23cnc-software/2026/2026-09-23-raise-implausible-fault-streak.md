---
id: RPSW-20260923-014
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
  - sensor-health
  - reliability
related:
  - RPSW-20260923-013
  - RPSW-20260923-007
---

# Require a full filter window of implausible samples before faulting

## Summary

The `CS1238 reading implausible` fault now requires 16 consecutive implausible
conversions (one full 16-sample filter window, about 25 ms at 640 SPS) instead
of three. Momentary bit-bang glitch bursts no longer stop the machine.

## Reason

The first stabilization build still faulted after 11 successful holds. The
telemetry showed `cs1238_last_reject` values of 2,920,287 and 4,218,117 raw —
the same large intermittent garbage signature as the earlier header incident —
arriving while the toolhead held cleanly in band. Three consecutive rejects is
only about 4.7 ms at 640 SPS, so a short burst of corrupted reads was enough to
raise the fault. The isolated glitches were already dropped before reaching the
force filter, so the fault added no safety and only interrupted an otherwise
working hold.

## Implementation

- `toolhead_config.h`: `CS1238_IMPLAUSIBLE_FAULT_STREAK` 3 -> 16, with a note
  that a dead or disconnected sensor faults through the read-timeout/online
  path instead.
- `pressure_controller.cpp`: updated the motor-drive gating comment so it no
  longer claims motor PWM was the only glitch source.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`:
  document the threshold and the header/connection follow-up.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 81960 bytes program storage and 16220 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench verification is required. Expected: isolated reject bursts no longer
  raise a fault; a persistent run of garbage still faults within one window.

## Struggles and rejected approaches

Keeping the 3-sample threshold and only widening the plausibility band was
rejected: the glitch magnitudes (2.9e6 / 4.2e6) are unambiguously outside any
reasonable force range and must remain dropped from the filter. The streak is a
secondary sensor-health net; the read-timeout path already catches a genuinely
dead sensor.

## Risks and follow-up

The intermittent garbage points to the CS1238 header/connection rather than
motor noise. Re-seat the header if `cs1238_rejects` climbs again; a persistent
failure still faults once it produces a full window of continuous garbage.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: raised streak.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: comment correction.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`: document the threshold.
