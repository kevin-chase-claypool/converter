---
id: WSW-20261025-004
date: 2026-10-25
category: windows-software
affected_categories:
  - windows-software
  - hardware
  - rp23cnc-software
status: implemented
components:
  - tools/make_bed_compensation_motion_test.py
  - samples/gcode/bed-compensation-motion-test.gcode
  - software/tests/test_bed_compensation_motion_test.py
tags:
  - m-06
  - bed-compensation
  - rotary
  - tracking
  - feed-ladder
  - backlash
  - test-paper
related:
  - HW-20261025-001
  - ADR-009
---

# Expand the XY/A tracking diagnostic into a full one-sheet matrix

## Summary

Replaced the first five-case tracking coupon with an eleven-case, one-run
diagnostic. The new sheet combines three feed requests, compensation on/off,
normal and reverse A sweeps, horizontal and vertical controls, Y-dominant
motion, an inner-radius pair, and an independent repeat without requiring the
paper to be removed or retaped.

## Reason

The first test could distinguish a broadly compensated-only failure from a
broadly mechanical one, but a negative result would not cover enough operating
conditions to justify a production CMYK layer. Repeating short tests would cost
more paper and taping time. One denser matrix provides more diagnostic branches
per sheet.

## Implementation

- Every one of the eleven cases requests `F350`, `F700`, and `F1200` over the
  same bed-space path.
- Each feed request draws forward and immediately back over the exact same
  path, so feed-dependent separation remains visible within one case.
- Cases 3/4, 5/6, 7/8, and 9/10 form compensated/uncompensated pairs for normal
  sweeps, reverse sweeps, Y-dominant motion, and inner-radius motion.
- Cases 1 and 2 are horizontal and vertical A-parked XY controls. Case 11
  repeats the compensated normal-sweep case to expose intermittency.
- Every rotating case performs a coordinated pen-up move from A0 to the start
  angle and another back to A0 before the return witness.
- Four frame crosses are drawn at A0 before and after the matrix to expose
  cumulative position loss.
- The complete output remains one G-code file, one Cycle Start, and no `M0`.

## Verification

- Nine focused generator tests pass for geometry, feed ladder, direction,
  compensation differences, pen-up coverage, case separation, frame repeat,
  paper bounds, and motion guards.
- Full converter discovery passes `544` tests with one expected OpenGL-context
  skip.
- Static preflight reports `4,235` drawing blocks and `33` travel blocks.
- Largest bed rotation inside one drawing block is `0.62 deg`; peak requested
  A rate is `211 motor deg/s` against the `500 motor deg/s` limit.
- There are `18` fed rotating pen-up moves and no bare rotated `G0`.
- Worst commanded bed-path bow is `0.004 mm` at `41 mm` radius; no block
  exceeds the `0.15 mm` path tolerance.
- All emitted machine points remain inside the compensation radius and the
  letter/A4 paper footprint.
- Generator output is deterministic. G-code SHA-256:
  `84806B2367C15061C6A2CB26E88414F225848B83BA777D9AC54156BCEF2EC18C`.
- No physical sheet has been run yet.

## Struggles and rejected approaches

- The original five-case test covered compensation and feed but only one broad
  path orientation, so it could not distinguish X-carriage from Y-carriage
  effects.
- Separate follow-up coupons were rejected because they would repeat setup and
  consume additional sheets. The feed ladder is instead overdrawing within each
  case.
- Directly changing `$701` or acceleration in the same run was rejected because
  it would confound feed, controller, and mechanical effects.

## Risks and follow-up

- All black passes overdraw the same path. A clean result means no visible
  separation at the 0.8 mm pen width; this is not a sub-pixel metrology test.
- A crowded matrix may make transient errors easier to see but harder to
  measure without a straight-down photograph.
- The run requests three passes per case and is expected to take roughly
  10-15 minutes plus pen-transition waits.
- Physical interpretation and any converter change remain pending the sheet.
- Run the complete file once at 100 percent override after `G65 P113`; do not
  change controller settings between cases.

## Files

- `tools/make_bed_compensation_motion_test.py`: eleven-case matrix generator.
- `samples/gcode/bed-compensation-motion-test.gcode`: complete one-run test.
- `software/tests/test_bed_compensation_motion_test.py`: geometry, feed,
  direction, pen-up, frame, bounds, and guard coverage.
- `docs/report/lab-notes/2026-10-25-m-06-compensation-sync-test-plan.md`:
  updated physical-test procedure and interpretation.
- `docs/research/2026-10-25-bed-compensation-and-simultaneous-xy-a-motion.md`:
  expanded discriminating-test design.
