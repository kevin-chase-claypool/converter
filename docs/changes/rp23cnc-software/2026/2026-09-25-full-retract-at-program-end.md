---
id: RPSW-20260925-009
date: 2026-09-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
  - software/converter_core/gcode.py
tags:
  - toolhead
  - full-retract
  - gp28
  - aux0
  - program-end
  - converter
---

# Full retract the pen to GP2 at program end

## Summary

The toolhead now treats an Aux0/GP28 assertion during normal print as a request
to retract the pen all the way up to the GP2 lift-home switch, instead of only
the ~1 mm M5 clearance lift. The converter emits that request after the final
M5 so the pen is fully clear of the bed when the paper is removed.

## Reason

The normal M5 leaves the pen about 1 mm above the paper, which was enough to
avoid dragging but left the pen hovering over the bed at the end of a print. A
full retract to GP2 clears the pen completely so the paper can be removed
without touching the pen.

## Implementation

- `toolhead_shared.h`: new `STATUS_FULL_RETRACT_REQUESTED` flag.
- `magnetic_homing.cpp`: in `DISARMED`, a healthy arm assertion that is not
  magnetic-armed (pen off GP2) sets the full-retract flag instead of faulting;
  `publishNormalPrintStatus()` holds GP27 low while the flag is pending so the
  controller observes a clean inactive-to-active edge.
- `pressure_controller.cpp`: consumes the flag once and drives `LIFTING` until
  GP2 asserts, then reports clear-ready.
- `gcode.py`: `append_full_retract()` emits `M65 P0` / `G65 P115 Q0` (or a
  fixed `G4` dwell) / `M64 P0` after the final pen-up, before the G53 park.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- `python -m unittest discover -s software/tests` passes (24 tests).

## Struggles and rejected approaches

Reusing the M3/M5 line with a timing threshold was rejected because M5 stays
held during ordinary between-contour travel, so a long travel would falsely
trigger a full retract. Aux0/GP28 is idle during normal print and gives a
distinct, unambiguous request without new wiring.

## Risks and follow-up

- An Aux0 assertion that is not preceded by the pen reaching GP2 no longer
  faults the magnetic controller; it instead performs a safe full retract. The
  magnetic scan itself remains gated by the same readiness prerequisites.
- Confirm on-bench that the `M65 P0` full-retract request and its `P115 Q0`
  acknowledgement complete before the G53 park on the installed machine.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_shared.h`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/magnetic_homing.cpp`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`
- `software/converter_core/gcode.py`
- `software/tests/test_theta_feed.py`
