# Lab Note: 2026-09-08 - M-06 radius-sweep repeatability

## Objective

Exercise the converter-generated pen-free inner, middle, and outer-radius
X/Y/A motion paths and verify return to the temporary G54 reference.

## Configuration

- Test asset: `samples/svg/m06-radius-sweep.svg`.
- Scope: pen-free; no toolhead actuation claimed.
- Work reference: the existing temporary G54 `X0 Y0 A0` marks.

## Commands used

Before and after the run, the operator used:

```gcode
G90
G54
G0 X0 Y0 A0
```

## Result

The owner reported that every radius-sweep path ran perfectly. After the full
program reached `IDLE`, the explicit G54 return landed X, Y, and A exactly on
their reference marks.

## Limits and next action

No elapsed times, per-radius measurements, or screenshots were captured in
this report. The geometry/repeatability observation is positive, but M-06
timing validation remains open: record inner/middle/outer elapsed times and
compare them with the converter preview estimate. See
[`../../testing/TEST_PLAN.md`](../../testing/TEST_PLAN.md) and
[`../../changes/hardware/2026/2026-09-07-verify-converter-motion-and-guarded-xy-envelope.md`](../../changes/hardware/2026/2026-09-07-verify-converter-motion-and-guarded-xy-envelope.md).
