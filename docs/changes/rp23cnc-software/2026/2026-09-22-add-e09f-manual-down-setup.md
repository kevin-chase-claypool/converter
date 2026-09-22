---
id: RPSW-20260922-012
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e09f_cs1238_guarded_force_hold
tags:
  - e-09f
  - n20
  - pen-installation
  - manual-control
related:
  - RPSW-20260922-010
---

# Add E-09F manual down setup pulse

## Summary

E-09F now accepts `d` / `DOWN` for one guarded 5 ms N20 DOWN pulse during
manual pen installation.

## Reason

The installed CS1238 signal can enter the nominal raw force band while the pen
is still air-gapped, so it cannot presently serve as an automatic paper-contact
detector. The operator needs a bounded way to establish an approximate
mechanical drawing preload on actual paper.

## Implementation

- Added `d` / `DOWN`, one 5 ms pulse using the existing ULT check and
  driver-sleep behavior.
- It cancels automatic state and does not claim that a raw value means contact.
- Retained `u` for one guarded 5 ms retract; twenty UP pulses (100 ms) are the
  observed provisional 1.75 mm mechanical clear motion.

## Verification

- Firmware compilation is required before flashing.
- The physical twenty-pulse UP / 1.75 mm clear observation is recorded in the
  E-09F lab note. `d` itself has not yet been powered after this change.

## Struggles and rejected approaches

Using `s` for pen installation was rejected because it can stop in a nominal
raw band before the pen physically reaches paper.

## Risks and follow-up

`d` is a supervised setup command, not production M3. Use one pulse at a time
with the physical cutoff reachable. Production M3/M5 remains gated pending a
separate design decision and verification.

## Files

- `firmware/pen_pressure/e09f_cs1238_guarded_force_hold/e09f_cs1238_guarded_force_hold.ino`: manual DOWN command.
- `firmware/pen_pressure/e09f_cs1238_guarded_force_hold/README.md`: setup procedure and safety boundary.
