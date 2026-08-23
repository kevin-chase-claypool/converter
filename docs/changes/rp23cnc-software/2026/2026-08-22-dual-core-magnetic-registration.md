---
id: RPSW-20260822-003
date: 2026-08-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
  - firmware/grblhal/macros/P100.macro
  - hardware/RP2040_RP23U5XBB_homing_candidate.json
tags:
  - dual-core
  - magnetic-registration
  - centroid
  - probe
related:
  - RPSW-20260822-001
  - RPSW-20260822-002
  - ADR-003
---

# Implement Dual-Core Magnetic Registration

## Summary

Implemented a commissioning-gated Pro Micro RP2350 dual-core toolhead firmware
and RP23CNC P100 macro for physical X/Y home, center-magnet centroid raster, and
outer-magnet A registration without adding drag-chain conductors.

## Reason

Physical X/Y switches locate maximum boundaries, not the bed's true center.
The existing one-bit isolated path cannot transmit a numeric centroid, so the
motion controller must record threshold entry/release coordinates and perform
the calculation.

## Implementation

Core 0 owns pressure/safety/HX711/DRV8833 and Core 1 owns TMAG/GP28/GP27. A
two-phase readiness handshake prevents a threshold edge from masquerading as a
center result. P100 additionally requires a separately commissioned
`pen - TMAG` XY vector before center registration. It scans equal-pitch chords, computes a width-weighted area
centroid, registers G54 XY, validates two outer-index observations one bed
revolution apart, and registers G54 A. Candidate build options enable probe and
NGC expression support; the baseline build is unchanged.

## Verification

- Arduino CLI compile for `rp2040:rp2040:sparkfun_promicrorp2350`, warnings
  enabled: passed; 75,628 bytes flash and 15,816 bytes globals.
- `python tools/validate_homing_macro.py`: passed structural and synthetic
  centroid/A arithmetic checks.
- Hardware motion, PRB, isolated-path, and ioSender tests: not run.

## Struggles and rejected approaches

A separate host data link and additional wires were rejected. Treating the
first GP27 threshold transition as center was rejected because it is only one
footprint edge. A single straight pass was rejected in favor of a full
serpentine area sample. A separate RP2040 adapter was corrected to the installed
Pro Micro RP2350.

## Risks and follow-up

F-08 must prove filesystem macro parsing, X and A G38 behavior, probe
parameters, and G54 semantics on the exact candidate build. E-18 must prove the
GP27/U3 path. T-01/T-02/E-07/E-08/M-08/M-09 must supply installed constants,
including the pen-minus-TMAG XY vector. All source commissioning flags remain false, and no UF2 was generated/flashed.
All source commissioning flags remain false, and no UF2 was generated/flashed.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/`: dual-core implementation.
- `firmware/grblhal/macros/P100.macro`: locked home/registration macro.
- `firmware/grblhal/config/homing-candidate.md`: candidate build recipe.
- `docs/decisions/ADR-003-controller-owned-magnetic-registration.md`: lasting ownership decision.
