---
id: RPSW-20260929-005
date: 2026-09-29
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - firmware/pen_pressure/README.md
  - docs/testing/TEST_PLAN.md
tags:
  - toolhead
  - force-control
  - pen-force
  - revert
related:
  - RPSW-20260929-004
  - docs/integration/INTERFACES.md
---

# Revert the pen force target to 45 g with a ±15 g band

## Summary

Restores the integrated toolhead's drawing-force target to 45 g with a ±15 g
target-ready band (30-60 g). This supersedes `RPSW-20260929-004`, which had
lowered the target to 38 g with a ±10 g band (28-48 g).

## Reason

The operator watched a print run with the lighter setting and judged it
unacceptable, and asked for the earlier values back. The setting RPSW-20260929-004
replaced had already been in use for printing, so this restores the last accepted
configuration rather than introducing a third untested one.

## Implementation

In `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:

- `TARGET_FORCE_RAW_DELTA` and `CONTACT_RAW_DELTA` back to `226745` (45 g).
- `CONTACT_READY_TOLERANCE_RAW` back to `75582` (±15 g).
- `HARD_FORCE_RAW_DELTA` stays `377908` (75 g) and `HOLD_URGENT_RELIEF_RAW`
  stays `100775` (20 g above target), so the relief trigger returns to 65 g,
  5 g beyond the band top and 10 g below the hard limit.

The comments in the same file now record the 2026-09-29 38 g / ±10 g attempt and
its revert so the experiment is not silently repeated. The current-state
documents were restored to the 45 g / 30-60 g values:
`firmware/pen_pressure/README.md`, `firmware/pen_pressure/CONTROL_STRATEGY.md`,
`firmware/README.md`, `docs/integration/INTERFACES.md`, and
`docs/testing/TEST_PLAN.md` (T-02, T-03).

Two corrections from `RPSW-20260929-004` were deliberately kept because they
were documentation defects independent of the force decision and they match the
installed code: the 10 ms coarse-pulse width with its 2:1 fine-pulse credit, and
the 75 g hard-limit value.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350` succeeded
  for `firmware/pen_pressure/pro_micro_rp2350_toolhead`. The force-envelope
  `static_assert` is evaluated at compile time and accepts the restored values.
- `python tools\docs_index.py --write` and `--check` passed.
- No new bench measurement. The restored values are the configuration that was
  printing before 2026-09-29, but the toolhead must still be re-flashed.

## Struggles and rejected approaches

This is the third recorded rejection of a narrow hold band: ±5 g failed on
2026-09-23, ±10 g was widened to ±15 g on 2026-09-25 for the same reason, and
the 2026-09-29 ±10 g retry was rejected during a print run. Do not narrow the
band again without first addressing the drift source (rail friction or stiction,
carriage/bearing condition, or the hold correction cadence) and producing
per-stroke force evidence.

## Risks and follow-up

- The exact failure mode observed during the print run is not recorded in this
  note. Record it in the T-02/T-03 evidence so the next attempt starts from
  measurement rather than preference.
- If lighter marking is wanted later, change the target alone while keeping the
  ±15 g band, and validate it on T-02/T-03 before printing.
- The 45 g target remains a supervised bench setting, not a production-qualified
  one; T-01J per-tool preflight still applies.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: restored
  45 g target and ±15 g band, with the revert recorded in the comments.
- `firmware/pen_pressure/README.md`: current target, band, and relief values.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: band values.
- `firmware/README.md`: hold-band value.
- `docs/integration/INTERFACES.md`: toolhead force values.
- `docs/testing/TEST_PLAN.md`: T-02 and T-03 acceptance values.
- `docs/changes/rp23cnc-software/2026/2026-09-29-lower-pen-force-target-to-38g.md`:
  marked superseded.
- `docs/project/ENGINEERING_LOG.md`: dated entry for this session.
