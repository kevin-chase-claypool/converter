---
id: RPSW-20260922-009
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
  - cs1238
  - pen-clear
  - fault-handling
related:
  - RPSW-20260922-008
---

# Fix E-09F release hard-limit fault

## Summary

E-09F no longer evaluates the downward contact-force hard limit while it is
performing a bounded upward release/air-gap sequence.

## Reason

During `CLEAR_START`, E-09F reported a transient `tare_delta=967934` and
faulted `hard_force_limit` before it could issue the first safe UP correction.
Upward movement cannot increase pen contact force, so applying that gate in the
release state was incorrect.

## Implementation

- Restricted the hard-force gate to `SEEK_HOLD`, the only automatic state that
  can command downward motion.
- Added an immediate second CS1238 confirmation before a seek/hold hard-limit
  fault, preventing one transient raw sample from causing a false fault while
  the driver is asleep.
- Retained the 30-pulse budget, 30-second timeout, ULT fault checks, GP2
  pre-UP blocking, and driver sleep after every pulse.

## Verification

- `arduino-cli compile --build-path work\\e09f-release-fix-build --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\\pen_pressure\\e09f_cs1238_guarded_force_hold` produced the UF2 artifact.
- No post-fix powered clear run is claimed.

## Struggles and rejected approaches

Treating the reported high raw delta as physical overforce during release was
rejected: the preceding hold was safe, the driver was asleep, and the state had
not yet commanded any new motion. Removing the hard limit from downward seeking
would be unsafe, so it remains there with a two-read confirmation.

## Risks and follow-up

Reflash E-09F, fresh-tare and arm, then repeat `s` followed by `c`. Retain the
terminal result. A real confirmed downward hard-force condition still faults.

## Files

- `firmware/pen_pressure/e09f_cs1238_guarded_force_hold/e09f_cs1238_guarded_force_hold.ino`: state-scoped fault logic.
- `docs/report/lab-notes/2026-09-22-e-09f-guarded-force-hold.md`: failed pre-fix clear evidence.
