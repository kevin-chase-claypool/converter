---
id: RPSW-20260910-003
date: 2026-09-10
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - P100.macro
  - P100 macro validator
tags:
  - p100
  - aux0
  - gp28
  - safety
  - macro
related:
  - RPSW-20260910-002
---

# Correct P100 installed Aux0 polarity

## Summary

Corrected the P100 macro's two-phase AUX0 command polarity to match the
installed active-low U2/GP28 path: `M65` arm, `M64` release, `M65` scan.

## Reason

The real hardware F-08 test proved the source's former command order was
backward. Running Q1 with that macro would not test the measured handshake.

## Implementation

All P100 abort and exit paths now use `M64 P0` to release AUX0. The macro
validator now verifies the normal arm/release/re-arm sequence, allows only two
assertions, and requires final release.

## Verification

- `python tools\validate_homing_macro.py` passed.
- `git diff --check` passed.

## Struggles and rejected approaches

The first validator revision incorrectly treated a cleanup command inside the
missing-ACK branch as part of the normal path. It was replaced with a
normal-flow-aware expression check. No hardware command was sent.

## Risks and follow-up

Transfer this corrected macro, then test only `G65 P100 Q1` with TB6600 fuses
still out. Q3/Q4 remain prohibited.

## Files

- `firmware/grblhal/macros/P100.macro`: corrected installed polarity.
- `tools/validate_homing_macro.py`: guarded polarity contract.
