---
id: RPSW-20260925-002
date: 2026-09-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - toolhead
  - cs1238
  - recovery
  - fault
---

# Recover from CS1238 implausible-reading bursts

## Summary

Extended the bounded auto-recovery so a `CS1238 reading implausible` burst also
lifts through the normal M5 clearance and re-seeks, instead of latching `FAULT`
and leaving the pen down while the gantry keeps moving.

## Reason

Previously only `hard force limit exceeded` auto-recovered; the implausible
burst still latched, which is exactly the drag-while-stopped failure the
operator wanted removed. A 16-consecutive-sample glitch burst is usually a
transient bit-bang artifact, not a dead sensor, so retrying is appropriate;
the read-timeout/online path still latches the genuine disconnect case.

## Implementation

- `pressure_controller.cpp`: in `serviceCs1238`, when the implausible streak
  reaches `CS1238_IMPLAUSIBLE_FAULT_STREAK`, reset the streak and, while under
  `HARD_LIMIT_RECOVERY_MAX`, increment `implausible_recoveries_` and transition
  to `CLEARANCE_LIFT`; otherwise latch the fault.
- `pressure_controller.h`: added the `implausible_recoveries_` counter and
  getter.
- `pro_micro_rp2350_toolhead.ino`: `recoveries=` now reports the hard-limit and
  implausible recoveries combined.
- `toolhead_config.h`: updated the recovery-max comment to describe both paths.

Both recovery counters reset on any successful contact.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- Behavioral confirmation is outstanding: induce a glitch burst and confirm the
  pen lifts and re-seeks instead of latching, and that a persistent burst still
  latches after the retry cap.

## Struggles and rejected approaches

Reusing `RELEASE_TO_CLEAR` (the force-verified release) was rejected for this
path: a glitching sensor makes force-based release detection unreliable, so the
timed `CLEARANCE_LIFT` is the correct recovery target.

## Risks and follow-up

- A genuinely intermittent-but-persistent sensor will now cycle lift/re-seek up
  to the retry cap before latching, which is the intended bound. The dead-sensor
  path still latches immediately via the read-timeout/online branch.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
