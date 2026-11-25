---
id: WSW-20261125-005
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/structure_tensor.py
  - software/tests/test_cmyk_edge_flow.py
  - software/README.md
  - docs/proposals/flow-field-cmyk.md
tags:
  - cmyk
  - edge-flow
  - coherent-color-flow
  - scene-depth
  - dark-layers
  - pitch-compression
  - portrait
  - physical-validation-pending
related:
  - WSW-20261125-004
  - WSW-20261125-003
---

# Gate coherent dark layers by scene depth

## Summary

Coherent color flow now uses scene luminance depth for its extra dark-tone
layers and local shade compression. Strong yellow or magenta coverage in a
bright face no longer makes that face behave like a shadow. The base network
still carries the full color image; additional networks begin only at a
scene-depth of `40 %`, with the final layer approaching the darkest `90 %`.

## Reason

The first coherent renderer used maximum C/M/Y/K coverage both to seed extra
layers and to compress pitch. Bright skin has strong yellow/magenta coverage,
so all three networks activated and the `60 %` compression setting contracted
the base pitch there. The resulting preview showed repeated nested color
contours and dense red/yellow paths across highlights instead of the
reference's open light planes with extra density in shadows.

The defect was reproducible with one bright synthetic field: three layers
produced `3267.56 mm` of yellow runs against `1164.94 mm` for one layer, even
though scene depth was only `0.12`.

I also inspected
[`msurguy/plotterfun-extended`](https://github.com/msurguy/plotterfun-extended)
at commit `00bf56dd872db8797486e021c26345929463e985`. Its Flow Field worker
independently supports the same density principle: edge and dark fields carry
the image form, while minimum/maximum separation is derived from source
brightness. It also explicitly masks transparent pixels. However, its CMYK
workflow runs the selected worker independently per channel using ordinary
channel separation; it does not provide a shared blurred structure tensor or
coherent local ink-plane assignment. It therefore supplies design evidence,
not a drop-in renderer. No Plotterfun Extended source was copied.

## Implementation

- Coherent layer seeding, path acceptance, and visible-run gating now sample
  the scene-depth field rather than maximum channel coverage.
- Extra layers interpolate their scene-depth threshold from `40 %` for the
  first additional layer to `90 %` for the final allowed layer.
- Coherent Shade compression also uses scene depth. Per-ink Edge-flow retains
  its existing per-channel compression behavior.
- The base layer still uses channel tone to choose one dominant ink or one
  close secondary ink. The fix does not collapse the output to a single yellow
  field.

## Verification

- The new bright-field regression failed before the fix with
  `3267.56 mm` versus `1164.94 mm` of yellow ink. One- and three-layer output
  now match within `2 %` in bright and middle scene depth.
- A dark-field regression requires three layers to produce more than `1.40x`
  the ink of one layer.
- A compression regression keeps bright-field increased ink below `1.12x`,
  while an `0.88` depth field grows by more than `1.30x`.
- Focused CMYK Edge-flow, separation, photo, tab, and sheet modules pass `137`
  tests in `38.635 s`.
- Complete converter discovery passes `694` tests in `154.523 s` with the one
  expected OpenGL-context skip.
- The full-circle Golden Sunset diagnostic reduced coherent black ink length
  from `20,240.4` to `15,412.9 mm`, magenta from `53,670.5` to
  `47,894.6 mm`, and yellow from `81,236.5` to `64,862.5 mm` at the same
  layout and screen controls.

## Struggles and rejected approaches

Using only the dominant ink removed the secondary color mixes, but the visual
comparison turned most of the face into a nearly uniform yellow field. That
lost the reference's adjacent yellow/red color planes and was rejected.

Keeping channel coverage for pitch compression but adding a depth check only
to extra layers still overdrew highlights, because the base network itself
compressed around bright yellow/magenta areas.

## Risks and follow-up

The `40-90 %` scene-depth range is software-selected. A physical four-pass
print is still required to judge whether shadows are dense enough, whether
highlights remain too open, and whether middle tones need a different layer
threshold.

The current source photograph still differs materially from the Reddit
portrait. No claim of exact tone or color match is implied.

## Files

- `software/converter_core/structure_tensor.py`: scene-depth layer support and
  coherent pitch selection.
- `software/tests/test_cmyk_edge_flow.py`: bright, middle, dark, and
  compression regressions.
- `software/README.md`: current coherent-flow layer behavior.
- `docs/proposals/flow-field-cmyk.md`: implemented density model.
- `docs/project/ROADMAP.md`: current software evidence and physical gate.
- `docs/project/ENGINEERING_LOG.md`: diagnosis and rejected alternatives.
