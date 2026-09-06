---
id: HW-20260906-005
date: 2026-09-06
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB V1.01
  - X and Y normally-closed limit switches
  - ioSender homing configuration
tags:
  - homing
  - limits
  - xy
  - m-07
  - commissioning
related:
  - M-07
  - HW-20260906-004
---

# Commission X/Y physical homing

## Summary

The installed X-east and Y-south switches now provide repeatable physical
X/Y machine homing. Single-axis X and Y tests and three combined XY home cycles
completed without alarm; the two logged repeats finished at the same machine
position.

## Reason

Measured X/Y travel values cannot safely support a repeatable machine reference
until the controller can find the physical home switches while excluding
unwired Z and continuous A from the cycle.

## Implementation

ioSender homing was enabled with single-axis diagnostic commands, a single
XY-only phase, Y-only direction inversion, 500 mm/min search, 50 mm/min
locate, and 10 mm pull-off. The larger pull-off is intentional clearance for a
nearby wire that could otherwise catch on a switch. Hard and soft limits remain
disabled.

## Verification

- `$HX` and `$HY` each completed their correct directional switch cycles.
- One initial and two repeated combined `$H` cycles completed without alarm.
- Both logged repeated homes finished at `MPos:-10.000,-498.000,0.000,0.000`
  with `H:1,3`.

## Struggles and rejected approaches

The prior multi-phase configuration would have attempted Z and A before X/Y.
It was not used; the cycle was explicitly reconfigured to omit both axes.

## Risks and follow-up

Do not enable hard or soft limits yet. Their endpoint behavior and the known
unrelated Z/A input state remain unverified. Homing establishes machine
coordinates only; the observed G54 offset is stale and P100 magnetic bed-center
and A-index registration remain required before converter output is streamed.

## Files

- `docs/report/lab-notes/2026-09-06-m-07-xy-physical-homing.md`: bench record.
- `docs/testing/TEST_PLAN.md`: current M-07 evidence and remaining scope.
- `firmware/README.md`: current firmware/motion commissioning status.
- `firmware/grblhal/config/build-record.md`: installed homing configuration.
- `docs/project/ROADMAP.md`: distinguishes completed physical homing from open
  limit and registration work.
