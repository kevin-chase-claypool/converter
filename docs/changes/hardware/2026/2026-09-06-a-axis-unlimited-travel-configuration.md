---
id: HW-20260906-003
date: 2026-09-06
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB V1.01
  - A-axis rotary bed
  - grblHAL axis settings
tags:
  - a-axis
  - rotary
  - soft-limits
  - configuration
related:
  - M-05
  - M-07
  - HW-20260906-002
---

# Configure the A axis without a finite travel limit

## Summary

The continuous A-axis rotary bed is configured with `$133=0.000` degrees,
removing the prior arbitrary 200-degree maximum-travel entry without disabling
A-axis motion.

## Reason

The A-axis bed has no mechanical endpoint. A finite maximum-travel value would
misrepresent the machine and could later interfere with conventional soft-limit
or homing behavior.

## Implementation

The controller setting was changed to `$133=0`. X and Y retain their measured
508 mm end-to-end physical travel entries. Those measured distances cannot yet
be enforced as controller soft limits until their physical home/limit system is
commissioned. No soft-limit or conventional A-axis homing behavior was enabled.

## Verification

- ioSender Settings: Grbl displays `$133` as `0.000 deg`.
- A-axis travel resolution, maximum rate, and acceleration remain
  `4.44444 step/deg`, `80000 deg/min`, and `6000 deg/sec^2`, respectively.

## Struggles and rejected approaches

Retaining the inherited 200-degree A maximum travel was rejected because it is
not a physical property of the continuously rotating bed.

## Risks and follow-up

`$133=0` is not an A-axis registration solution. Keep A out of ordinary
finite-travel homing/soft-limit workflows; complete the P100 magnetic
registration and X/Y homing/limit work before enabling production limits.

## Files

- `firmware/grblhal/config/build-record.md`: current controller setting
  snapshot.
- `docs/integration/INTERFACES.md`: A-axis travel contract.
- `docs/project/ENGINEERING_LOG.md`: dated configuration decision.
