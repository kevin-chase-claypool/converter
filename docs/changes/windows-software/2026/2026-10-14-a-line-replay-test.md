---
id: WSW-20261014-001
date: 2026-10-14
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_a_line_replay_test.py
  - samples/gcode/a-line-replay-test.gcode
tags:
  - a-axis
  - bed
  - tilt
  - replay
  - registration
  - diagnostic
related:
  - WSW-20261013-014
  - HW-20261011-001
---

# Bed-angle line-replay test: origin line as the constant, quadrant replays against it

## Summary

New generator `tools/make_a_line_replay_test.py` and sample
`samples/gcode/a-line-replay-test.gcode`: one **origin line** is drawn at
A=0 - the reference, like the screw left alone in a 3D-printer bed-tilt
adjustment - and the same bed-frame line is replayed at the quadrant bed
angles (default 90/180/270), with two A=0 control passes and a closing A=0
pass after the highest angle. Every replay must land exactly on the origin:
a constant parallel gap is that quadrant's offset (translation error), and a
fan opening at the ends is a rotation error - 0.5 deg of rotation spreads the
ends of a 60 mm half-line by 0.52 mm.

Lines are identified by a stepped end-length code: origin 140 mm total,
closing 128, controls 120, then the replays 112/104/96 for 90/180/270 deg -
each replay 8 mm shorter in total length than the previous, so a caliper
across a line's ends attributes it without any extra marks. Draw with the
finest pen available (a 0.15 mm Pigma Micron 003 makes ~0.2 mm offsets
readable under a loupe or a close-up photo).

## Reason

Operator request after the 2026-10-13/14 centre-test session left a displaced
tick bundle: "you could create a test for me that uses an origin line then
marks a series of angles against it. i could use my finest pigma micron 003
for this test ... it works the same way in bed tilt on 3d printers. one point
is set as the constant against which each of the other 3 quadrants are
measured."

Ink cannot read bed height on this machine - the toolhead's force loop holds
contact force constant, so the mark looks the same whatever the gap. What the
marks can read is the XY offset per bed angle, which is the observable that
the tick ring already exposed; a full-length line separates a pure
translation (parallel gap) from a rotation (end fan), which a single tick
cannot do.

## Implementation

- Draw order: origin (A=0), `--control-passes` A=0 replays (default 2, they
  must coincide with the origin or repeatability is the story), one replay per
  angle in `--angles` (default quadrant angles 90/180/270, each 8 mm shorter
  in total length than the previous), then the closing A=0 pass (8 mm longer
  than the controls), which also exercises the A reversal.
- Rotation mapping is identical to the centre test: machine position is the
  paper-frame point rotated by the bed angle, and A is the bed angle times
  the measured 12.03324 ratio.
- Options: `--half-length`, `--replay-half-length`, `--angles`,
  `--control-passes`, `--replay-step` (0 disables the length stepping),
  `--closing` / `--no-closing`, `--line-angle`, `--feed` (default F350). A
  finer shape read is one flag away:
  `--angles 45,90,135,180,225,270,315`; a single replay can be re-run for
  identification with e.g. `--angles 90`.
- The M3/M5 stations use the same `G65 P115` handshakes as the centre test,
  and the trailer runs the proven full-retract and park sequence.

## Verification

- Generator self-checks pass: 7 passes (origin 1, control 2, replays 3,
  closing 1), 68 lines, balanced parentheses, A range 0..3248.97 motor deg,
  maximum commanded radius 70 mm; the length code prints as origin 140,
  control 120, replays 112/104/96, closing 128.
- `python tools\check_gcode_motion.py samples\gcode\a-line-replay-test.gcode`
  reports 0.00 deg of bed rotation inside any drawing move and 4 pen-up
  repositions carrying A as bare `G0` rapids - by design and the same motion
  pattern as `a-center-test.gcode`; that guard tool targets print files, not
  diagnostic replays.
- **Pending:** the bench run. It needs HOME + registration first, so G54 X0
  Y0 is the physical bed centre.

## Struggles and rejected approaches

- Rejected making the mark itself height-sensitive. The force loop normalises
  ink against bed height, so a marking test can only carry XY information;
  height stays with the probe (`bed_mesh_probe.py`) or a dial indicator.
- The first revision only made the origin longest and left the replays
  identical; the operator asked how a caliper reading attributes a line to a
  quadrant. The replays now carry the stepped end-length code (8 mm total per
  step) and the closing pass is 8 mm longer than the controls, so even the
  reference band is attributable.
- Labelling ticks attached to each line were reconsidered and rejected: the
  length code adds no ink inside the measurement band and cannot drift out of
  step with the line it labels. A single angle can still be replayed alone
  (`--angles 90`).

## Risks and follow-up

- The per-angle offsets mix the registration-centre translation with the
  height-coupling (runout) term until they are decomposed; the polar probe
  (`tools/bed_mesh_probe.py --mode polar`) is the measurement that separates
  them.
- Keep the pen's M5 clearance above the bed's height variation during the
  pen-up indexing moves, as with the other A tests.
- Acceptance: tilt the rail ends until every replay collapses onto the
  origin; if a residual remains, it belongs to the disc-warp/bearing-runout
  fork recorded in `HW-20261011-001`.

## Files

- `tools/make_a_line_replay_test.py`: the generator.
- `samples/gcode/a-line-replay-test.gcode`: the generated test program.
- `software/README.md`: listed with the other machine-measurement programs.
