---
id: RPSW-20260923-005
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e09e_cs1238_pen_scale_pulse
tags:
  - settle
  - characterization
  - observability
  - e09e
related:
  - RPSW-20260922-034
---

# Add a one-pulse settle trace to E-09E

## Summary

The E-09E pulse-check sketch now has an `s` shortcut and a `SETTLE` command
that issue one bounded 5 ms DOWN pulse and then stream the 16-sample filtered
CS1238 value for 2.5 seconds, so the installed mechanism's post-pulse settle
time can be measured directly.

## Reason

The integrated controller's seek, tune, and clear-tare waits are all currently
set to 500 ms, a value borrowed from E-09F rather than measured on this
mechanism. The settle wait is the dominant per-stroke cost in a print, so its
actual value needs to be measured before any print-speed work can claim a
target. No existing command produced a continuous post-pulse trace.

## Implementation

- `firmware/pen_pressure/e09e_cs1238_pen_scale_pulse/e09e_cs1238_pen_scale_pulse.ino`:
  added `settleTrace()`. It requires a valid tare and a DOWN-pulse arm, performs
  one guarded 5 ms DOWN pulse through the same enable/fault path as the normal
  pulse, then emits `SETTLE,<time_ms>,<cs1238_filtered>` records for 2500 ms
  using the same 16-sample mean the integrated controller acts on. `s` and
  `SETTLE` are wired into the shortcut and long-command dispatch.

The trace reports the filtered value rather than raw samples so the curve maps
directly to the controller's decision signal, and the ~25 ms cadence keeps the
serial stream readable at 115200 baud.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 66312 bytes program storage and 11196 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench capture is required; the output is human-read `SETTLE,ms,raw` lines.

## Struggles and rejected approaches

Adding the trace to the integrated controller was rejected. It would have had
to pause the pressure state machine or race its motor commands, and the
repository's staged-bring-up pattern keeps characterization in small dedicated
sketches. Emitting raw samples at the full 640 Hz rate was rejected because the
serial port cannot keep up, and the 16-sample filtered value is what the
decisions actually use anyway.

## Risks and follow-up

The DOWN pulse still requires `a` first, so the command cannot run without the
same supervision as every other E-09E down pulse. The trace measures clear-air
settle, not near-contact settle; if the two differ, a near-contact variant will
be needed. An UP-pulse variant for the M5 clearance settle is not yet included.

## Files

- `firmware/pen_pressure/e09e_cs1238_pen_scale_pulse/e09e_cs1238_pen_scale_pulse.ino`: add the settle-trace command and shortcut.
- `firmware/pen_pressure/README.md`, `docs/integration/INTERFACES.md`: document the new shortcut and command.
