---
id: WSW-20261125-011
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/structure_tensor.py
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_workflow.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_edge_flow.py
  - software/tests/test_cmyk_photo_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
  - docs/integration/INTERFACES.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - coherent-color-flow
  - shadow-layers
  - color-continuity
  - keylines
  - tone-bridge
  - chaining
  - manifest
related:
  - WSW-20261125-004
  - WSW-20261125-005
  - WSW-20261125-010
---

# Expose coherent CMYK flow and coverage controls

## Summary

The coherent CMYK workflow now exposes the parameters that previously lived
inside its renderer: first/final shadow-layer depths, ink-plane smoothing
distance, secondary-ink mix ratio, Black-keyline color separation, and the
same-streamline tone-gap bridge. These controls are separate from base pitch,
per-ink separation weights, adjacent contour chaining, and the rest of the
screen recipe.

Set manifests move to version 7 with the complete values. Artwork recipes
restore the new fields and use backward-compatible defaults when older recipes
do not contain them.

## Reason

The adaptive-flow development contract requires geometric density, per-ink
coverage, color continuity, Black keyline behavior, shadow-layer thresholds,
tone-gap bridging, and adjacent chaining to be independently controllable.
Previously the coherent renderer held the `40/90 %` scene-depth boundaries,
`6 mm` ink-plane window, `72 %` secondary-ink ratio, `25 %` color separation,
and `4 mm` local bridge as constants or coupled values.

## Implementation

- **First shadow layer** and **Final shadow layer** set the first extra and
  final coherent scene-depth thresholds. The UI normalizes them into ascending
  order, and layer zero always remains the base network.
- **Ink-plane hold** sets the arc-length smoothing window for contiguous local
  CMYK assignments. **Secondary ink mix** sets how close a second channel must
  be to the dominant coverage before it remains on the same path.
- **Colour edge separation** exposes the C/M/Y coverage reduction beside
  Black keylines. It is active only when keylines are enabled.
- **Tone-gap bridge** controls retracing through a local coverage gap on one
  already traced streamline. It is independent of **Pen-down chain**, which
  joins adjacent contour endpoints and decides whether a visible connector is
  faster than lift/travel/lower.
- `trace_shared_structure_streamlines()` accepts explicit dark-layer start/end
  values and clamps malformed input into a valid ascending interval. Both the
  coherent and stochastic shared CMYK entry points forward them.
- Recommended coherent defaults remain `40/90 %` shadows, `6 mm` hold,
  `72 %` secondary mix, `25 %` edge separation, and a `4 mm` same-path bridge.
  Comparison recipes set their own bridge value so prior per-ink/shared
  topology is not silently changed.
- The layer cache key now includes keylines and every exposed control. Version-7
  manifests record the values, and the stage dependency contracts list them.

## Verification

- Focused CMYK/workflow tests pass `112` tests.
- The broader CMYK/workflow/generator subset passes `225` tests in `37.861 s`
  with one expected OpenGL-context skip.
- Complete converter discovery passes `738` tests in `137.598 s` with that
  same expected skip.
- Regressions confirm each UI control reaches the coherent renderer with the
  selected value, changing them invalidates the cache, sidecar recipes restore
  them, and shadow thresholds cannot invert.
- No physical plot was generated. The values remain software-selected and
  unvalidated on paper.

## Struggles and rejected approaches

Applying the new shadow thresholds to the legacy per-ink network would have
changed existing comparison output because that renderer uses a different
historical threshold ladder. The shadow controls are therefore enabled and
recorded for coherent/shared scene-depth modes, where those constants were
actually owned. Reusing the adjacent chain gap as the tone bridge was rejected
because the two behaviors solve different geometry problems and have different
wear/visibility risks.

## Risks and follow-up

The exposed controls can produce visible overprint, long same-path connectors,
or dramatic density changes. Validation warns about a near-100 % secondary mix,
but the selected defaults are not paper-qualified. Black keyline confidence
thresholds remain internal constants; only the keyline toggle and color
separation are exposed in this milestone.

Four-pass paper evidence is still required to select final shadow, continuity,
edge-separation, and bridge values.

## Files

- `software/converter_core/structure_tensor.py`: parameterized shadow layers.
- `software/converter_core/cmyk.py`: coherent/shared forwarding contracts.
- `software/generator_tabs/cmyk_tab.py`: controls, cache key, sidecar, renderer
  arguments, validation, and manifest version 7.
- `software/generator_tabs/cmyk_workflow.py`: stage descriptions and dependency
  contracts.
- `software/tests/test_cmyk_edge_flow.py`,
  `test_cmyk_photo_tab.py`, `test_cmyk_tab.py`: forwarding, cache,
  persistence, normalization, and manifest regressions.
- `software/README.md`: operator behavior and current defaults.
- `docs/integration/INTERFACES.md`: version-7 set-manifest contract.
- `docs/project/ROADMAP.md`: current coverage-control status.
