# M-06 compensated XY/A tracking test plan

**Date:** 2026-10-25

## Purpose

Determine whether the remaining pen/bed tracking error is caused by bed
compensation, controller mixed X/Y/A dynamics, or residual A-axis mechanics.
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
letter/A4 paper and one black 0.8 mm Pigma Micron. It contains a top-to-bottom
matrix with identical bed-space shape and A schedule:

1. XY-only A-parked control at `F700`.
2. Rotating uncompensated at `F700`.
3. Rotating compensated at `F700`.
4. Rotating uncompensated at `F350`.
5. Rotating compensated at `F350`.

Each case draws an A0 witness cross, makes a simultaneous rotating pen-up move,
draws a sine path forward and back over itself with the bed rotating from
-14.5 to +14.5 degrees and back, makes the reverse rotating pen-up move to A0,
then draws the same witness cross again.

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
moves: 1560 drawing, 14 travel
largest bed rotation inside one drawing block: 0.19 deg (cap 15.0)
largest demanded A rate: 54 motor deg/s (limit 500)
pen-up moves carrying rotation: 8 fed, 0 bare G0
worst commanded bed-path bow: 0.001 mm at 72 mm radius
moves exceeding 0.15 mm path tolerance: 0
```

The preflight command reports PASS against the existing bed-step, A-rate, and
bare-rapid guards. Generator output is deterministic; the committed G-code
SHA-256 is
`ED48632808AFBC46FEDE13000B948E5D4006B39ABE5D0F336FE8644AD3C7C203`.

## Accept and interpretation

Photograph the sheet straight down after completion. Inspect each case at the
left witness and along both forward/reverse traces.

- All five cases clean: compensation and combined X/Y/A motion pass this
  discriminator; proceed to the production wave print.
- Case 1 clean, cases 2-5 similarly distorted: suspect residual A drivetrain
  mechanics, torque loss, belt compliance, or backlash.
- Cases 2 and 4 clean, cases 3 and 5 distorted: compensation directly changes
  the failure; stop and revise compensation feed/subdivision planning.
- `F700` cases distorted and `F350` cases clean: motion is dynamic or
  torque-limited; do not treat compensation geometry alone as the cause.
- Initial/return witness pairs separate: rotating pen-up travel lost position.
- Forward and reverse traces separate while the witness pairs agree: transient
  following error recovered at the end of the stroke.

Do not change `$701` or other controller settings during this baseline run.
Changing multiple variables would destroy the comparison.
