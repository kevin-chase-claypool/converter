---
id: RPSW-20260923-006
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - settle
  - performance
  - force-control
  - t02
related:
  - RPSW-20260922-034
  - RPSW-20260923-005
---

# Reduce the sensing settle to the measured 300 ms

## Summary

The toolhead's seek, tune, and clear-tare settles drop from 500 ms to 300 ms,
roughly halving the per-pulse cost of every pen transition.

## Reason

The 500 ms value was borrowed from E-09F rather than measured on this
mechanism, and it is the dominant per-stroke cost in a print: the warm cycles in
the 2026-09-23 nine-cycle run used 23-28 pulses per M3, so each pen-down cost
12-14 seconds almost entirely in settle time.

The 2026-09-23 E-09E settle trace measured it directly. Over three 5 ms DOWN
pulses with the pen clear, the 16-sample filtered value reached within about
1,000 raw (roughly 0.2 g) of its plateau at 218, 220, and 294 ms, against a tail
noise floor of 299-692 raw peak-to-peak. 300 ms covers the worst of the three at
about 1.5x its noise.

## Implementation

`toolhead_config.h`:

- `HOME_SEEK_SETTLE_MS` 500 -> 300
- `HOME_TUNE_SETTLE_MS` 500 -> 300
- `PEN_CLEAR_TARE_SETTLE_MS` 500 -> 300

The two timeouts are left at 60 s. The static assertions still pass: the worst
seek sequence is 100 x 325 ms and the worst tune sequence is 100 x 305 ms, both
well inside the 60 s bound.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 82448 bytes program storage and 16236 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench confirmation is required. The expected effect is a first-touch
  reference spread and fault rate no worse than the nine-cycle run that
  motivated the 500 ms value.

## Struggles and rejected approaches

Going lower than 300 ms was rejected. The trace shows the error at 121-146 ms is
still 1,700-5,955 raw depending on the trace, and under-reading force during the
approach is exactly the mechanism that produced the earlier overshoot into the
60 g hard limit. Cutting to 250 ms would halve cost again but leave the worst
trace around 2,000 raw from its plateau at the decision point.

Per-constant tuning was also rejected: the tare settle is paid once per stroke
while the seek and tune settles are paid roughly 25 times, but all three sit on
the same measured mechanism response, and one value keeps the behaviour
comparable across runs.

## Risks and follow-up

The measurement is clear-air. Near contact, with the spring compressed and the
tip touching paper, the settling could be slower, so a cycle-set re-run is the
acceptance check rather than the trace alone. If the reference spread widens or
a hard-force trip returns, the first response is to restore 500 ms on
`HOME_SEEK_SETTLE_MS` and `HOME_TUNE_SETTLE_MS` only.

The larger remaining cost is the pulse count per M3, not the settle. Twenty-five
pulses at 300 ms is still about 7.5 seconds per pen-down; reducing that needs
the deterministic-clearance work, not a shorter settle.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: settle constants and their measured justification.
- `firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: align the documented settle.
