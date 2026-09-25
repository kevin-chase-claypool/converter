---
id: RPSW-20260925-007
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

# Guarantee a GP27 inactive interval on every pen-command transition

## Summary

The toolhead now forces GP27 inactive for a guaranteed 50 ms on every M3/M5
command transition before the normal-print ready status may reassert. This
lets the `P115 Q1` acknowledgement always observe a fresh inactive-to-active
completion edge, even when the physical pen move is instantaneous.

## Reason

Normal-print status asserts GP27 in both stable states (contact-ready and
clear-ready), so the only inactive interval was the seek/lift itself. When a
transition completed instantly — for example an M5 issued while the pen was
already at the GP2 lift switch, which jumps straight back to `LIFTED` — GP27
stayed asserted and `P115 Q1` timed out its 0.50 s stale-state release phase
with `error:39 - Value out of range`, aborting the program mid-print.

## Implementation

- `toolhead_config.h`: new `GP27_TRANSITION_LOW_MS = 50` with a dated comment.
- `magnetic_homing.h`: added command-edge and low-window tracking state.
- `magnetic_homing.cpp`: `publishNormalPrintStatus()` now reads GP29 on core 1
  to detect the M3/M5 edge and holds the GP27 output low for the floor before
  reasserting the derived ready state. The floor never lengthens a normal
  seek/lift, which already stays inactive far longer than 50 ms.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- F-05A (P115 handshake) remains the on-bench confirmation: each `P115 Q1`
  after M3/M5 must observe the inactive-then-active edge with no error 39.

## Struggles and rejected approaches

Loosening `P115 Q1` to skip the stale-state release phase was rejected because
that check is what stops the previous M3/M5 completion from being mistaken for
the current command's acknowledgement. The firmware-side guaranteed low window
keeps that protection intact.

## Risks and follow-up

- Confirm on-bench that the 50 ms floor clears F-08's 20 ms GP27-inactive
  requirement across a mixed sequence of normal and GP2-starting M5s.
- The floor adds no latency to ordinary seek/lift; it only bounds the rare
  already-clear transition.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/magnetic_homing.h`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/magnetic_homing.cpp`
