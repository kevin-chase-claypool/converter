---
id: RPSW-20260929-002
date: 2026-09-29
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
status: verified
components:
  - firmware/grblhal/macros/P115.macro
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - p115
  - gp27
  - prb
  - handshake
  - f-05a
  - commissioning
related:
  - RPSW-20260929-001
  - ADR-007
---

# F-05A: the commissioned GP27/PRB pen-transition acknowledgement passed

## Summary

The installed GP27 -> PC817C `U3` -> `PRB` path and the controller-resident
`P115` acknowledgement macro were validated together on the machine. `P115 Q0`
accepted a verified initial clear, `P115 Q1` observed a genuine fresh
inactive-then-active edge after both an `M3` and an `M5`, and both failure
modes raised `error[39]` instead of letting the program run on. F-05A is
recorded as passed.

## Reason

`P115` has been source-ready since 2026-09-21 and the toolhead has published
contact- and clear-ready on GP27 since 2026-09-25, but no bench session had
demonstrated the two together. The converter's handshake option was left off by
default until that evidence existed, and every generated program had to use
fixed `G4` dwells. A pre-check on the same day also found the contact-ready
level toggling in `HOLD_FORCE`, which had to be fixed before the level could be
trusted (`RPSW-20260929-001`).

## Implementation

No production behaviour changed in this entry. It records the verification of
the existing contract plus the two helper test programs that made the
transition observable:

- `samples/gcode/f05a-q7-edge-check.gcode` holds the pen clear, settles, then
  issues `M3` immediately followed by `G65 P115 Q7 B12` so the macro is already
  polling while the toolhead moves.
- `samples/gcode/f05a-p115-strict-pass.gcode` performs the strict sequence
  `Q0` / `M3` + `Q1 B12` / `M5` + `Q1`.

Both depend on the toolhead command and the macro call being streamed back to
back; a single-line send cannot capture the edge because the seek completes
first.

## Verification

- Controller identity: grblHAL `1.1f.20260908`, `[SIGNALS:HSEP]` (probe
  input enabled), `[NEWOPT:...,EXPR,...]`, board `RP23U5XBB`; `$6=1`, `$16=1`.
- Parked clear-ready: toolhead `pressure=LIFTED`, `fault=none`, `lift_home=1`,
  `status=0x0000146f`, `ready=[contact:0 clear:1 det:0]`; controller `Pn:ZAP`.
- Held contact: `pressure=HOLD_FORCE`, `fault=none`, `force_norm_raw=193531`
  inside the 30-60 g band, `status=0x00000c63`, `ready=[contact:1 clear:0
  det:0]`, steady 10 s after `M3`. The pre-fix toggling did not recur.
- `Q7` parked: `release missing` + `completion observed`.
- `Q7` across a streamed `M3`: `release observed` + `completion observed` with
  `Pn:ZAP -> ZA -> ZAP`.
- Strict pass: three `P115 toolhead completion acknowledged` lines and no
  `error[39]`.
- Failure paths: a held-high level returned `P115 command completion did not
  clear its prior ready state`; a disconnected `PROBE SIG` conductor returned
  `P115 toolhead ready acknowledgement timed out`. Both raised `error:39 -
  Value out of range`.
- Independent input proof: dry-contacting `PROBE SIG` to `PROBE GND` flipped
  the controller from `Pn:ZA` to `Pn:ZAP`; `U3` measured 0.147 V and 0.172 V
  asserted to `CTRL_GND`, against the ~0.2 V bench figure.
- Full record: `docs/report/lab-notes/2026-09-29-f-05a-gp27-prb-acknowledgement-pass.md`.

## Struggles and rejected approaches

- An early DMM reading of "0 V" at `PROBE SIG` was a misreading and briefly
  sent the investigation toward the return wiring. The corrected readings and
  the dry-contact flip cleared it.
- Sending the macro by hand was rejected as a method: the seek finishes before
  the next line can be sent, so the macro only ever sees the settled state.
  Both helper programs stream the macro against the transition instead.
- Treating the repeated `Pn:ZA` samples as a fault was rejected once the
  toolhead's own `ready=[...]` field was read at the same moment; those samples
  came from seeks and other non-ready states.

## Risks and follow-up

- The intermittent `error[39]` seen during real printing, roughly once an hour,
  was **not** reproduced in this session. The contact-ready release hysteresis
  in `RPSW-20260929-001` is the targeted mitigation and still needs a real print
  run with the toolhead live stream running to confirm.
- The converter's **Wait for GP27 toolhead ready** default is unchanged and stays
  off pending the project owner's decision; F-05A is no longer the blocker.
- The controller's settings have drifted from the documented snapshot:
  `$21=1`, `$24=1000.0`, `$25=4000.0`, `$110=$111=10000.000`, `$131=451.000`.
  This is recorded as an open discrepancy against
  `firmware/grblhal/config/machine-settings.md` and
  `firmware/grblhal/config/build-record.md`, not as a verified change.

## Files

- `docs/report/lab-notes/2026-09-29-f-05a-gp27-prb-acknowledgement-pass.md`:
  full test record.
- `samples/gcode/f05a-q7-edge-check.gcode`: streamed transition-edge probe.
- `samples/gcode/f05a-p115-strict-pass.gcode`: streamed strict `Q0`/`Q1` pass.
- `docs/testing/TEST_PLAN.md`, `docs/integration/INTERFACES.md`,
  `firmware/README.md`, `firmware/pen_pressure/README.md`,
  `firmware/grblhal/macros/README.md`, `software/README.md`,
  `software/converter_core/settings.py`, `docs/project/ROADMAP.md`: F-05A
  status moved from open to passed, with the unchanged converter default and
  the open items stated.
