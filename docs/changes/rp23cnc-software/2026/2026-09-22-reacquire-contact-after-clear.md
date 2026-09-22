---
id: RPSW-20260922-029
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - cs1238
  - m3-m5
  - contact-detection
  - force-control
related:
  - RPSW-20260922-028
---

# Re-acquire Contact after M5 Clearance

## Summary

Every normal M3 now re-finds paper after M5 clearance before it tunes and holds
drawing force.

## Reason

The prior normal-M3 shortcut moved DOWN for a fixed 100 ms, retained the
preceding contact reference, and entered force hold. Bench evidence showed it
could be physically clear and enter `HOLD_FORCE` at only 5,235 raw, then fault
for not acquiring force.

## Implementation

On an M3 beginning with GP2 released, the controller clears the old touch
reference and reuses the stopped-pulse trend confirmation already used after a
home-origin seek. It uses only bounded 5 ms DOWN pulses because M5's 100 ms
clearance leaves a small gap. Acceptance still requires three 25 ms-separated
filtered windows of a persistent response, followed by the existing 10 ms
back-off and fine tuning.

## Verification

- Arduino CLI compile passed for the SparkFun Pro Micro RP2350 target.
- Repeated supervised M3/M5 hardware cycles remain required.

## Risks and follow-up

The normal re-contact pulse count and timing are unqualified candidates. Test
repeatable clear/re-contact cycles with the selected pen before connecting
M3/M5 to production G-code.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`
- `firmware/pen_pressure/CONTROL_STRATEGY.md`
