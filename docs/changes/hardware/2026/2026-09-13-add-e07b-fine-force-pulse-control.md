---
id: HW-20260913-011
date: 2026-09-13
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/e07b_hx711_actuator_steps
tags:
  - n20
  - force-control
  - pulse-duration
  - e-07b
related:
  - HW-20260913-010
---

# Add E07B fine force-pulse control

## Summary

E07B now starts at 20 ms and adjusts in 10 ms increments below 100 ms, while
retaining 100 ms increments above that threshold through the existing `[` and
`]` commands.

## Reason

With the repaired DRV8833 and installed 1000 RPM N20, one 100 ms lift pulse
reduced measured blunt-tool force from 43.4 g to 0.5 g. A 100 ms minimum is
therefore too coarse to characterize or control writing force.

## Implementation

`[` and `]` use 10 ms steps while the selected duration is below 100 ms; at
100 ms and above they use 100 ms steps. The protected range is 10--1000 ms
and the post-flash default is 20 ms. The commands retain their existing
direction, sleep-after-pulse, and fault behavior.

## Verification

- SparkFun Pro Micro RP2350 compile passed.
- The physical force evidence motivating the change was 43.4 g at
  `hx_delta=-503592`, followed by 0.5 g at `hx_delta=-5984` after one 100 ms
  lift pulse.
- A controlled 20 ms down pulse reached 19.6 g at `hx_delta=-349534`; one
  20 ms lift pulse released to 0.0 g at `hx_delta=-8217`.
- Two 10 ms down pulses reached 22.8 g at `hx_delta=-337484`; the 10 ms
  release measurement remains pending.

## Struggles and rejected approaches

Keeping a 100 ms minimum was rejected because the measured correction is nearly
the entire low-force operating range. Removing the 1000 ms cap was also
rejected because LIFT_HOME remains telemetry-only in E07B.

## Risks and follow-up

The fine pulse range is a diagnostic tool, not an approved force-control
profile. Establish repeatable force response, travel bounds, and release
hysteresis with the scale before selecting a target or enabling automatic
approach.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: fine/coarse duration selection.
- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`: records the measurement that motivated the revision.
