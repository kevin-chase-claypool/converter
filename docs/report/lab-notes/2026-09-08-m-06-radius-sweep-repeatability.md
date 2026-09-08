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

For the same run, the owner recorded 1:15.05 (75.05 s) of actual bed movement.
The converter preview reported 2:40.58 (160.58 s). The preview therefore
overestimated the observed motion interval by 1:25.53 (85.53 s), or about
2.14×. This is one timing observation; it does not by itself identify whether
the difference is in preview modelling, its scope versus the stopwatch interval,
or machine execution.

## Limits and next action

No per-radius elapsed times or screenshots were captured in this report. The
geometry/repeatability observation is positive, but M-06 timing validation
remains open: repeat the total timing or record inner/middle/outer elapsed
times and compare their like-for-like scope with the converter preview estimate. See
[`../../testing/TEST_PLAN.md`](../../testing/TEST_PLAN.md) and
[`../../changes/hardware/2026/2026-09-07-verify-converter-motion-and-guarded-xy-envelope.md`](../../changes/hardware/2026/2026-09-07-verify-converter-motion-and-guarded-xy-envelope.md).
