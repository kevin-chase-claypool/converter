---
id: HW-20260909-002
date: 2026-09-09
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - N20 toolhead actuator
tags:
  - toolhead
  - n20
  - actuator
  - commissioning
related:
  - HW-20260909-001
---

# Order faster toolhead actuator candidates

## Summary

Ordered 6 V 400 RPM and 1000 RPM N20 threaded-gear motor candidates to assess
whether they improve the toolhead's slow 200 RPM actuator response.

## Reason

The installed 200 RPM actuator is too slow for the desired toolhead testing.

## Implementation

The present 200 RPM motor remains installed. No motor selection, wiring, or
firmware constant changed. Loaded tests are paused because an actuator swap can
change torque, current, self-locking, backlash, travel, and pulse response.

## Verification

Purchase reported by the project owner; exact received motor specifications and
mechanical compatibility remain unverified.

## Struggles and rejected approaches

Continuing force/contact characterization with the outgoing motor was rejected:
those results cannot qualify either replacement candidate.

## Risks and follow-up

Higher RPM does not by itself establish adequate force or safe self-locking.
On receipt, verify shaft/thread compatibility and repeat E-05, guarded E-06,
E-15, direction, GP2 travel, and T-01 characterization before force control.

## Files

- `docs/hardware/BOM.md`: ordered actuator candidates and receipt gates.
- `docs/testing/TEST_PLAN.md`: hardware-change hold and required requalification.
