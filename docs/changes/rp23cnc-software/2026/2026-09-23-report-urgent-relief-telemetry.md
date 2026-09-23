---
id: RPSW-20260923-003
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - observability
  - telemetry
  - force-control
related:
  - RPSW-20260923-002
---

# Report urgent over-force relief activity in telemetry

## Summary

The `p` snapshot and every telemetry record now carry
`urgent_relief_count=<activations> urgent_relief_ms=<total driving time>`, so
the over-force relief's activity is visible instead of silent.

## Reason

The 2026-09-23 five-cycle run completed with no faults, but the relief emits no
state event and changes no pressure state, so the log could not show whether it
engaged at all. Without that, a successful run cannot distinguish "relief did
its job" from "the mechanism happened not to run away", and a future fault
cannot show whether the relief fired and lost.

## Implementation

- `pressure_controller.h`: added a relief activation counter and an accumulated
  relief driving time, both exposed through accessors.
- `pressure_controller.cpp`: the counter increments when relief starts; the
  accumulated time adds the elapsed interval whenever relief stops, on either
  the return-to-target or the bounded-maximum path.
- `pro_micro_rp2350_toolhead.ino`: added the two fields to the shared telemetry
  record.
- The telemetry buffer is raised from 512 to 640 characters. The longest
  observed record was about 455 characters, and the writer silently drops a
  record that does not fit, so the extra headroom removes a latent silent-drop
  path now that the record is longer.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 82432 bytes program storage and 16236 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench confirmation that the fields appear and move is pending the next run.

## Struggles and rejected approaches

A single combined `<count>/<ms>` field was rejected as too easy to confuse with
the existing `<completed>/<limit>` counters. A state event on every relief
activation was rejected because relief can repeat within a cycle and the quiet
default output is deliberate.

## Risks and follow-up

The counter is monotonic and never cleared, so a long session shows cumulative
activity; compare successive `p` snapshots rather than reading the raw value as
per-cycle. A cycle with `urgent_relief_count` unchanged across its snapshots
means the relief never fired during that cycle.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: telemetry fields and record buffer.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`: relief counter state and accessors.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: relief accounting.
- `firmware/pen_pressure/README.md`, `docs/integration/INTERFACES.md`: document the new snapshot fields.
