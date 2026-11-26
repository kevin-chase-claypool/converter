---
id: WSW-20261125-012
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/structure_tensor.py
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/cmyk_workflow.py
  - software/tests/test_cmyk_edge_flow.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
  - docs/integration/INTERFACES.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - process-color
  - error-diffusion
  - structure-tensor
  - fine-detail
  - mark-limit
  - geometry
  - manifest
related:
  - WSW-20261125-004
  - WSW-20261125-007
  - WSW-20261125-008
  - WSW-20261125-011
---

# Stabilize the precision process-color screen

## Summary

The CMYK tuner now exposes a **Precision process screen (fine CMYK cells)**
recipe. It divides the placed page into pen-footprint cells, error-diffuses each
calibrated C/M/Y/K plate into a binary ink subset, and draws short
structure-oriented marks for that subset. Sparse highlights retain their
requested average plate coverage, all marks remain inside the artwork page, and
the configured per-ink mark cap is honored by growing the cell pitch.

Set manifests move to version 8 and record the process-cell pitch and Black edge
threshold when this style is selected.

## Reason

The uncommitted renderer slice selected one of the 16 whole-cell process-ink
subsets by nearest RGB palette colour. That method quantized a uniform `15 %`
single-ink target to the empty subset on every tested cell: the requested light
tint disappeared because the target was closer to paper than to full ink.
Short angled edge marks also extended outside the page; a pure Cyan
`50 %` probe ranged from `-0.0366 mm` to `40.0366 mm` on a nominal
`0-40 mm` page, and Yellow reached `-0.0556 mm` to `40.0556 mm`.

Those failures violate the slice's two requirements: preserve color coverage
and emit bounded geometry.

## Implementation

- `_coverage_masks()` error-diffuses each C/M/Y/K field independently with a
  deterministic channel-specific serpentine phase and seeded sub-pen
  threshold jitter. The selected bits form one process-ink subset per cell.
  This preserves each plate's requested long-run coverage instead of forcing
  the whole RGB target through a nearest-colour palette threshold, while
  avoiding identical or complementary one-pixel lattices between plates.
- The error is propagated one pixel at a time. A row-vectorized prototype was
  rejected because errors created earlier in the same scan row did not reach
  later pixels; it still left the `15 %` case blank.
- Each selected ink draws one three-point mark through the cell centre. The
  shared structure-tensor tangent and confidence come from
  `structure_tensor_fields()`, with the channel angle as fallback. Strong Black
  keylines raise K coverage through the configured edge threshold.
- Every mark endpoint is clipped to the page rectangle. If any plate exceeds
  `max_marks`, the renderer recursively grows the cell pitch rather than
  dropping the excess marks.
- The search flow styles use a `1.10` pen-width pitch floor. The CMYK stage
  validation reports the same floor instead of the prior `0.9` value.
- Auto now treats the precision process screen like the other flow-guided
  styles for exposure control, and its process-area coverage estimate uses the
  calibrated plate fields directly rather than multiplying them by a
  pen/pitch factor that would understate the binary cell screen.
- The **Max marks/ink** spin box now reaches the recipe's requested `800000`
  instead of clamping at `200000`. Its path tolerance is `0.05 mm`, the existing
  control's minimum step, rather than the unreachable `0.04 mm` initially
  listed in the recipe.
- The workflow stage is now labelled **Screen geometry and spacing** so it
  honestly covers both streamline tracing and pen-footprint process cells.

## Verification

- `python -m unittest -q software.tests.test_cmyk_tab software.tests.test_cmyk_edge_flow`
  passed `104` tests.
- The focused CMYK suite passed `170` tests in `29.163 s`.
- Complete converter discovery passed `747` tests in `137.462 s` with one
  expected OpenGL-context skip.
- `python -m py_compile` passed for all six changed Python files.
- Determinism compares every emitted coordinate, not only mark counts.
- A `40 x 40 mm`, `1.0 mm` cell probe now keeps pure-channel tilted edge marks
  within `[0, 40]` in both axes, including the sub-pen offsets from `3x`
  overdraw.
- Uniform plate targets `C 15 % / M 35 % / Y 55 % / K 25 %` render at
  `14.44 % / 34.56 % / 55.00 % / 24.75 %`, all inside the `2` percentage-point
  regression tolerance.
- A `0.25 mm` dense request capped at `100` marks per ink grows to a `94`-mark
  maximum rather than truncating any plate.
- A three-ink `50 %` plate mixture reproduces the continuous multiply-model
  mean RGB within `1.56/255` in the worst channel. Exact shared or complementary
  binary lattices exceeded `25/255` before deterministic channel jitter.
- A zero-tone step edge produces no marks with keylines off and Black-only
  structure marks with keylines on; no Cyan, Magenta, or Yellow phantom ink is
  introduced.
- A `250 x 250 mm` synthetic page at `0.35` pre-scale pitch completed in
  `4.307 s` with all emitted coordinates within the page bounds.
- No paper contact sheet was created or inspected. The checks are numeric and
  widget/route regressions only.

## Struggles and rejected approaches

The first palette implementation looked like conventional Floyd-Steinberg code
but processed a full scan row with NumPy before accumulating the horizontal
errors. The original light-tone loss was therefore compounded by a diffusion
bug. Replacing the 16-colour nearest-colour choice with independent plate
coverage exposed that bug immediately; changing the loop to strict per-pixel
order fixed it.

The first bounds regression used only one seed of a K-dominant gradient and
never activated Cyan or Yellow at the page corners. Replacing it with isolated
C/M/Y/K fields made the edge failure reproducible.

## Risks and follow-up

The new diffusion changes local overlap from a jointly selected RGB palette to
independently screened process plates. Its long-run channel coverage is now
bounded and testable, but visible overprint texture and four-pass color on paper
remain unvalidated. The fixed `0.35` recipe pitch is pre-scale; the renderer
raises it to the `1.10` pen-width floor after the artwork scale is applied.

The next bounded task is a four-pass paper contact comparing the precision
process recipe with coherent color flow at identical placement, pen order,
image controls, and registration. Record hue/density, light-tint survival,
keyline continuity, connector visibility, and elapsed time before promoting or
tuning the recipe.

## Files

- `software/converter_core/cmyk.py`: process-cell renderer, plate diffusion,
  orientation, page clipping, mark cap, and coherent-flow forwarding.
- `software/converter_core/structure_tensor.py`: shared tensor-field sampling
  entry point and `1.10` pen-width flow floor.
- `software/generator_tabs/cmyk_tab.py`: process style, recipe controls,
  renderer dispatch, validation floor, and version-8 manifest fields.
- `software/generator_tabs/cmyk_workflow.py`: geometry-stage contract and
  precision process recipe entry.
- `software/tests/test_cmyk_edge_flow.py`: deterministic coordinate,
  edge-bound, coverage, and mark-cap regressions.
- `software/tests/test_cmyk_tab.py`: scaled process dispatch and manifest
  version coverage.
- `software/README.md`: operator behavior, defaults, pitch floor, and version-8
  manifest description.
- `docs/integration/INTERFACES.md`: version-8 publication contract.
- `docs/project/ROADMAP.md`: current precision-screen status and next physical
  comparison.
