---
id: RPSW-20261001-001
date: 2026-10-01
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - windows-software
  - hardware
status: verified
components:
  - firmware/grblhal/config/machine-settings.md
  - docs/integration/INTERFACES.md
tags:
  - grblhal
  - settings
  - theta
  - drift
  - safety
related:
  - WSW-20261001-010
  - RPSW-20260930-004
  - software/README.md
---

# Lower the A-axis maximum rate to 20000 motor deg/min

## Summary

`$113` is changed from `80000.000` to `20000.000` motor deg/min on the RP23CNC.
`$123` stays at `6000.000` motor deg/s². Nothing else in the settings dump
changed, and the new value survives a power cycle.

The old value is 110.8 bed deg/s through the 12.03324:1 bed drive, which is
about 21 m/min of pen surface speed at the 185 mm rim - as fast as the X/Y
rapids. The bed cannot hold that; the converter asked for it, the stepper
stalled, and the plot drifted from the lost steps. 20000 motor deg/min is
27.7 bed deg/s, the same surface speed as the converter's 700 mm/min tangential
limit expressed at a 25 mm radius.

## Reason

The converter side of this is `WSW-20261001-010`: the planner no longer emits
bed sweeps it cannot justify (parking the bed instead of rotating more than 15
deg in one segment, or at all near the bed centre) and no longer assumes an A
rate above 20000 motor deg/min. That left the controller as the remaining place
where the old, unachievable rate could still be commanded - controller-side
rapids, jogging, homing, and the pure-X/Y `G0` travels the converter still
emits.

Evidence that the old value was the cause: the file being plotted when the
defect was photographed (`samples/gcode/ben.gcode`) asks for 1333 motor deg/s
in single drawing moves at radii of 0.35-9.1 mm, up to 561 motor deg (46.6 bed
deg) in one move, and unwinds a whole bed revolution as a `G0` rapid at every
`theta_wrap` re-registration.

## Implementation

Applied from ioSender with the machine idle:

```text
$113=20000
$$
```

The full "before" dump, the change, and the acceptance test are recorded in
[`2026-10-01-theta-a-rate-limit-lowering.md`](../../../report/lab-notes/2026-10-01-theta-a-rate-limit-lowering.md).
A 109-key comparison of the before and after dumps shows exactly one difference:
`$113 80000.000 -> 20000.000`.

## Verification

- `$$` after the change reports `$113=20000.000` and `$123=6000.000`; every
  other setting is byte-identical to the before dump.
- The controller was power-cycled and `$$` repeated, so the value is confirmed
  persistent rather than only in the running configuration.
- `$103 = 4.44444` steps per A unit x 4331.9664 motor deg per bed revolution =
  19,253 steps per bed revolution, matching the documented A calibration, so
  the axis really is configured in motor degrees.
- 165 converter tests pass with the matching converter change; the roadmap item
  keeps the physical acceptance test open until it is run.
- **Acceptance test passed 2026-10-01**: `samples/gcode/a-repeatability-test.gcode`
  was run on paper - two bed revolutions out and two back at `F20000`, with the
  pen down, at r = 100 mm and r = 160 mm. Both stations produced **perfect
  circles**: the pen rejoined its own line after eight revolutions of bed travel
  at each radius, and the two radial ticks at each station coincide. The A axis
  therefore holds position at 20000 motor deg/min over the full 104 s of
  rotation.

## Struggles and rejected approaches

- Considered also lowering `$123`. It is already 6000 motor deg/s², equal to
  the converter's assumption, so changing it here would only add a second
  variable before the mark test. Lower it later if the bed still stalls.
- Considered leaving the controller alone and relying on the converter's own
  cap. Rejected: the controller is still the authority for rapids, and a `G0`
  that includes A runs at the configured rate no matter what the converter
  assumes.

## Risks and follow-up

- **The physical acceptance test is still open.** Draw a reference line, run
  `G91 G1 A4331.9664 F20000` and back, redraw, and confirm the marks coincide.
  Until that passes, this is a configuration change with software verification
  only.
- Every rapid that includes A is now slower: one bed revolution takes about
  13 s instead of about 2 s. Homing and jogging are unaffected as long as they
  do not rotate A.
- If the bed still loses position at 20000/6000, lower `$113` in steps
  (`12000`, `8000`) and repeat the mark test; the converter will simply be
  clipped by the controller on the rare moves that exceed it, which slows the
  coordinated move without changing the path.

## Files

- `firmware/grblhal/config/machine-settings.md`: current A motion limit added.
- `docs/integration/INTERFACES.md`: the A-rate sentence now names 20000.
- `docs/report/lab-notes/2026-10-01-theta-a-rate-limit-lowering.md`: the dump
  and the acceptance test.
- `tools/make_a_repeatability_test.py` and
  `samples/gcode/a-repeatability-test.gcode`: the Cycle-Start version of the
  acceptance test - a radial tick, two bed revolutions out and back, the tick
  again, at r = 100 mm and r = 160 mm. Because the out-and-back cancels a pure
  ratio error, it measures lost motion only; the ratio stays with
  `samples/gcode/theta-calibration.gcode`.
