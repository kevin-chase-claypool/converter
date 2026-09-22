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

`PWM_LIFT` is now `255`. The bounded timeout and GP2 maximum-UP guard remain;
the timeout was subsequently extended to 3000 ms in response to observed
travel taking longer than 700 ms. The down/preload and moving-average
correction values are not changed by that timeout adjustment.

## Verification

The integrated sketch compiled successfully for
`rp2040:rp2040:sparkfun_promicrorp2350`. The powered retry with full lift drive
and the revised timeout is pending.

## Struggles and rejected approaches

The first response raised lift drive to the already validated full phase level;
the timeout was extended separately after another trace still ended before
GP2 asserted.

## Risks and follow-up

Use the physical cutoff during the next boot. If full drive still does not
reach GP2, stop and run the standalone E-09E direction test rather than making
the timeout longer.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: full
  lift-drive setting.
