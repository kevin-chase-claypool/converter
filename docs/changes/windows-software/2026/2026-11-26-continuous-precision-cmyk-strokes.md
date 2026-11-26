---
id: WSW-20261126-003
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - precision-screen
  - pen-down
  - path-chaining
  - continuous
  - toolpath-efficiency
  - physical-validation-pending
related:
  - WSW-20261126-002
  - WSW-20261123-011
---

# Chain precision CMYK cells into continuous strokes

## Summary

The Precision process screen now joins adjacent selected CMYK cell marks into
longer polylines before X/Y/A planning. Its recipe uses a local connector
radius of about three resolved process cells instead of the previous `1.0 mm`
limit. On the controlled Golden Sunset portrait, the final four programs fall
from `19,703` M3 sequences to `2,522`, an `87.2 %` reduction in pen cycles.

## Reason

The process screen chose each C/M/Y/K cell independently and emitted a short
three-point mark for every selected cell. The generic **Keep pen down** pass
did not pre-chain those marks because they were tagged `ScreenTrail` objects,
which the general contour joiner deliberately preserves. Only the later
post-planner pass could join them, and a `1.0 mm` limit left much of the plate
as isolated dashes. On the installed toolhead, each remaining M3/M5 cycle is
far more expensive than the additional short connector ink, so print time was
dominated by fragmented paths rather than drawing distance.

## Implementation

- Precision-process marks are converted to untagged chain input immediately
  before the normal pre-planner **Keep pen down** pass. The result is wrapped
  back into `ScreenTrail` objects so ink preview and post-planner chaining keep
  their existing contract. Wave, TSP, and other tagged paths remain untouched.
- The precision recipe derives its chain gap from the resolved process pitch,
  targeting three cell widths and rounding to the control's `0.5 mm` step.
  At the controlled `0.98 mm` cell pitch this is `3.0 mm`; a different pen or
  artwork scale changes the gap proportionally.
- New artwork sidecars record the process continuity ratio. A precision recipe
  saved before this field existed migrates its previous fixed `1.0 mm` limit
  once, so reopening the operator's current image does not silently retain the
  fragmented behavior.
- The selected CMYK cell subsets, tone-centroid positioning, structure-tensor
  orientation, Black keyline policy, page clipping, and mark cap are unchanged.
  Connectors add visible ink, which is the deliberate speed-versus-density
  tradeoff exposed by the existing **Keep pen down** gap control.

## Verification

- `software.tests.test_cmyk_tab`,
  `software.tests.test_cmyk_screen_styles`, and
  `software.tests.test_cmyk_contract` passed `89` tests.
- The complete focused CMYK/exporter set passed `179` tests. Complete converter
  discovery passed `757` tests in `175.211 s` with one expected
  OpenGL-context skip; Python compilation passed.
- A focused headless export of the Golden Sunset source at `250 mm`,
  `0.90 mm` pen, `0.35 mm` requested pitch (`0.987654 mm` resolved), seed `7`,
  and the precision recipe produced complete transactional Y/M/C/K programs.
- The pre-planner chain reduced the raw plate marks from
  `13,071 / 23,285 / 26,242 / 12,406` for C/M/Y/K to
  `738 / 707 / 656 / 840` chains. Exact G-code emitted
  `637 / 600 / 548 / 737` M3 sequences respectively, `2,522` total.
  The prior checked-in precision set emitted `4,275 / 5,347 / 5,231 / 4,850`,
  `19,703` total.
- The regenerated comparison preview retains the three faces, eyes, glasses,
  smiles, foreground clothing, and tree/lantern structure while showing
  continuous linework rather than isolated cell dashes.
- `tools/check_gcode_motion.py --strict` passed all four programs. The largest
  drawing-step rotation was `6.80 deg` against the `15 deg` cap, the largest A
  demand was `280 motor deg/s` against `500`, and no bare rotating `G0` was
  present. The strict checker still reports a small number of subdivision-cap
  tolerance cases inherited from the existing planner; it returns PASS.
- The probe artifacts were written to a temporary directory and are not
  checked in. Physical paper remains unavailable.

## Struggles and rejected approaches

A `1.0 mm` chain remained visibly dotted and reduced the controlled set only
to about `8,737` M3 sequences. Extending the gap to five or more cell widths
fell below `2,000` chains in the render probe, but doubled or nearly tripled
the raw plate ink length through long connectors. Three cells keeps the joins
local to the screen while removing most isolated marks.

A separate Continuous row style already offers the absolute fewest pen cycles,
but it replaces the structure-oriented cell layout and changes the visual
language. Retaining the precision screen and making its existing Keep pen down
option work before planning preserves the operator's selected colour workflow.

## Risks and follow-up

The added bridge ink is real and changes local density, especially in bright
areas with sparse cell selection. A lower chain gap restores a finer screen;
a larger gap saves more time. The next physical gate is a registered four-pass
sheet comparing this `3.0 mm` result with the prior precision set for hue,
density, facial detail, drag, and elapsed time. The rendered comparison is
software evidence only.

## Files

- `software/generator_tabs/cmyk_tab.py`: process-specific pre-planner chaining,
  pitch-derived recipe gap, and operator-facing descriptions.
- `software/tests/test_cmyk_tab.py`: pre-planner process chaining regression and
  recipe expectation.
- `software/README.md`: current process-screen continuity behavior and
  connector tradeoff.
