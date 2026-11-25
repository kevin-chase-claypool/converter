---
id: WSW-20261125-003
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/structure_tensor.py
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/cmyk_sheet.py
  - software/README.md
tags:
  - cmyk
  - edge-flow
  - streamline
  - variable-pitch
  - density
  - portrait
  - physical-validation-pending
related:
  - WSW-20261125-002
  - WSW-20261123-019
---

# Compress Edge-flow pitch continuously in darker tone

## Summary

Edge-flow streamlines now move progressively closer together as their local ink
tone darkens. A new **Shade compression** control scales the base Dot pitch
continuously from the requested spacing in highlights down toward a pen-safe
minimum in shadows. The previous fixed-pitch output remains available at `0 %`.

## Reason

The reference artwork does not merely activate additional whole streamline
layers in dark areas. Its individual lines crowd together through gradients and
shadow planes, producing a continuous change in hatch density. The converter
previously kept every line network at one base pitch and changed density only
through tone gating and whole-layer thresholds.

## Implementation

- Added `_edge_flow_local_pitch`, which maps local ink tone `t` and compression
  `c` to `base_pitch × (1 - c × t)`. The result never exceeds the operator's Dot
  pitch and never falls below `0.9` pen widths.
- The per-ink tracer now seeds parallel neighbours along each accepted
  streamline at its local target pitch. Occupancy cells use the same local
  separation, so dark regions can accept closer lines while light regions retain
  the base spacing.
- The fixed-grid traversal remains in place. At `0 %` compression the old
  candidate order is retained, and the previous fixed-pitch mark counts are
  unchanged.
- The shared experimental network supports the same local compression for
  comparison.
- Added **Shade compression** to the CMYK screen controls, artwork recipe,
  print-set manifest, calibration-sheet manifest, Auto coverage estimate, and
  Fine detail snapshot. The recommended photo recipe uses `60 %`; Fine detail
  uses `65 %`.
- Existing **Flow layers** remain as additional stepped dark-tone networks.
  They complement the continuous pitch change rather than implementing it.

## Verification

- A synthetic tone ramp verifies monotonically decreasing local pitch. The
  darkest result respects the pen-width floor, and compressed dark-field ink
  length is more than `1.25×` the fixed-pitch result.
- On the supplied `IMG_0514.JPG` software render, fixed versus `60 %`
  compression produced:
  - Cyan: `2,912` to `3,542` marks
  - Magenta: `2,932` to `3,502`
  - Yellow: `4,837` to `7,113`
  - Black: `1,931` to `2,157`
- The fixed-pitch counts exactly match the pre-change render, confirming that
  `0 %` preserves the prior output.
- Focused Edge-flow, CMYK-tab, and calibration-sheet modules pass `100` tests.
  CMYK photo processing passes `17` tests.
- Complete converter discovery passes `684` tests with one expected
  OpenGL-context skip in `159.951 s`.
- Visual inspection used `tmp/edge-flow-variants.png`; it is diagnostic output
  and is not a tracked project artifact.

## Struggles and rejected approaches

Using more Flow layers alone was rejected because it changes density in
discrete bands rather than compressing the gaps between adjacent contours.
Changing only the scanning seed interval was also insufficient: for a
horizontal streamline, a denser seed row does not move the neighbouring
parallel line closer. The final implementation seeds neighbours normal to each
traced path at the local density-dependent distance.

Leaving sub-pen spacing unconstrained was rejected because the requested ink
would print as a solid patch and hide the contour structure. Compression is
therefore bounded to `0.9` pen widths and `90 %`.

## Risks and follow-up

Dense shadows generate more marks and plot time. `Max marks/ink` remains the
hard output bound, and excessive compression can merge adjacent pen strokes
physically even though their centerlines remain separate.

The software comparison is verified, but the reference-level compression,
paper spread, and best default for each installed pen remain pending a physical
four-pass sheet.

## Files

- `software/converter_core/structure_tensor.py`: local pitch mapping,
  continuous neighbour seeding, and local separation occupancy.
- `software/converter_core/cmyk.py`: per-ink/shared API plumbing and Auto
  coverage estimate.
- `software/generator_tabs/cmyk_tab.py`: control, recipe state, recommendations,
  Fine detail, and manifest.
- `software/generator_tabs/cmyk_sheet.py`: calibration-sheet geometry and
  manifest.
- `software/tests/test_cmyk_edge_flow.py`: monotonic pitch and dense-output
  regressions.
- `software/tests/test_cmyk_tab.py`: UI, persistence, recommendation, and
  manifest coverage.
- `software/README.md`: current behavior and operating guidance.
- `docs/proposals/flow-field-cmyk.md`: updated implemented design.
