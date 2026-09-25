---
id: RPSW-20260925-006
date: 2026-09-25
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - toolhead
  - fault
  - recovery
  - uart
---

# Auto-clear a latched fault when the pen-up command is held

## Summary

A latched toolhead `FAULT` now clears itself when the controller holds the
pen-up command (GP29 released) for `FAULT_AUTO_CLEAR_MS` (500 ms), retracting to
GP2 and handing control back to GP29 - no service console needed.

## Reason

The machine required the Arduino IDE serial console (`c` then `a`) any time the
toolhead latched a fault, including at startup, because the controller had no
way to clear it. That made the toolhead depend on a laptop connection it should
not need, and the controller already sees the fault through the dropped GP27
ready signal.

## Implementation

- `toolhead_config.h`: `FAULT_AUTO_CLEAR_MS` (500 ms).
- `pressure_controller.cpp`: in `PressureState::FAULT`, track how long GP29 has
  been released; on the debounce, clear the fault reason, drop manual override,
  and transition to `LIFTING` (retract to GP2).
- `pressure_controller.h`: `fault_release_since_ms_`.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` builds
  cleanly.
- Behavioral confirmation is outstanding: latch a fault, hold M5 (or restart
  the controller, whose idle state is M5), and confirm the toolhead retracts and
  returns to GP29 control without the serial console.

## Risks and follow-up

- A fault raised while the controller is asserting M3 stays latched until the
  controller releases (a program M5 or an operator M5), which is intended.
- A persistent fault now cycles clear/re-latch on each M3 instead of waiting for
  a human; it stays visible because GP27 drops and the controller errors out.
- The serial `c`/`a` path is unchanged for bench work.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`
- `firmware/pen_pressure/CONTROL_STRATEGY.md`
