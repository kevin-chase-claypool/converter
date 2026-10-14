---
id: WSW-20261013-015
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_xy_scale_check.py
  - samples/gcode/xy-scale-check.gcode
tags:
  - xy
  - scale
  - steps-per-mm
  - squareness
  - diagnostic
related:
  - WSW-20261013-014
  - WSW-20261013-013
---

# X/Y machine-scale check sheet

## Summary

New generator `tools/make_xy_scale_check.py` and sample
`samples/gcode/xy-scale-check.gcode`: a 200 mm ruler along machine X (marks
every 50 mm), the same ruler along machine Y, and a 120 mm square in the
+X/+Y quadrant, all drawn with the bed parked (the program contains no A
words). A steel rule over the drawn intervals measures the X and Y
steps-per-mm directly; the square's diagonals check axis squareness. The
sheet needs a sheet at least 205 x 205 mm (8.5 x 11 in portrait fits,
centred on the registered bed centre).

## Reason

The centre-test bench result (control tick clean, eight-angle tick bundle
displaced) matches a 2.46 mm registration-centre offset, but a G54 origin
correction did not remove the bundle. An error that grows with commanded
position - not one that stays constant - is what remains: if `$100`/`$101`
steps-per-mm are wrong, the pen's fitted frame scales differently in X and
Y, and features drawn at different bed angles land displaced by different
amounts while fixed-bed and single-station diagnostics stay clean. No
existing sample measures commanded millimetres against real millimetres, so
this sheet does, with no electronics and no rewiring.

## Implementation

- `tools/make_xy_scale_check.py` emits the standard converter preamble
  (`G21/G90/G94/G17/G54`, `M5` + `G65 P115 Q0`) and postamble, uses the
  `M3`/`M5` + `G65 P115 Q1` handshakes, and never emits an A word, so the
  bed holds its angle throughout.
- X ruler: stroke from (-100, -80) to (+100, -80) with end bars (+-12 mm)
  and ticks every 50 mm (+-8 mm). Y ruler: the same at X = -80. Square:
  120 mm, upper-right corner on (+100, +100), side 120.000 mm and
  diagonals 169.706 mm expected.
- Self-checks: balanced parentheses on every line, no A word in any motion
  line (macro arguments excluded), all motion inside a 165 mm radius, and a
  report of drawing length, pen cycles, and maximum radius.
- Reading the sheet: an interval long or short by the same fraction
  everywhere means steps-per-mm is off by that fraction - new
  steps/mm = old x drawn / commanded, applied per axis (`$100` X, `$101`
  Y). Unequal square diagonals mean skew or a scale difference between the
  axes and point at the step-scale numbers instead.

## Verification

- Generator run: 117 lines, 1072 mm of drawing, 13 pen cycles, ~3.4 min at
  F350; maximum commanded radius 141.4 mm (inside the 165 mm bench limit);
  expected square diagonal 169.7056 mm.
- `tools/check_gcode_motion.py samples/gcode/xy-scale-check.gcode --strict`
  passes (no A words, so no bed rotation is commanded).
- Bench measurement pending: plot the sheet, measure every 50 mm interval
  and the 200 mm end-to-end distance on both rulers plus the square sides
  and diagonals with a steel rule.

## Struggles and rejected approaches

- An earlier layout put the square over the crossing rulers; ticks and the
  square's edges then shared space with the rulers' measurement band. The
  square was moved into the +X/+Y quadrant and the rulers to Y = -80 /
  X = -80 so no element crosses a ruler interval.
- The A-word self-check first tripped on `G65 P115 ... A1 W2` macro
  arguments; the check now ignores `G65` call lines, which carry no axis
  words.

## Risks and follow-up

- 200 x 200 mm of drawing needs the paper centred on the registered origin
  to about +-8 mm on 8.5 x 11 in; regenerate smaller (`--span`) if the
  paper placement cannot hold that.
- If the rulers measure true but the centre-test bundle still spreads,
  scale is excluded and the residual belongs to the rotation centre
  (P100 `axis_center_correction`) rather than to G54.

## Files

- `tools/make_xy_scale_check.py`: generator and self-checks.
- `samples/gcode/xy-scale-check.gcode`: the generated sheet.
- `software/README.md`: listed with the other repeatability programs.
