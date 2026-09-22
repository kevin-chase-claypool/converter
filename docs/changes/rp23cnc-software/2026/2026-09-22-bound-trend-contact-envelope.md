---
id: RPSW-20260922-030
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
  - force-limit
  - contact-detection
  - safety
related:
  - RPSW-20260922-029
---

# Bound Trend Contact to a Usable Envelope

## Summary

Trend-based contact remains tolerant of a coarse mechanism, but it must begin
in a broad low-force region and cannot move the calibrated 60 g safety ceiling.

## Reason

Repeated M3/M5 testing accepted a persistent 39 g mechanical response as a
touch reference. The relative 35 g target then entered hold near 69 g, outside
the desired endpoint even for a non-precision tool.

## Implementation

A three-window trend is accepted only at or below the provisional 20 g
low-force envelope. A higher persistent response faults with the driver off.
The touch reference still shifts the broad drawing target, but the hard guard
is always the E-09C-calibrated absolute 60 g value.

## Verification

- Arduino CLI compile passed for the SparkFun Pro Micro RP2350 target.
- The selected 20 g envelope requires supervised repeated-cycle T-02 evidence.

## Risks and follow-up

This is not an exact contact threshold. The 20 g candidate is deliberately
broad enough for the observed 9–19 g accepted starts while rejecting the 39 g
false start. Revise it only from repeat-cycle evidence.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`
- `firmware/pen_pressure/CONTROL_STRATEGY.md`
