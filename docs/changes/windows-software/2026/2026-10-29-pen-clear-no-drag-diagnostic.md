---
id: WSW-20261029-005
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/make_pen_clear_test.py
  - software/tests/test_pen_clear_test.py
  - samples/gcode/pen-clear-no-drag-30.gcode
tags:
  - toolhead
  - pen-clear
  - M5
  - T-01H
  - drag
  - diagnostic
related:
  - RPSW-20261023-001
  - WSW-20261029-004
---

# Add a one-start pen-clear no-drag diagnostic

## Summary

Added a compact 30-cycle `M3`/`M5` diagnostic that draws isolated witness
strokes on ordinary paper and jogs the pen up between them at three travel
speeds. It requires one initial Cycle Start and produces visible connector
lines wherever normal `M5` fails to clear.

## Reason

The corrected dense v3 sheet has one visually confirmed pen-up drag even
though the operator confirmed that the deployed toolhead is the 130 ms
clearance build. The existing T-01H procedure is manual and difficult to
repeat consistently. A compact one-page program separates intermittent clear
failure from paper, crossing, and full-sheet calibration effects.

## Implementation

`tools/make_pen_clear_test.py` generates
`samples/gcode/pen-clear-no-drag-30.gcode`.

- Thirty isolated 6 mm witness strokes are arranged in a 5 x 6 serpentine
  grid inside about 140 x 200 mm.
- Each stroke uses the normal `M3` force seek and `M5` clear plus the configured
  `P115` acknowledgement.
- The 30 pen-up jogs are split into ten at `F300`, ten at `F1000`, and ten at
  `F3000`.
- The program has no `M0` stops and finishes with the normal full retract and
  off-bed park.
- A small header asks the operator to inspect every connector and to run
  `G65 P113` before starting.

## Verification

- Unit coverage verifies 30 `M3`, 30 witness strokes, 30 pen-up travels, no
  `M0`, and ten jogs at each feed.
- The committed sample matches the generator byte-for-byte.
- Macro parsing passes.
- Strict motion checks pass with 30 drawing moves, 30 travel moves, and no
  rotating `G0`.
- The full converter suite passes all `575` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- Using a single center mark repeatedly would not reveal the direction or speed
  dependence of an intermittent drag.
- Running another full 14-inch calibration sheet would consume scarce stock
  without isolating the physical cause.
- Increasing the 130 ms clearance pulse again without a repeatable failure
  signal would change the machine without evidence.

## Risks and follow-up

No physical result exists yet. Run the program on ordinary paper at the normal
plotting height with the same 005 pen. If connectors appear, record their feed
group and inspect the toolhead `p` status immediately after `M5`. If no drag
appears in 30 cycles, repeat once before attributing the original mark to the
toolhead rather than a local paper or ink artifact.

## Files

- `tools/make_pen_clear_test.py`: diagnostic generator.
- `software/tests/test_pen_clear_test.py`: program and sample regressions.
- `samples/gcode/pen-clear-no-drag-30.gcode`: one-start physical test.
- `software/README.md` and `docs/testing/TEST_PLAN.md`: operating procedure.
