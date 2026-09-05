---
id: WSW-20260905-002
date: 2026-09-05
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/kinematics.py
  - software/converter_core/gcode.py
  - software/tests/test_theta_feed.py
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

# Implement radius-aware A-axis feed for drawing

## Summary

The converter now makes drawing A-axis feed radius-aware. A is emitted in
motor-shaft degrees, while the desired writing speed is tangential bed speed;
therefore the required angular rate changes inversely with the pen's radius
from the bed center.

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

The planner calculates this per segment from the average endpoint radius. It
uses the new `Theta tangential speed mm/min` field for the bed-surface request,
retains `Feed rate` as the maximum X/Y component speed, and derives one
coordinated `F` from the longer component duration. The installed A profile
(`$113 = 80000` motor-deg/min; `$123 = 6000` motor-deg/s²) caps the request.
At the exact center it uses capped angular motion without division by zero and
reports zero achieved tangential speed. Preview and emitted G-code call the
same feed-planning helper.

## Verification

- `python -m unittest discover -s software/tests -v` passed all 10 tests.
- Tests cover inverse-radius A rates, forward/reverse moves, rate and
  acceleration limits, center behavior, unchanged no-A output, and generated
  G-code/preview parity.
- The formula remains consistent with the validated 12:1 A motor-degree
  contract documented in `docs/integration/INTERFACES.md`.

## Struggles and rejected approaches

Treating the modal `F` as a fixed bed-surface speed was rejected because the
same angular rate produces different tangential speeds at different radii.
Redefining the existing `Feed rate` field was also rejected because it would
silently change X/Y-only output. Applying the 12:1 ratio a second time in
firmware remains rejected; the converter's established A unit is motor-shaft
degrees.

## Risks and follow-up

Near the center, the rate required for a chosen tangential speed can exceed
`$113`; the converter lowers achievable surface speed rather than emitting an
unbounded request. The acceleration cap is intentionally conservative because
it treats each segment as rest-to-rest. Combined XY/A feed metric and
look-ahead behavior must be measured on the installed grblHAL build in M-06
before relying on high-speed runtime estimates.

## Files

- `software/converter_core/settings.py`: adds the explicit tangential-speed
  setting and installed A limit profile.
- `software/converter_core/kinematics.py`: plans radius-aware segment feeds.
- `software/converter_core/gcode.py`: emits planned feeds and exposes the same
  values to preview moves.
- `software/tests/test_theta_feed.py`: covers planner and G-code/preview
  behavior.
- `software/README.md`, `docs/HANDOFF.md`, and
  `docs/integration/INTERFACES.md`: document current behavior and M-06 risk.
- `docs/project/ROADMAP.md`: records the completed software task.
