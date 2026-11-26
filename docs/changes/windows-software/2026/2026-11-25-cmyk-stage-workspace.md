---
id: WSW-20261125-010
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_workflow.py
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/_tab_common.py
  - software/converter_core/structure_tensor.py
  - software/converter_core/__init__.py
  - software/tests/test_cmyk_workflow.py
  - software/tests/test_cmyk_photo_tab.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_edge_flow.py
  - software/README.md
  - software/generator_tabs/README.md
  - docs/integration/INTERFACES.md
  - docs/decisions/ADR-011-cmyk-stage-workspace.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - user-interface
  - workflow
  - stage-navigation
  - structure-tensor
  - diagnostics
  - parameter-locks
  - recipes
  - manifest
related:
  - WSW-20261125-004
  - WSW-20261125-009
  - ADR-011
---

# Add the persistent adaptive CMYK stage workspace

`WSW-20261125-011` later advances the same manifest from version 6 to version 7
to expose coherent flow and coverage controls.

## Summary

CMYK Photo now has a persistent nine-stage workflow rail above the guided card
and advanced tuner. Selecting a stage opens only that stage's settings,
states its input/output/validation/cache contract, supports **Reset stage**,
and can lock the stage against automatic recipe changes. The selected stage
and locks persist in the artwork recipe.

The rail offers four complete comparison recipes. The Direction stage can
render the current multichannel structure tensor as an undirected orientation
field with confidence-coded brightness. Set manifests move to version 6 so
they record each stage's settings hash and lock state.

The simulation preview, renderer algorithms, four-file order, G-code contract,
machine frame, registration, and one-click guided action remain unchanged.

## Reason

The coherent renderer, calibrated separation, adaptive spacing, keylines, and
four-program export existed, but every control occupied one long advanced form
and one monolithic cache key. Operators could not isolate composition, color,
separation, tensor guidance, streamline placement, ink assignment, path order,
motion, or review. Automatic image adjustments also had no way to preserve a
manually chosen parameter group.

## Implementation

- `cmyk_workflow.py` defines nine stages with explicit input, output,
  validation, diagnostic, settings-group, and cache-dependency contracts.
  The same module owns deterministic widget-state capture/restore and the
  stage navigator.
- The former single Screen form is split into Screening, Flow geometry, Ink
  assignment, and Path and continuity groups. Image processing and separation
  are also separate groups. The stage rail filters these existing widgets
  rather than duplicating controls.
- Per-stage reset restores that group's construction defaults and invalidates
  the combined layer/analysis caches.
- Per-stage locks preserve current values around Auto, recommended defaults,
  quick guided defaults, and complete recipe application. Explicit stage reset
  remains available while locked.
- Recipe presets select recommended coherent flow, per-ink Edge-flow,
  stochastic shared flow, or line-screen output.
- `structure_field_diagnostic()` maps the undirected tangent angle to a
  repeating 180-degree hue, guidance confidence to brightness, and keyline
  confidence to a white overlay. The Direction-stage dialog renders this image
  on demand and can be reviewed without replacing the shared physical-print
  preview.
- Stage validation reports missing artwork, invalid usable page area, zero ink
  weights, unsafe effective pitch, excessive overdraw or bridge gaps, motion
  violations, and incomplete output channels when available.
- The artwork sidecar records the selected stage and locked stages. Version-6
  set manifests record current stage, lock list, per-stage settings SHA-256
  hashes, and the available diagnostic modes.

## Verification

- Focused workflow, CMYK Edge-flow, Photo, and full tuner tests pass `108`
  tests.
- The broader CMYK, workflow, and generator-shell subset passes `221` tests in
  `35.323 s` with one expected OpenGL-context skip.
- Complete converter discovery passes `734` tests in `140.782 s` with that
  same expected skip.
- An offscreen render at `430 x 900` confirmed the guided rail and the filtered
  Direction inspector remain usable without horizontal overflow.
- A synthetic color-gradient source produced a 240 x 240 direction/confidence
  PNG with visible curved orientation and high-confidence edge structure.
- The diagnostic reversal regression confirms an eigenvector direction and its
  opposite render the same colour. A flat field is measurably darker than a
  structured field.

## Struggles and rejected approaches

Hiding stage groups before measuring the advanced controls shrank the tool
pane and broke the established wide-controls layout. The pane now retains the
full pre-filter control width. Duplicating controls per stage was rejected
because it would create multiple sources of truth and break recipe persistence.
Materializing separate caches for every stage in this milestone was also
rejected: the current renderer has not yet been split into independently
verifiable intermediate stages, so it would risk changing geometry without a
clear acceptance test.

## Risks and follow-up

The renderer still rebuilds from one combined cache key. Stage hashes make
dependencies explicit and reviewable, but they do not yet prevent re-running
upstream work when only a downstream stage changes. Only Direction has a
dedicated graphical diagnostic; Review uses the existing shared print preview,
and the other stages currently expose textual contract/validation summaries.
The roadmap keeps this larger cache and pipeline split unchecked.

The stage rail and field image are software-verified. No physical four-pass
print was made, so paper density, ink spread, connector visibility, registration,
and final recipe quality remain unverified.

## Files

- `software/generator_tabs/cmyk_workflow.py`: stage contracts, navigation,
  recipes, locks, and widget-state helpers.
- `software/generator_tabs/cmyk_tab.py`: stage-owned groups, filtering,
  validation, persistence, recipe behavior, diagnostic dialog, and manifest v6.
- `software/generator_tabs/_tab_common.py`: group-box registry.
- `software/converter_core/structure_tensor.py`: undirected flow-field image.
- `software/converter_core/__init__.py`: public diagnostic export.
- Tests in `test_cmyk_workflow.py`, `test_cmyk_photo_tab.py`,
  `test_cmyk_tab.py`, and `test_cmyk_edge_flow.py`.
- `software/README.md`, `software/generator_tabs/README.md`,
  `docs/integration/INTERFACES.md`, `docs/project/ROADMAP.md`: current
  behavior and remaining cache work.
- `docs/decisions/ADR-011-cmyk-stage-workspace.md`: stage-rail architecture.
