---
id: RPSW-20260925-003
date: 2026-09-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - toolhead
  - gp27
  - handshake
  - p115
---

# Enable the GP27 normal-print status

## Summary

Flipped `GP27_NORMAL_STATUS_ENABLED` to `true`, so the toolhead now asserts GP27
with its contact-ready (M3) and clear-ready (M5) status while the magnetic
protocol is disarmed.

## Reason

The normal-print handshake path was the last commissioning gate. With F-08's
endpoint items verified by the P113 runs and T-01H accepted (both ready bits now
available), the only remaining item was the master switch plus the on-bench
P115 validation (F-05A).

## Implementation

- `toolhead_config.h`: `GP27_NORMAL_STATUS_ENABLED` `false -> true` with a dated
  comment. `publishNormalPrintStatus()` already gates the output on magnetic
  `DISARMED`, so normal-print GP27 and the magnetic scan cannot overlap.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- F-05A (P115 handshake) remains the on-bench verification: with `P115.macro`
  installed and the converter checkbox ticked, `P115 Q0`/`Q1` must observe the
  inactive-then-active edge. A stuck signal errors `39`.

## Struggles and rejected approaches

The flag was previously held false pending F-05A's formal evidence; it is now
enabled ahead of that final bench check at the operator's direction, with the
P115 timeout as the safety net against a stuck signal.

## Risks and follow-up

- Until F-05A passes and the converter box is ticked, the controller still uses
  the fixed `G4` dwells; enabling the flag alone does not change generated
  programs.
- F-08 is marked passed on the strength of the P113 runs.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
