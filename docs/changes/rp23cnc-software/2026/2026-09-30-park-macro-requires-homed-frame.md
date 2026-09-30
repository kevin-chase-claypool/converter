---
id: RPSW-20260930-004
date: 2026-09-30
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P116.macro
tags:
  - iosender
  - macro
  - p116
  - p111
  - park
  - g53
  - soft-limit
  - homing
  - safety
  - failed-approach
related:
  - RPSW-20260930-003
  - WSW-20260925-003
  - WSW-20260929-003
---

# Require a homed frame before the park macro moves

## Summary

The first version of `P116.macro` parked the gantry with `G53 G0 X-10 Y-436`
without establishing the machine frame first. Pressing it on 2026-09-30 drove
the gantry into the `-Y` end. `P116` now runs `G65 P111` (physical X/Y home)
before the park, and it no longer risks starting the toolhead's two-phase
magnetic arm when the pen is already parked at GP2.

## Reason

`G53` addresses machine coordinates. That only means anything once the machine
has a machine position, and grblHAL only builds the X/Y work envelope for homed
axes. On an unhomed controller - after power-up and an unlock, for example - the
controller has no frame and no soft-limit envelope, so the same line becomes a
commanded 436 mm move in `-Y` starting from wherever the gantry physically is.
The registered bed centre sits at machine `Y -195.270` and the enforced Y end is
`Y -441`, so only about 246 mm of travel exists below the bed centre. The
operator reported the gantry rammed in `-Y`; that arithmetic is the mechanism.

## Implementation

- `P116.macro`: inserts `G65 P111` - the reviewed single-owner X/Y home - between
  the GP2 full retract and the `G53` park, so the park runs with a known frame
  and under the controller's own soft limits. An out-of-envelope park target is
  now refused with `Alarm:2` instead of being driven.
- `P116.macro`: the arm handling that produced a clean rising edge changed from
  `M64 P0` / `G4 P0.20` / `M65 P0` to `M64 P0` / `G4 P3.5` / `M65 P0`. When the
  pen is already parked at GP2 the toolhead's readiness prerequisites are met,
  so the old pair was exactly the two-phase magnetic arm: the first assertion
  became a `READY_ACK`, and the second one, inside the 3.0 s
  `MAG_REARM_WINDOW_MS`, moved the magnetic state into `SCAN_ACTIVE`. Waiting
  longer than the rearm window makes the single assertion a full-retract
  request again, and it costs nothing when the pen is off GP2.
- Documentation: `firmware/README.md`, `firmware/grblhal/README.md`,
  `firmware/grblhal/macros/README.md`, and `docs/integration/INTERFACES.md`
  now state the homed-frame precondition for every `G53` park, the pasteable
  ioSender form carries `G65 P111`, and `docs/project/ROADMAP.md` records the
  failure, the re-verification conditions, and the park-target margin debt.

## Verification

- Not re-run on the machine. There is no bench evidence that the corrected
  sequence parks correctly; that is the open acceptance item in
  `docs/project/ROADMAP.md`.
- The frame and envelope arithmetic is checked against recorded main-branch
  evidence rather than assumed: `$130=455`, `$131=451`, `$27=10`, `$21=1`, and
  the registered bed centre `-232.449,-195.270` give enforced work limits X
  `-212.551..222.449` and Y `-245.730..185.270` (`WSW-20260929-003`, with its
  same-day correction), i.e. machine `X -445..-10`, `Y -441..-10`.
- The magnetic-arm collision was read out of the installed toolhead source:
  `MAG_REARM_WINDOW_MS = 3000` and `MAG_READY_ACK_DELAY_MS = 20` in
  `toolhead_config.h`, and the `DISARMED` / `READY_ACK` / `WAIT_REARM` /
  `SCAN_ACTIVE` transitions in `magnetic_homing.cpp`.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

The first version avoided a controller-side home deliberately, to keep the
button from duplicating P113's homing cost, and documented "run from `IDLE` with
a known machine position" as the precondition. A documented precondition is not
a guard: the first press violated it and the machine moved 436 mm. The
alternative - leaving the park out and telling the operator to home first - was
rejected because it drops the requested behaviour rather than making it safe.

An explicit "is the machine homed" test was considered and not used: the
installed NGC parameter set in this repository exposes `#<_probe_state>` and the
probe result parameters only, and the build record does not document a
homed-state parameter, so the macro would have had to rely on a guessed name.
The success path from the first version (`M64 P0` / `G4 P0.20` / `M65 P0`) was
also rejected on re-reading the toolhead source, for the magnetic-arm reason
above.

## Risks and follow-up

- The park target is tight. Machine `X-10` is exactly the X pull-off edge and
  `Y-436` is 5 mm inside the enforced Y end, so any drift in `$27`, `$130`, or
  `$131` turns the program-end park - and this button - into `Alarm:2`. Recorded
  as roadmap technical debt; the fix is to derive the target from a fresh `$$`
  readout.
- The converter's own program-end park has the same precondition. It is
  normally satisfied because every run starts with `G65 P113`, but a program
  streamed on an unhomed controller reaches the same unguarded `G53` move.
- Homing inside the button re-zeroes the machine frame. Homing repeatability is
  the binding assumption for the existing G54 registration; the operator should
  re-register with `G65 P113` before the next job rather than assume the
  previous session's G54 survives a park press.
- `G65 P115 Q0` still inherits the unexplained roughly hourly `error[39]` from
  real printing. Here it fails safe by stopping before any motion.
- The exact machine state at the time of the 2026-09-30 failure - homed or not -
  is not yet confirmed by the operator; if the controller had been homed, the
  same fix still applies because the home-then-park order is what puts the move
  under the soft-limit check, but the accepted park target itself would then
  need to be re-derived before it is trusted again.

## Files

- `firmware/grblhal/macros/P116.macro`: the home step and the corrected arm gap.
- `firmware/grblhal/macros/README.md`: P116 behaviour, the failure, the
  pasteable ioSender form, and the park-target margins.
- `firmware/grblhal/README.md`: P116 summary and the reason the home is
  mandatory.
- `firmware/README.md`: the `G53` park precondition in the integration contract.
- `docs/integration/INTERFACES.md`: the `G53 G0` row now states the homed-frame
  requirement; the `G65 P116` row lists the home.
- `docs/project/ROADMAP.md`: failure, re-verification acceptance, and the
  park-target margin debt.
