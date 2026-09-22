---
id: RPSW-20260922-013
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
  - CS1238/N20 M3-M5 control path
tags:
  - mechanical-preload
  - m3-m5
  - cs1238
  - pen-clearance
related:
  - E-09F
  - T-01H
---

# Stage mechanical-preload M3/M5 behavior

## Summary

Added a disabled-by-default controller mode that uses the bench-measured 100 ms
DOWN/UP travel pair for an operator-installed pen preload. This is staged for
the current non-precision plotter; it does not replace the validated raw-force
control path.

## Reason

E-09F bench evidence showed that twenty guarded 5 ms UP pulses produced about
1.75 mm of clearance and twenty matching DOWN pulses restored acceptable paper
resistance. The raw CS1238 threshold could enter its target band while the pen
was still physically air-gapped, so raw seeking is not a reliable contact
detector for this installed-pen setup.

## Implementation

- `MECHANICAL_PRELOAD_MODE` in `toolhead_config.h` selects the staged path and
  remains `false` behind commissioning gates.
- When deliberately enabled, M3 applies a bounded 100 ms DOWN move, stops, and
  leaves the motor asleep; M5 applies a bounded 100 ms UP move and returns to
  `LIFTED`.
- After the timed M3 preload, the CS1238 16-sample moving average resumes
  bounded force corrections toward the calibrated target. It does not seek
  initial paper contact. GP2 remains the maximum-UP limit, and existing
  actuator-direction, lift-reference, magnetic, clear, and other safety gates
  remain in force.

## Verification

- Existing E-09F post-flash bench evidence: 20 x 5 ms UP ≈ 1.75 mm clearance;
  20 x 5 ms DOWN restored operator-judged paper resistance.
- Source compile verification is run with the RP2350 Arduino CLI command below.

## Struggles and rejected approaches

The initial raw-force seek/release behavior was retained as the normal validated
path, but not used for this staged mode because a stable raw target did not
prove physical paper contact or a repeatable air gap after pen changes.

## Risks and follow-up

The mode is intentionally not authorized for flashing or production use yet.
Commission actuator direction and lift reference first, then repeat the
installed-pen M3/M5 travel check. A future per-pen validated force profile may
supersede this fixed-duration alternative.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: staged
  mode flag and 100 ms travel constant.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  bounded M3/M5 state transitions.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`: state
  declaration.
- `firmware/pen_pressure/README.md`: operational and safety notes.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: controller design note.
- `docs/integration/INTERFACES.md`: M3/M5 contract documentation.
