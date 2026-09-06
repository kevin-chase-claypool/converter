# M-06 pen-free coordinated X/Y/A smoke test - 2026-09-06

## Objective

Verify that the installed X, Y, and A axes can execute simultaneous motion in
both directions and return all three physical references to their starts,
without a pen or toolhead force contact.

## Configuration

- Controller: RP23CNC/RP23U5XBB V1.01 through ioSender.
- X: `$100=79.71304` step/mm, `$110=1500` mm/min, `$120=500` mm/sec^2.
- Y: `$101=80.00000` step/mm, `$111=1500` mm/min, `$121=500` mm/sec^2.
- A: `$103=4.44444` step/deg, `$113=80000` deg/min, `$123=6000` deg/sec^2,
  `$133=0`.
- Pen/toolhead: pen absent; no `M3` or `M5` command.

## Commands

```gcode
G21
G94
G91

G1 X50 Y50 A720 F20000
G1 X-50 Y-50 A-720 F20000

G1 X-50 Y50 A-720 F20000
G1 X50 Y-50 A720 F20000

G90
```

The same sequence was also reported perfect at `F15000` before the `F20000`
run.

## Results

- The coordinated sequence was reported perfect at both `F15000` and `F20000`.
- X/Y carriage and A-bed marks returned to their starting references.
- No motion problem, lost-step symptom, or unexpected direction was reported.
- Disposition: **Initial pen-free M-06 coordinated repeatability smoke test
  passed through `F20000`.**

## Scope and next action

This confirms basic simultaneous X/Y/A execution and return repeatability for
the tested symmetric moves. It does not validate converter-generated geometry,
mixed-axis feed semantics, elapsed-time prediction, or radius-aware tangential
speed. Next, run a converter-generated pen-free sample at inner, middle, and
outer radii and compare preview time, emitted blocks, and returned marks.

## Related records

- [`TEST_PLAN.md`](../../testing/TEST_PLAN.md), M-06
- [`xya-coordinated-smoke.gcode`](../../testing/gcode/xya-coordinated-smoke.gcode)
