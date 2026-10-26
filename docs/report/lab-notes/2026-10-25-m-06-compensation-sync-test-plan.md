# M-06 comprehensive compensated XY/A tracking test plan

**Date:** 2026-10-25

## Purpose

Determine whether the remaining pen/bed tracking error comes from bed
compensation, controller mixed X/Y/A dynamics, residual A-axis mechanics, X/Y
carriage load, direction-dependent backlash, or radius-dependent motion.
The source-level analysis is in
[`2026-10-25-bed-compensation-and-simultaneous-xy-a-motion.md`](../../research/2026-10-25-bed-compensation-and-simultaneous-xy-a-motion.md).

## Program

Generate or regenerate:

```powershell
python tools\make_bed_compensation_motion_test.py
```

Output:

[`bed-compensation-motion-test.gcode`](../../../samples/gcode/bed-compensation-motion-test.gcode)

The program is one file, one Cycle Start, and no `M0` pauses. It uses ordinary
letter/A4 paper and one black 0.8 mm Pigma Micron. Its maximum machine point is
about `150.6 mm` from bed center, inside both the letter-paper footprint and the
compensation coverage.

Each case draws an A0 witness, performs a rotating pen-up move to the path,
redraws the exact path forward and backward at requested `F350`, `F700`, and
`F1200`, performs the reverse rotating pen-up move to A0, and draws the same
witness again.

| Cases | Purpose |
|---|---|
| 1-2 | Horizontal and vertical A-parked XY controls |
| 3-4 | Normal A sweep, uncompensated and compensated |
| 5-6 | Reverse A sweep, uncompensated and compensated |
| 7-8 | Y-dominant A sweep, uncompensated and compensated |
| 9-10 | Inner-radius diagonal sweep, uncompensated and compensated |
| 11 | Independent repeat of the highest-risk compensated normal sweep |

Four frame crosses are drawn at A0 before the matrix and again after every case.
They show cumulative position loss across the complete run.

The motion-path model estimates about 10 minutes of movement, plus
pen-transition waits; allow roughly 10-15 minutes without stopping the program.

## Preconditions

- Use a flat, fully taped sheet. Do not adjust tape during the run.
- Use a black 0.8 mm Pigma Micron with adequate ink.
- Run `G65 P113` once before this program and verify the center check.
- Do not re-register, move the sheet, or change artwork offsets during the run.
- Confirm `$113=30000`, `$123=6000`, `$376=1`, and `$701=0`.
- Use 100 percent feed override.
- Have the toolhead and motion emergency stop available.

## Static verification completed

```text
moves: 4235 drawing, 33 travel
largest bed rotation inside one drawing block: 0.62 deg (cap 15.0)
largest demanded A rate: 211 motor deg/s (limit 500)
pen-up moves carrying rotation: 18 fed, 0 bare G0
worst commanded bed-path bow: 0.004 mm at 41 mm radius
moves exceeding 0.15 mm path tolerance: 0
```

The preflight reports PASS against the current bed-step, A-rate, bare-rapid,
and path-tolerance guards. Generator output is deterministic; the committed
G-code SHA-256 is
`84806B2367C15061C6A2CB26E88414F225848B83BA777D9AC54156BCEF2EC18C`.

## Accept and interpretation

Photograph the sheet straight down after completion. Inspect every witness,
each of the three feed overlays, both trace directions, and the start/end frame.

- All eleven cases and the repeated frame clean: combined X/Y/A motion passes
  this discriminator; proceed to a production wave layer.
- Parked controls clean but rotating cases distorted: residual A mechanics,
  torque loss, compliance, or backlash is more likely than compensation.
- Only compensated members of pairs 3/4, 5/6, 7/8, or 9/10 distorted:
  compensation-induced planner dynamics or feed selection remains in scope.
- One feed overlay separates from the other two: the failure is rate or dynamic
  torque dependent, not a static compensation offset.
- Normal sweep clean but reverse sweep distorted: direction-dependent backlash,
  belt wind-up, or A coupling.
- Horizontal clean but Y-dominant distorted: inspect the repaired Y carriage and
  drag-chain path before changing compensation.
- Mid-radius clean but inner cases distorted: inspect radius-dependent A feed,
  bed-centre error, and runout.
- Initial/return witness pairs separate: rotating pen-up travel lost position.
- Final frame differs from the initial frame: cumulative position was lost
  somewhere in the matrix.
- Forward/reverse traces separate while witnesses agree: transient following
  error recovered by the end of each stroke.
- Case 11 differs from case 4: the mechanism is intermittent or dependent on
  accumulated machine state.

Do not change `$701`, acceleration, or other controller settings during this
baseline run. Changing multiple variables would destroy the comparison.
