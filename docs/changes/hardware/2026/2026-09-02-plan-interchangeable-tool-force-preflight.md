---
id: HW-20260902-001
date: 2026-09-02
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - toolhead-force-control
  - firmware/pen_pressure
  - firmware/grblhal/macros/P100.macro
tags:
  - toolhead
  - interchangeable-tools
  - load-cell
  - p100
  - pen-clear
  - testing
related:
  - HW-20260901-001
  - HW-20260901-002
---

# Plan Interchangeable-Tool Force Preflight

## Summary

Defined a tool-agnostic pen-pressure control contract. Pens, markers, and
pencils may be installed at different vertical clamp heights; normal operation
uses calibrated load-cell contact/release states rather than one shared
pen-tip datum.

## Reason

A fixed pen stop would make one pen's measured retract clearance repeatable,
but would limit interchangeable writing tools. The load cell can determine
whether the installed tip is pressing paper or has released it, so the system
can validate each tool against the actual paper before it plots.

## Implementation

- `CONTACT` is the filtered residual crossing `F_contact_on`; `CLEAR` is the
  residual remaining below `F_release_off`.
- Normal M5 remains force-release plus a tool-validated clearance pulse; it
  never makes a high-cycle trip to GP2.
- The planned P100 preflight is: `LIFT_HOME`, RAM-only no-contact baseline,
  guarded seek to paper, normal M5 clear, and stable clear-band confirmation.
- The current `P100.macro` does not implement or wait for this preflight,
  because the current M3/M5 plus fixed dwell interface has no acknowledgement
  for the local result.
- Added T-01J to validate contact/release, clearance, and selected
  target-force/pulse settings for each intended tool type.
- Added the intended P100 Q0 data-movement order: GP28/GP27 first carries the
  GP2-verified home-ready result, then magnetic state; GP29 carries M3/M5;
  the future touch-check result reuses GP28/GP27 in a defined third protocol
  phase.

## Verification

Documentation-only update. `python tools\\docs_index.py --write` and
`python tools\\docs_index.py --check` must pass. T-01J and a future
acknowledged P100 implementation remain required before automatic tool-change
validation is enabled.

## Struggles and rejected approaches

Using a no-contact load-cell value as an absolute tip-height measurement was
rejected: multiple unloaded positions can produce the same reading. Treating
the previously measured 0.1885 in tip clearance as universal was also rejected;
it applied only to the then-installed pen.

## Risks and follow-up

The load cell proves pressing versus released, not the exact air gap. Each tool
type needs an accepted force target and clearance pulse from T-01J. Automatic
P100 continuation requires a future toolhead acknowledgement/fault interface;
do not claim that the current macro validates a tool change.

## Files

- `firmware/pen_pressure/CONTROL_STRATEGY.md`: records the tool-agnostic state
  contract and force limitations.
- `firmware/pen_pressure/README.md`: adds the user-facing commissioning gate.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: scopes the future P100
  preflight, current interface limitation, and authoritative data movement.
- `docs/testing/TEST_PLAN.md`: adds T-01J.
- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: places T-01J in the gate order.
- `docs/integration/INTERFACES.md`: records that the current macro cannot yet
  wait for a toolhead preflight result.
- `docs/architecture/SYSTEM_ARCHITECTURE.md` and
  `docs/decisions/ADR-004-separate-pen-clear-from-lift-home.md`: preserve the
  architecture decision.
