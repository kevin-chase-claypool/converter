---
id: RPSW-20260911-011
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P100.macro
  - firmware/grblhal/macros/P111.macro
  - tools/validate_homing_macro.py
tags:
  - P100
  - P111
  - homing
  - grblHAL
  - safety
related:
  - RPSW-20260911-006
  - RPSW-20260911-010
---

# Isolate P100 System Homing

## Summary

Removed every `$H` from P100 and added P111 as the sole standalone physical
X/Y home macro.

## Reason

The controller trace proved `G65 P100 Q5` entered `Home` exactly three times
before raster motion. P100 contained exactly three literal `$H` lines: the
early Q2 branch plus two legacy Q0/Q2 branches. grblHAL treats `$H` as a
system command while streaming the macro, rather than a flow-controlled
G-code line, so false O-word branches did not protect Q5.

## Implementation

P100 Q2 now returns error 39 with an instruction to use `G65 P111`; all
legacy physical-home branches were removed. P111 performs the previously
verified `M5`, three-second settle, one unconditional `$H`, and completion
message. Q5 is consequently free of any homing system command. The static
validator now rejects `$H` anywhere in P100, enforces P111's minimal
four-command contract, and rejects multiline parenthesized comments in P100.

## Verification

- Captured Q5 controller trace: three `Home` cycles occurred immediately
  after `G65 P100 Q5`, then the raster completed at
  `MPos:-232.313,-218.313`; physical magnet placement agreed with the TMAG
  endpoint.
- `G65 P111` was installed and produced exactly one successful X/Y home cycle
  ending at `MPos:-10.000,-436.000` with `H:1,3`.
- The first installed corrected P100 attempt stopped before motion with
  `error:71`. The source correction included a parenthesized comment split
  across two physical lines; grblHAL parsed its second line as an expression.
  That comment is now one physical line and the validator rejects this form.
- The corrected P100 Q5 run completed with no `Home` state after its command
  and ended at `MPos:-232.013,-218.775`. A magnet placed below the resulting
  TMAG location was visually centered under the chip.

## Risks and follow-up

P100 Q5 is now verified as a center-magnet survey. After a controller restart,
run P111 once before Q5. Q0 remains locked; future production startup must
explicitly compose the separate home stage with the later registration macro
without nesting G65 calls.

## Files

- `firmware/grblhal/macros/P100.macro`: no `$H` system command remains.
- `firmware/grblhal/macros/P111.macro`: isolated physical X/Y home.
- `tools/validate_homing_macro.py`: prevents reintroduction of `$H` to P100.
- `firmware/grblhal/macros/README.md`: revised operator contract.
