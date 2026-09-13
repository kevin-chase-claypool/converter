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
- Two 10 ms down pulses reached 22.8 g at `hx_delta=-337484`; one 10 ms lift
  pulse reduced that force to 11.3 g at `hx_delta=-51311`.
- A second 10 ms lift pulse released the scale to 0.0 g at `hx_delta=19079`.
- A fresh clear tare followed by one 10 ms down pulse produced
  `hx_delta=-325671` while the scale remained 0.0 g. This fails the required
  force-signal correlation; force mapping is paused pending mechanical/HX711
  isolation.
- Repeat one-pulse 10 ms trials reached 53.4 g at `hx_delta=-95958` and
  31.1 g at `hx_delta=-364221`; one 10 ms lift then cleared the latter to
  0.0 g at `hx_delta=-18012`. This confirms variable down-force response.
- After the reported screw/spring resolution, paired 10 ms cycles still reached
  11.8 g and 27.8 g respectively; each one-pulse lift returned to 0.0 g.
  Down-force varies while release is repeatable. This is expected in an
open-loop gearbox/friction system and must be handled by settled force
feedback rather than treated as a fixed grams-per-pulse calibration.
- At a 31.5 g stationary point, three HX711 deltas over about six seconds
  spanned 2384 counts (`-186392` to `-184008`), supporting settled-feedback
  evaluation despite variable open-loop pulse displacement.
- After release to a physical 0.0 g, the HX711 held a +164k to +168k count
  offset for 16 seconds without motion. This fails the absolute zero-reference
  requirement and pauses closed-loop force work pending load-cell force-path
  isolation.

## Struggles and rejected approaches

Keeping a 100 ms minimum was rejected because the measured correction is nearly
the entire low-force operating range. Removing the 1000 ms cap was also
rejected because LIFT_HOME remains telemetry-only in E07B.

## Risks and follow-up

The fine pulse range is a diagnostic tool, not an approved force-control
profile. The earlier no-contact result still requires attention, but variable
open-loop pulse force alone is expected with gearbox friction. Establish a
settled load-cell/scale transfer, bounded pulse limits, deadband, and dwell
before selecting a target or enabling automatic approach.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: fine/coarse duration selection.
- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`: records the measurement that motivated the revision.
