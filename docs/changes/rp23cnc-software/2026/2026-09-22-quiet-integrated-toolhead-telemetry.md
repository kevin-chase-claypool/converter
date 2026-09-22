---
id: RPSW-20260922-019
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino
  - integrated Pro Micro service console
tags:
  - serial-monitor
  - telemetry
  - fault-diagnostics
  - cs1238
related:
  - docs/integration/INTERFACES.md
  - docs/project/ENGINEERING_LOG.md
---

# Make integrated toolhead telemetry quiet by default

## Summary

Replace the continuous one-second serial status flood with event-driven
pressure-state output, one-shot snapshots, and an optional live stream.

## Reason

The operator found the continuously scrolling Arduino Serial Monitor difficult
to use. The captured output contained only repeated latched fault lines and did
not include the sample that originally crossed the hard-force limit.

## Implementation

- Emit one status record when the pressure state changes; emit an explicit
  `FAULT_EVENT` once when the controller enters a fault.
- Add `p` for one snapshot and `v` to toggle the one-second live stream. The
  stream is off after reset.
- Add `cs1238_tare`, `tare_valid`, `force_norm_raw`, and `hard_limit_raw` to
  telemetry, and rename the TMAG counter from `samples` to `mag_samples`.
- Keep `?`, `t`, `e`, `l`, `a`, and `c` command behavior unchanged.

## Verification

- `arduino-cli compile --build-path <temporary-directory> --fqbn
  rp2040:rp2040:sparkfun_promicrorp2350
  firmware\pen_pressure\pro_micro_rp2350_toolhead` passed (79,776 bytes
  program storage; 16,164 bytes global memory).
- `python tools\docs_index.py --write` and `--check` passed for 189 change
  notes. Hardware confirmation that the first-fault record identifies the
  autonomous startup fault remains pending.
- Hardware confirmation that the first-fault record identifies the autonomous
  startup fault remains pending.

## Struggles and rejected approaches

Increasing the interval alone would still create an endless scroll and could
continue to hide the one-time fault transition. Event-driven output plus an
explicit stream toggle gives both a quiet default and live monitoring on demand.

## Risks and follow-up

The underlying autonomous hard-force fault is not diagnosed by this UI change.
The next serial capture must start before power-on and preserve the single
`FAULT_EVENT` record. Do not clear the fault until that record has been saved.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`:
  event-driven output, snapshot/stream commands, and fault details.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.*`:
  expose normalized force and tare validity for diagnostics.
- `firmware/pen_pressure/README.md` and `docs/integration/INTERFACES.md`:
  document serial behavior and commands.
- `docs/project/ENGINEERING_LOG.md`: capture evidence, scope, and next action.
