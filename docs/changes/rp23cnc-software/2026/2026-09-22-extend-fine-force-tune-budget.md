---
id: RPSW-20260922-027
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
  - n20
  - force-tune
  - safety
related:
  - RPSW-20260922-026
---

# Extend Fine Force-Tune Budget

## Summary

The released-state fine force-tune phase now permits up to 100 individual 5 ms
pulses in seven seconds and reports its count separately in snapshots.

## Reason

The first valid two-touch trace established the released tare and 5 g surface
touch, then safely exhausted the original 30-pulse force-tune budget at only
about 9.6 g. The post-touch back-off intentionally creates a real gap, so the
remaining issue is permitted fine travel rather than force direction or safety.

## Implementation

No single pulse, target force, or hard-force limit increased. The tune budget
is 100 x 5 ms pulses and seven seconds, which remains bounded. `p` snapshots
now distinguish total home-seek and fine-tune pulse counts.

## Verification

- The input trace showed released tare `117 raw`, first-touch `25,589 raw`,
  and tune-budget fault at `48,185 raw`, with the driver asleep.
- Recompile and run the next supervised T-02 attempt before use.

## Struggles and rejected approaches

Increasing the pulse width or force target was rejected because the 5 ms
resolution and 60 g hard-force guard are the safety properties being tested.

## Risks and follow-up

Confirm the extended fine approach reaches the 30–40 g band without a hard
fault, then repeat stationary contact/clear cycles before G-code testing.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  bounded tune limits.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`:
  separate tune telemetry.
