---
id: RPSW-20261002-001
date: 2026-10-02
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - m5
  - pen-clear
  - clearance
  - toolhead
  - drag
related:
  - RPSW-20260923-011
  - RPSW-20260925-001
---

# Raise the M5 clearance pulse to 70 ms

## Summary

`PEN_CLEAR_EXTRA_LIFT_MS` rises from 57 ms to 70 ms, targeting about 1.2 mm of
pen-up clearance instead of about 1 mm. Normal `M5` still releases to the
load-cell clear band first, then adds this fixed UP pulse.

## Reason

The operator reported concentric drag marks outside the artwork on production
prints. Pen-up travel (`M5` followed by X/Y/A moves) was leaving the tip in
contact with the paper, which is the expected symptom of a clearance air gap
that is too small. The 57 ms value was accepted under T-01H on 2026-09-25, but
that run measured the gap at ~1.75 mm while the derivation comment treated
57 ms as ~1 mm, so the true installed gap is the uncertain quantity. 70 ms
sits between the reduced 1 mm target and the larger 100 ms value the machine
ran before 2026-09-23.

## Implementation

- `toolhead_config.h`: `PEN_CLEAR_EXTRA_LIFT_MS` 57 -> 70, with the reason and
  the open re-measurement recorded in the adjacent comments. `PEN_CLEAR_VALID`
  stays `true`; the change only increases clearance above the accepted value
  and does not alter release detection.
- `pressure_controller.cpp`: replaced two stale "100 ms clearance" comments
  with references to `PEN_CLEAR_EXTRA_LIFT_MS` so the source no longer carries
  a third, wrong value.

No converter change is needed: the lift is a firmware time, not a distance
commanded in G-code. Warm-seek travel re-learns the new gap through the
existing moving average, so no seek constant changed.

## Verification

- `arduino-cli compile` for `rp2040:rp2040:sparkfun_promicrorp2350`: see the
  session result recorded in the engineering log.
- `python tools\docs_index.py --write` and `--check`: pass.
- Hardware verification remains **open**. No scale or no-drag print run was
  possible in this session, so the 70 ms pen-tip gap is an estimate, not a
  measurement.

## Struggles and rejected approaches

The 57 ms value was chosen to shorten the next `M3` seek, which is why the
reduction was made on 2026-09-23. Reverting straight to the old 100 ms would
restore the long warm seek for a margin that may not be needed; 70 ms is the
smallest step that clearly exceeds the reported drag condition.

## Risks and follow-up

- The clearance must also stay below the GP2 full-home switch. The clearance
  state stops immediately if GP2 asserts, so a longer pulse cannot drive into
  the switch; 70 ms is far inside the 1800 ms release timeout.
- Re-run the T-01H-style no-drag check with the pen-tip gap measured directly.
  If the measured gap is still not clearly clear, raise the pulse again; if it
  is large, the value can be trimmed back toward 57 ms.
- Technical debt: `docs/project/ENGINEERING_LOG.md` is ~7,200 lines, far past
  the 1,000-line archive trigger in `AGENTS.md`, and its generated topic index
  currently covers only the pre-2026-09-11 archive rather than the full log.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: clearance constant and gate comment.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: stale clearance comments.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`: current clearance value.
- `docs/integration/INTERFACES.md`: M5 clearance description.
- `docs/testing/TEST_PLAN.md`: T-01H state and the open re-verification.
- `software/README.md`: converter dwell note that quotes the clearance height.
