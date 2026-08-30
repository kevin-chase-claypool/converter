---
id: HW-20260830-005
date: 2026-08-30
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - toolhead-lift-home-switch
  - docs/hardware/WIRING_TABLE.md
  - firmware/pen_pressure
tags:
  - toolhead
  - lift-home
  - microswitch
  - gp2
related:
  - HW-20260830-004
---

# Plan Toolhead LIFT-Home Switch

## Summary

Recorded a planned normally-open LIFT-home microswitch input between Pro Micro
RP2350 `GP2` and `TOOL_GND`. The owner identified microswitch terminals `1`
and `3` as the intended dry-contact pair.

## Reason

The pen carriage floats on its linear rail relative to the load-cell force
path, so the load cell cannot establish retracted height. A local position
reference is needed to repeat the selected LIFT clearance before plotting.

## Implementation

The planned firmware uses `GP2` with `INPUT_PULLUP`; the normally-open contact
pulls the input LOW when the moving carriage flag presses a fixed switch. The
contact has no electrical polarity. The switch is a reference sensor, not a
mechanical stop: a separate backstop and spring solid-height margin remain
required.

## Verification

- Owner identified terminals `1` and `3` for the intended COM/NO pair.
- No wire has been installed and no powered GPIO test is claimed.
- T-01G defines the required continuity, GPIO, ten-cycle repeatability, and
  timeout checks.

## Struggles and rejected approaches

Using the floating load-cell reading as a LIFT reference was rejected because
spring compression does not load that sensor in this carriage arrangement.

## Risks and follow-up

Confirm continuity behavior before wiring. Install the switch/flag and verify
T-01G before enabling firmware use. Verify the backstop and solid-height margin
separately in T-01A; neither is established by switch actuation.

## Files

- `docs/hardware/WIRING_TABLE.md`: planned `GP2` LIFT-home input.
- `docs/testing/TEST_PLAN.md`: T-01G acceptance test.
- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: inserts T-01G before powered
  direction testing.
- `docs/report/lab-notes/2026-08-30-t-01g-lift-home-switch-terminal-identification.md`:
  current observation and outstanding evidence.
