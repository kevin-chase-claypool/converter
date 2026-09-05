---
id: WSW-20260905-002
date: 2026-09-05
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: planned
components:
  - software/converter_core/kinematics.py
  - software/converter_core/gcode.py
  - software/README.md
  - docs/integration/INTERFACES.md
tags:
  - theta
  - a-axis
  - tangential-speed
  - radius
  - feed-planning
related:
  - M-03
  - M-06
  - HW-20260905-004
---

# Plan radius-aware A-axis feed for drawing

## Summary

The converter must make A-axis feed radius-aware. A is emitted in motor-shaft
degrees, while the desired writing speed is tangential bed speed; therefore the
required angular rate changes inversely with the pen's radius from the bed
center.

## Reason

The A-axis bed-ratio check validated 4,320 motor degrees per bed revolution.
Using one fixed A interpretation of the modal `F` would make the pen surface
speed vary as the radius changes. The effect is largest near the center, where
the same angular rate produces very little tangential travel.

## Implementation

For radius `r` in millimeters and target tangential speed `v` in mm/min, the
motor-degree rate is:

```text
A_feed_motor_deg/min = (4320 × v) / (2π × r)
```

The future planner change must calculate this per segment, combine the A
contribution with XY motion for coordinated feed, cap the result at the
controller's A rate/acceleration limits, and define a safe zero/near-zero
radius policy. Preview timing must use the same result as emitted G-code.

## Verification

- The formula is consistent with the validated 12:1 ratio and A motor-degree
  contract documented in `docs/integration/INTERFACES.md`.
- A hardware-coordinated-motion test (M-06) remains required to verify how
  grblHAL applies the combined `F` and axis limits.
- Software implementation and generated-G-code tests are not complete yet.

## Struggles and rejected approaches

Treating the modal `F` as a fixed bed-surface speed was rejected because the
same angular rate produces different tangential speeds at different radii.
Applying the 12:1 ratio a second time in firmware is also rejected; the
converter's established A unit is motor-shaft degrees.

## Risks and follow-up

Near the center, the rate required for a chosen tangential speed can exceed
`$113`; the converter must lower achievable surface speed rather than emit an
unbounded request. Combined XY/A feed metric behavior must be measured on the
installed grblHAL build. Add unit, G-code, preview, and hardware acceptance
tests before treating the feature as implemented.

## Files

- `software/README.md`: records the user-facing requirement and formula.
- `docs/HANDOFF.md`: records the G-code caveat and hardware verification need.
- `docs/integration/INTERFACES.md`: records the cross-subsystem feed contract.
- `docs/project/ROADMAP.md`: adds the Phase 4 implementation task.
