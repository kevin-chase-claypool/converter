---
id: RPSW-20260930-003
date: 2026-09-30
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
status: implemented
components:
  - firmware/grblhal/macros/P116.macro
tags:
  - iosender
  - macro
  - p116
  - p115
  - lift-home
  - gp2
  - park
  - g53
  - service
related:
  - RPSW-20260924-001
  - RPSW-20260929-002
  - WSW-20260925-003
---

# Add a manual pen-up-to-lift-home and park macro

## Summary

`firmware/grblhal/macros/P116.macro` adds the operator command the converter
previously produced only inside a saved program: normal pen-up, a full retract
to the GP2 lift-home switch, and an off-bed park. The ioSender button is
`PEN UP + PARK`, has confirmation enabled, and issues `G65 P116`. The same
sequence is documented as pasteable ioSender macro text for a controller that
does not carry the macro file.

## Reason

Between runs the operator could only lift the pen and clear the bed by starting
another program, homing, or jogging by hand. The end-of-print sequence already
existed in `software/converter_core/gcode.py` (`append_full_retract` plus
`park_home_command`) and in the toolhead's disarmed-Aux0 full-retract path, but
there was no manual entry point. The owner asked for an ioSender macro that
takes the pen up to the limit switch and parks.

## Implementation

`P116.macro` performs, in order:

1. the self-contained `G21 G90 G94 G17 G54` setup the converter emits as its
   program preamble, so an interrupted session cannot leave the macro in
   incremental or Z-plane modes;
2. `M5` then `G65 P115 Q0`, proving the normal M5 clearance before any gantry
   move (a stuck or faulted toolhead raises `error[39]` here, while the pen is
   still over the bed, instead of after the park move);
3. `M64 P0`, a 0.20 s settle, then `M65 P0` to request the GP2 full retract,
   releasing the arm first so an earlier abort between `M65` and `M64` cannot
   swallow the rising edge that Core 1 needs;
4. `G4 P3.0`, the toolhead's own `BOOT_LIFT_TIME_MS` retract bound, inside which
   a missed switch raises `GP2 lift-home not reached during retract`;
5. `M64 P0` and `G53 G0 X-10 Y-436`, the converter's default off-bed park in
   machine coordinates.

The macro contains no `$H` and does not home, so it stays inside the repository
rule that P111/P113 own physical homing. It requires a known machine position,
the installed Aux0/GP28 `M64`/`M65` output, and the `P115.macro` that F-05A
verified on 2026-09-29.

## Verification

- The packaged command has not been run on the machine yet. `P116` is
  source-ready and awaits the bench verification recorded in
  `docs/project/ROADMAP.md` (Phase 6).
- The retract half of the sequence already ran on the installed hardware: the
  2026-09-29 F-05A session parked the pen at GP2 with `M64 P0`, `M5`, `M65 P0`,
  `G4 P3.0`, `M64 P0`. What remains unverified is the packaged macro - the
  `P115 Q0` clear proof in front of it and the `G53` park behind it.
- Reviewed against the implemented firmware paths it depends on: Core 1's
  `STATUS_FULL_RETRACT_REQUESTED` on a disarmed arm rising edge
  (`magnetic_homing.cpp`), Core 0's `LIFTING` state and its
  `BOOT_LIFT_TIME_MS` fault (`pressure_controller.cpp`), and the
  `PEN_CLEAR_VALID`/`ENABLE` gates that publish clear-ready on GP27.
- `python tools\docs_index.py --write` and `--check` pass.
- Documentation: `firmware/README.md`, `firmware/grblhal/README.md`,
  `firmware/grblhal/macros/README.md`, `docs/integration/INTERFACES.md`, and
  `docs/project/ROADMAP.md`.

## Struggles and rejected approaches

The first draft used a fixed `G4` bound for both the pen-up and the retract, to
match the converter's dwell default and avoid depending on a second macro file.
That was rejected as the shipped default because it lets the `G53` park run
without any evidence that the pen left the paper; `G65 P115 Q0` before the
retract is the one place where the verified GP27 level can actually prevent a
drag. The no-`P115` variant is documented instead of shipped.

A conditional wait on the GP2 edge itself was also rejected. The toolhead
publishes clear-ready at the normal clearance gap, not only at GP2, so no
existing signal distinguishes "cleared the paper" from "reached the switch"; an
`M65`-then-`Q1` handshake is also race-prone because the forced-low interval can
begin or end before the macro's first poll. The retract therefore stays
bounded-and-fault-protected rather than edge-proven.

## Risks and follow-up

- Any `G53` move needs a known machine position; pressed from an unhomed
  controller the macro cannot park and the controller will reject the move.
- `G65 P115 Q0` inherits the unexplained roughly hourly `error[39]` seen with
  the handshake during real printing. Here it fails safe (the gantry does not
  move), but the operator must clear the condition before the machine can be
  parked.
- `P116` does not verify that GP2 was reached, only that the retract stayed
  inside the toolhead's 3 s bound without faulting. A slow or obstructed retract
  is caught by the toolhead's own fault, not by the macro.
- The `G4 P3.0` bound and the park target are duplicated between the macro and
  the converter's `park_x_machine` / `park_y_machine` settings; changing one
  requires changing the other.

## Files

- `firmware/grblhal/macros/P116.macro`: the new service macro.
- `firmware/grblhal/macros/README.md`: P116 behaviour, the button, and the
  pasteable ioSender form.
- `firmware/grblhal/README.md`: P116 summary, plus correcting two stale
  statements that F-05A was still open and P115 was not installed.
- `firmware/README.md`: the full-retract and park contract, and its manual
  entry point.
- `docs/integration/INTERFACES.md`: `G65 P116` row and the manual-button note.
- `docs/project/ROADMAP.md`: the Phase 6 bench-verification task.
