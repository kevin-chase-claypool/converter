---
id: HW-20260905-004
date: 2026-09-05
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB V1.01
  - A-axis TB6600 and 17HS15-1504S-X1 motor
  - 12:1 rotating bed
tags:
  - a-axis
  - bed-ratio
  - calibration
  - commissioning
related:
  - M-05
  - HW-20260905-003
  - docs/report/lab-notes/2026-09-05-m-05-bed-ratio-check.md
---

# Verify the A-axis 12:1 bed ratio

## Summary

The calibrated A-axis passed the full bed-ratio check. A commanded `A4320`
(12 motor revolutions) produced one complete bed revolution, and the bed
returned exactly to its starting reference after reverse motion.

## Reason

The A-axis motor-degree calibration had passed its one-motor-revolution check,
but the installed 12:1 pulley reduction still needed physical verification
before using A-axis commands for bed-angle registration and coordinated motion.

## Implementation

The operator retained `$103 = 4.44444` steps per commanded motor-degree,
marked the bed against a fixed frame reference, and ran equal forward and
reverse `A4320` moves at `F10000`. The pen was not engaged and the bed was
free to rotate through the tested range.

## Verification

- `G1 A4320 F10000` returned the bed mark to the fixed reference after one bed
  revolution.
- `G1 A-4320 F10000` returned the bed to its original position.
- Repeated forward/reverse checks returned exactly to the starting mark each
  time, with no reported lost-step or position error.
- M-05 is **passed** for the unloaded geometric ratio check.

## Struggles and rejected approaches

None encountered. The test used a unique physical mark and a fixed frame
pointer so a return to the reference could be distinguished from an ambiguous
or partially rotated bed position.

## Risks and follow-up

This validates the unloaded 12:1 scaling, not the final plotting feed,
pen-engaged force behavior, magnetic index repeatability, or thermal limits.
Continue with the X rate check and M-03 X/Y dimensional calibration, followed
by the separate homing, registration, and toolhead validation tests.

## Files

- `docs/report/lab-notes/2026-09-05-m-05-bed-ratio-check.md`: records the
  commands, physical reference procedure, and pass result.
- `docs/testing/TEST_PLAN.md`: records M-05 as passed and links the evidence.
- `docs/report/lab-notes/README.md`: adds the new note to the index.
- `docs/project/ENGINEERING_LOG.md`: records the completed commissioning
  milestone.
