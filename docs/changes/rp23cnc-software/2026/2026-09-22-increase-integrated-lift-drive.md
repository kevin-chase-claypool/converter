---
id: RPSW-20260922-016
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
tags:
  - motor-drive
  - gp2
  - supervised-bench
related:
  - RPSW-20260922-015
  - E-09E
---

# Match integrated lift drive to validated bench pulses

## Summary

Raised the integrated controller's lift PWM from 70/255 to full drive after a
correctly polarized boot still failed to reach GP2.

## Reason

The E-09E installed-pen test uses full phase drive for its validated 5–100 ms
UP pulses. The integrated build timed out at GP2 with no DRV8833 fault while
using the lower duty cycle.

## Implementation

`PWM_LIFT` is now `255`. The bounded 700 ms timeout and GP2 maximum-UP guard
remain unchanged; the down/preload and moving-average correction values are
not changed by this adjustment.

## Verification

The integrated sketch compiled successfully for
`rp2040:rp2040:sparkfun_promicrorp2350`. A powered retry is pending.

## Struggles and rejected approaches

Increasing the timeout was rejected as the first response because the motor
had not yet been shown to move under the integrated duty cycle.

## Risks and follow-up

Use the physical cutoff during the next boot. If full drive still does not
reach GP2, stop and run the standalone E-09E direction test rather than making
the timeout longer.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: full
  lift-drive setting.
