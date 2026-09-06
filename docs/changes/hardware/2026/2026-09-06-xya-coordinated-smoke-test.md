---
id: HW-20260906-004
date: 2026-09-06
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB V1.01
  - X-axis, Y-axis, and A-axis TB6600 drives
  - X/Y gantry and rotary bed
tags:
  - xya
  - coordinated-motion
  - m-06
  - repeatability
  - commissioning
related:
  - M-06
  - HW-20260906-002
  - HW-20260906-003
---

# Verify pen-free coordinated X/Y/A repeatability

## Summary

The X/Y gantry and A rotary bed completed matched simultaneous diagonal moves
at `F15000` and `F20000`. All carriage and bed reference marks returned to
their starts; the operator reported no motion problem.

## Reason

After individual X/Y/A scale and unloaded-motion checks passed, the machine
needed a pen-free coordinated motion check before converter-output validation
and toolhead work.

## Implementation

The reusable test is
[`docs/testing/gcode/xya-coordinated-smoke.gcode`](../../../testing/gcode/xya-coordinated-smoke.gcode).
It runs four relative blocks, each moving X, Y, and A simultaneously, and
restores absolute mode. No tool command is present.

## Verification

- The same symmetric sequence was reported perfect at `F15000` and `F20000`.
- The X/Y carriage reference and A-bed reference returned exactly to their
  starting marks after the `F20000` test.
- No lost-step, direction, or smoothness problem was reported.

## Risks and follow-up

This is a basic repeatability smoke test only. It does not prove the
converter's radius-aware feed timing or geometry. Run a converter-generated
pen-free sample at inner, middle, and outer radii, compare elapsed time with
preview, and inspect emitted G-code before authorizing drawing motion.

## Files

- `docs/testing/gcode/xya-coordinated-smoke.gcode`: reusable M-06 smoke test.
- `docs/report/lab-notes/2026-09-06-m-06-xya-coordinated-smoke.md`: bench
  observations and scope.
- `docs/testing/TEST_PLAN.md`: M-06 evidence and remaining validation.
