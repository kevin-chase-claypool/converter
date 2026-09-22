---
id: RP23CNC-20260921-007
date: 2026-09-21
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P115.macro
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/magnetic_homing.cpp
  - software/converter_core/gcode.py
  - software/converter_core/settings.py
tags:
  - gp27
  - prb
  - m3-m5
  - pen-ready
  - synchronization
  - f-05a
related:
  - docs/decisions/ADR-007-bounded-gp27-pen-ready-wait.md
  - docs/testing/TEST_PLAN.md
---

# Add bounded GP27 toolhead-ready wait

## Summary

Added an opt-in, controller-side GP27/PRB acknowledgement after normal M3/M5
pen transitions. Normal generated G-code retains its existing fixed G4 delays.

## Reason

Fixed delays do not prove that the pen completed contact or clear. The existing
GP27/U3 return can provide a controller-visible completion signal without a
new wire, provided it cannot conflict with the GP28/P100 magnetic protocol.

## Implementation

- Added [`P115.macro`](../../../../firmware/grblhal/macros/P115.macro). `Q1`
  requires the prior ready level to release and a fresh ready assertion;
  `Q0` waits for the initial clear acknowledgement. Its bounded failures raise
  `error[39]` before the next motion block.
- Added an unchecked converter option that emits P115 only with the existing
  non-Z M3/M5 pen contract. Invalid combinations fail settings validation.
- Restricted the integrated toolhead's normal GP27 status to fully
  `DISARMED` magnetic state so P100 keeps exclusive ownership otherwise.
- Added F-05A and ADR-007 to define the required proof before commissioning.

## Verification

- `python -m unittest software.tests.test_theta_feed` — passed (19 tests).
- `python tools\validate_homing_macro.py` — passed static macro safety checks.
- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350 firmware\pen_pressure\pro_micro_rp2350_toolhead` — passed.

## Struggles and rejected approaches

The repository has no grblHAL plugin source tree, so invisible M3/M5 command
interception could not be implemented or verified here. A filesystem macro is
the smallest controller-resident integration compatible with the installed
candidate build and existing `P100` macro practice.

## Risks and follow-up

P115's NGC loop semantics, PRB polarity, and physical timeout behavior remain
unverified. Do not copy/enable it, enable GP27 normal status, or check the
converter option until F-05A passes on an isolated PRB fixture, followed by
the gated integrated test. The 0.50 s and 5.00 s values are candidate bounds,
not measured production timing.

## Files

- `firmware/grblhal/macros/P115.macro`: bounded fresh-edge acknowledgement.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/magnetic_homing.cpp`:
  magnetic-state ownership boundary.
- `software/converter_core/gcode.py`: opt-in P115 emission.
- `software/converter_core/settings.py`: UI setting and contract validation.
- `software/qt_svg_to_gcode.pyw`: checkbox wiring.
- `software/tests/test_theta_feed.py`: converter coverage.
- `tools/validate_homing_macro.py`: P115 static safety validation.
- `docs/decisions/ADR-007-bounded-gp27-pen-ready-wait.md`: durable decision.
