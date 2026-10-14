---
id: WSW-20261014-003
date: 2026-10-14
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_a_tilt_pairs_test.py
  - samples/gcode/a-tilt-pairs-test.gcode
tags:
  - bed
  - tilt
  - a-axis
  - diagnostic
  - calibration
related:
  - WSW-20261014-001
  - HW-20261011-001
---

# Bed-tilt quadrant pair test: four labeled A=0-versus-angle line pairs

## Summary

New generator `tools/make_a_tilt_pairs_test.py` and sample
`samples/gcode/a-tilt-pairs-test.gcode`. Four pairs of lines are drawn at
separated spots on the sheet already on the bed - SW, SE, NE, NW. Each pair
is the same 66 mm paper segment drawn twice: the constant pass at A = 0
(drawn 80 mm long) and the test pass with the bed indexed to that pair's
angle (drawn 66 mm long). A zigzag label above each pair counts the angle:
1 tooth = control (A0 twice), 2 = 90, 3 = 180, 4 = 270 deg.

Inside a pair the longer line is always the constant. A perpendicular gap
between the two lines is that quadrant's offset, unequal gaps at the two
ends indicate rotation (fan), and the end overhangs read the along-line
component. The control pair is the "constant quadrant" of the 3D-printer
tilt workflow; the other three are measured against it.

## Reason

Operator request: "i want to do a drawing test ... like a bed tilt
calculation where one of the quadrants is the constant while the other 3 get
measured ... make it very clear which lines go together. i will measure
their offset using calipers." The earlier single-station replay test put
every pass on one line, which made caliper attribution hard; separate,
labeled pairs give one clean measurement per quadrant.

## Implementation

- Pairs at (-50,-50), (50,-50), (50,50), (-50,50); lines along X; constant
  half length 40 mm, test half length 33 mm; a one-stroke zigzag label sits
  8-12 mm above each pair with 5 mm tooth spacing.
- Test passes use the same rotation mapping as the other A tests: the machine
  position is the paper point rotated by the bed angle, and A is the angle
  times 12.03324.
- The same `G65 P115` handshakes, pen-up moves between strokes, and the
  proven full-retract + park trailer.
- The layout spans about +-90 mm in X and +-62 mm in Y, fits the sheet on
  the bed, and clears the earlier test's ink at y = 0.
- `--station-shift-y` (and `--station-rot`) move the station rows so a
  re-run after an adjustment lands on clean paper on a used sheet; the
  committed sample is generated with `--station-shift-y -25` (fresh rows at
  y = +25 / -75) for the confirmation run.

## Verification

- Generator self-checks pass: 12 strokes (4 pairs x label/constant/test),
  A values 0/90/180/270, balanced parentheses, max commanded radius
  110.1 mm.
- `python tools\docs_index.py --write` / `--check` - indexes valid.
- **First bench run (2026-10-14):** on the freshly registered sheet (new P100
  Y 0.3, park magnet-verified) the control pair printed on top of itself
  (<=0.15 mm); 90 deg ~0.6-0.7 mm lens-shaped; 180 deg ~1.0-1.2 mm with a
  slight taper; 270 deg ~0.3-0.6 mm opening to ~0.8-1.1 mm. The ladder
  ratio repeats the pre-fix frame values, but the frame was re-registered
  and magnet-checked and every non-control pair tapers along the line - the
  residual matches the bed-height-vs-angle mechanism through the pen
  carriage instead. The operator flipped the sheet and the same layout was
  re-run on the blank side with a new pen: every pair reproduced within
  ~0.05-0.1 mm (control single; 90 deg 0.70-0.80; 180 deg 1.00-1.20;
  270 deg taper ~0.2 to 0.7 mm), so the signature is stable across sheet
  side and pen; see
  `docs/report/lab-notes/2026-10-14-tilt-pairs-first-run.md`.

## Struggles and rejected approaches

- Considered re-using the single-station replay layout with better labels;
  rejected because four angles overlapping at one spot re-creates the
  attribution problem the operator is trying to avoid.
- Rejected extra per-pair marks beyond the tooth count: the count reads at a
  glance and keeps the pairs clean.

## Risks and follow-up

- The measured offset is the bed-height difference coupling through the pen
  carriage (plus any residual mapping term), not a direct Z reading; if the
  pairs never separate even with tilt, the coupling is small and the gauge
  gap-map remains the direct height measurement.
- One adjustment iteration may not be enough; keep the same sheet so the
  before/after pairs compare under identical placement.

## Files

- `tools/make_a_tilt_pairs_test.py`: the generator.
- `samples/gcode/a-tilt-pairs-test.gcode`: the generated test program.
- `software/README.md`: listed with the other machine-measurement programs.
- `docs/project/ENGINEERING_LOG.md`: log entry.
