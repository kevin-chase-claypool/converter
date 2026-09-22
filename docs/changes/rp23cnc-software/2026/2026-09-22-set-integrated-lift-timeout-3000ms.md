---
id: RPSW-20260922-017
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: verified
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - integrated boot/fault recovery LIFTING state
tags:
  - gp2
  - lift-home
  - timeout
related:
  - RPSW-20260922-016
  - T-01G
---

# Set integrated lift timeout to 3000 ms

## Summary

Changed the supervised build's boot/fault-recovery UP timeout from 700 ms to
3000 ms.

## Reason

The user wants the mechanism to continue retracting until GP2 reports the full
retract limit. The prior 700 ms bound expired while `lift_home=0`.

## Implementation

The `LIFTING` state already stops the motor immediately when GP2 reports
`lift_home=1`. `BOOT_LIFT_TIME_MS` is the independent maximum continuous-UP
duration if the switch never activates; it is now 3000 ms. Normal M5 retains
its separate 100 ms air-gap move.

## Verification

The integrated sketch compiled for
`rp2040:rp2040:sparkfun_promicrorp2350`; documentation-index checks passed.
The subsequent supervised boot trace reached `pressure=LIFTED`,
`lift_home=1`, `fault=none` after first reporting `LIFTING`, `lift_home=0`.

## Struggles and rejected approaches

The 700 ms bound was too short for the observed travel. Removing the timeout
was not selected because it would permit indefinite UP drive if the switch or
wiring fails.

## Risks and follow-up

Full-drive UP can run for up to 3000 ms if GP2 does not activate. Keep the
physical cutoff reachable during supervised boot. The successful trace shows
GP2 activated before the timeout on this run; repeatability and mechanical
backstop margin remain to be characterized separately.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: timeout
  value and behavior comment.
- `firmware/pen_pressure/README.md`: current supervised boot behavior.
- `docs/changes/rp23cnc-software/2026/2026-09-22-increase-integrated-lift-drive.md`:
  follow-up to the full-drive lift update.
- `docs/report/lab-notes/2026-09-22-integrated-gp2-boot-retract-pass.md`:
  observed post-flash pass.
- `docs/project/ENGINEERING_LOG.md`: reason, safety bound, and next bench step.
