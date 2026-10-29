---
id: WSW-20261029-003
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_bed_error_calibration.py
  - software/tests/test_bed_compensation.py
  - samples/gcode/bed-error-map-dense-91-v3-auto.gcode
  - samples/gcode/bed-error-map-dense-91-v3-auto.csv
tags:
  - bed-calibration
  - dense-mesh
  - pass-control
  - unattended
  - drying-dwell
related:
  - WSW-20261029-002
---

# Run bed calibration passes with timed dwells

## Summary

The calibration generator can now replace its eight manual `M0` pass stops
with timed `G4` dwells. A separate five-second v3 program starts once and runs
through all nine passes without requiring another Cycle Start.

## Reason

The operator reports that the installed pen dries immediately. Requiring nine
Cycle Start activations therefore adds interaction without helping the ink.
A short automatic dwell still gives the controller time to settle at A=0 while
keeping the calibration available as a single run.

## Implementation

`tools/make_bed_error_calibration.py` adds
`--pass-dwell-seconds SECONDS`.

- Omitting the option preserves the existing manual `M0` programs.
- A positive value emits `G4 P<seconds>` between passes and identifies the
  timed mode in the G-code header.
- Zero emits continuous pass changes with no dwell.
- Automatic output uses an `-auto` filename suffix so it cannot overwrite the
  operator-confirmed variant.
- The generator returns to A=0 and completes the normal pen-clear handshake
  before every dwell.

The five-second dense sheet is
`samples/gcode/bed-error-map-dense-91-v3-auto.gcode`.

## Verification

- The manual v3 program still contains eight `M0` pauses.
- The automatic v3 program contains zero `M0` commands and eight
  `G4 P5 (automatic pass dwell; ... next)` commands.
- Negative, infinite, and NaN dwell values are rejected.
- The committed automatic G-code and CSV match the generator output exactly.
- All `63` focused bed tests and all `570` converter tests pass with one
  expected OpenGL-context skip.
- Macro parsing and strict motion checks pass with 2,336 drawing moves, 1,069
  travel moves, no bare rotating `G0`, and the same motion bounds as the manual
  program.
- Automatic G-code SHA-256:
  `421CAAC9AF15B67B2FB9B313B2D11521EFF738124CA8BB9716D43199DA97C13E`.
  Its 823-row CSV is byte-identical to the manual v3 CSV.

## Struggles and rejected approaches

- Removing all dwells would be mechanically valid, but retaining five seconds
  gives the toolhead and bed a clear settling boundary between passes at
  negligible cost.
- Making timed operation the default would remove the existing opportunity to
  stop for a lifted sheet, bubble, or toolhead fault.
- Reusing the manual filename would make it too easy to start an unattended
  print without noticing that its stop behavior changed.

## Risks and follow-up

No physical v3 auto run has completed yet. Watch the first run to confirm the
paper remains secured and no wet-ink transfer appears. The five-second value is
operational, not a substitute for aborting if the sheet moves or the pen stops
marking correctly.

The auto variant changes only pass timing. It does not alter station geometry,
measurement rows, G54 registration, or the requirement to run `G65 P113`
first.

## Files

- `tools/make_bed_error_calibration.py`: configurable automatic pass dwell and
  filename selection.
- `software/tests/test_bed_compensation.py`: timed-pass, validation, and
  committed-sample regressions.
- `samples/gcode/bed-error-map-dense-91-v3-auto.gcode` and `.csv`: one-start
  five-second-dwell calibration sheet.
- `software/README.md`, `docs/testing/TEST_PLAN.md`, and
  `docs/project/ROADMAP.md`: operating instructions and current status.
