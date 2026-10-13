---
id: RPSW-20261013-001
date: 2026-10-13
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
tags:
  - toolhead
  - pen-clear
  - m5
  - clearance
related:
  - ADR-004
  - RPSW-20261011-001
---

# Raise the M5 pen-clearance pulse to 90 ms

## Summary

`PEN_CLEAR_EXTRA_LIFT_MS` is raised from 70 ms to **90 ms** of full-drive UP
after the M5 force-release point. At the measured drive rate (1.75 mm per
100 ms), that moves the M5 clearance from about 1.2 mm to about **1.55 mm**
above the release point, per the operator's request for the pen to lift
slightly higher.

## Reason

Operator request (2026-10-13): the M5 clearance needs a little more margin.
History: the T-01H-accepted value was 57 ms; it was raised to 70 ms on
2026-10-02 when drag marks appeared during pen-up travel on production prints.
This is the next step on the same lever.

## Implementation

One constant in `toolhead_config.h`, with dated comments. Every affected
behaviour is already relative to it: M5 adds the pulse after proving release,
M3 warm-seek travel learning absorbs the larger gap on its first touch, and the
contact-seek budget (100 pulses, ~8.75 mm) covers the extra ~0.35 mm with wide
margin. No host-side or converter change is required.

## Verification

- Source inspection only in this session: constant 70 -> 90, comments updated.
- Pending bench validation per ADR-004: confirm release still verifies, M3
  contact acquisition still completes on the first try, and pen-up travel
  produces no drag marks at the new clearance.

## Struggles and rejected approaches

None; single-constant change on the operator's explicit request.

## Risks and follow-up

- A larger clearance lengthens every M3 approach slightly (about +20 ms of
  drive plus settle behaviour) - negligible at plot scale.
- If drag marks persist at 90 ms, the next step is 100-110 ms; if the force
  release itself becomes marginal, revisit the release window rather than
  pushing the pulse further.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: the
  constant and its dated history comments.
- `docs/project/ENGINEERING_LOG.md`: session entry.
