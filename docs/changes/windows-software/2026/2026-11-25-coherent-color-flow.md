---
id: WSW-20261125-004
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/structure_tensor.py
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_edge_flow.py
  - software/tests/test_cmyk_separation.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
  - docs/proposals/flow-field-cmyk.md
tags:
  - cmyk
  - edge-flow
  - coherent-color-flow
  - streamline
  - ink-planes
  - edge-preserving
  - keylines
  - transparency
  - portrait
  - physical-validation-pending
related:
  - WSW-20261125-003
  - WSW-20261125-002
  - WSW-20261123-019
  - WSW-20261124-006
---

# Add a coherent shared-geometry CMYK color-flow renderer

## Summary

The CMYK tab now offers **Coherent color flow (shared geometry, ink planes)**,
and **Use recommended photo defaults** selects it. One streamline geometry is
traced per density layer through the blurred multichannel structure tensor.
Each path keeps contiguous local CMYK assignments instead of independently
phasing four short tone gates. Dark regions add offset parallel layers, weak
structure retains the four fixed screen angles by layer, and Black keylines
stay on high-confidence image boundaries.

The prior independently seeded per-ink renderer and the stochastic shared
Edge-flow experiment remain selectable. All modes preserve the four separate
page-registered G-code files.

## Reason

The existing guide correctly followed facial contours, but the production
per-ink path converted each traced streamline into `4-8 mm` stochastic
channel intervals. On the open Golden Sunset source at its live
`1.2 mm` source pitch, pen `0.9 mm`, smoothing `3.5 mm`, three layers, and
`60 %` compression, `46.6 %` of visible marks were shorter than `5 mm`; the
90th percentile was `16.24 mm`. Four independent fallback networks also
crossed in flat, high-texture areas, which read as multicoloured fragments.

That geometry ownership, not a lack of global contrast, explained why more
tone force amplified glasses, lights, and plaid instead of producing the
reference's broader color planes. A comparison render showed the same source
could support longer coherent paths without replacing the four-pen output
contract.

## Implementation

- `structure_tensor.py` now exposes one tensor-component stage and blends it
  toward a per-density-layer fallback angle. Coherent layers therefore share
  the same edge tangent where structure is clear but retain cyan 15°, magenta
  75°, yellow 0°, and black 45° in weak regions.
- `_coherent_ink_runs()` smooths channel coverage along arc length rather than
  randomly segmenting each channel. A 6 mm paper-space window keeps the
  dominant ink and includes a second ink only when it reaches `72 %` of that
  coverage. Small gaps up to the operator's path bridge remain one stroke.
- The coherent tracer continues its geometry through ordinary tone changes and
  applies the density-layer threshold to visible ink runs. Dark layers add
  offset parallel geometry instead of creating more random dashes.
- Black is weighted against ordinary dark texture while keylines are active,
  but is boosted continuously where guidance confidence exceeds the keyline
  gate. C/M/Y are lightly quieted at the same boundaries.
- Coherent color flow applies a self-guided edge-preserving simplification at
  `65 %` of Flow smoothing before sharpening and separation.
- Transparent source pixels are now composited onto white paper. The open
  circular PNG stored transparent black RGB; converting it directly to RGB
  previously turned the entire surround into dense black ink.
- Page size, artwork scale, pen offsets, registration, colour separation,
  preview, save, planner, and G-code contracts are unchanged.

## Verification

- A synthetic coherent path through a mid-tone region keeps one ink over more
  than `55 mm`.
- A two-plane fixture confirms local yellow and magenta coverage without
  introducing cyan or black.
- A strong-edge fixture confirms Black keyline ink increases while the colour
  path remains present.
- A texture fixture confirms the guided filter removes fine interior variance
  while retaining at least `80 %` of a strong boundary step.
- A transparent-RGBA fixture confirms all four separated tone arrays remain
  below `1e-6`.
- On the open Golden Sunset selfie with the same scale, pitch, pen width,
  smoothing radius, layer count, and compression, coherent color flow (with
  keylines) raised the mark-length 90th percentile from `16.24` to `29.18 mm`,
  raised the maximum from `142.26` to `378.80 mm`, and reduced the sub-`5 mm`
  share from `46.6 %` to `40.8 %`. The diagnostic contact sheet is
  `tmp/coherent-flow-compare.png` and is not a tracked artifact.
- Focused CMYK Edge-flow, separation, photo, and tab modules pass `119` tests.
- Complete converter discovery passes `692` tests in `135.933 s` with the one
  expected OpenGL-context skip.

## Struggles and rejected approaches

Simply increasing contrast, GCR, layer count, or compression was rejected
because it amplified source texture and still gated short path intervals.
Keeping four independent networks while only merging their endpoints was also
rejected: it reduced pen lifts but did not give ink assignments a stable local
geometric owner.

The first coherent render used random per-channel phase gates through the
shared tracer. It reduced four-way overlap but still produced short speckled
swatches. The first keyline threshold also treated high-contrast texture as
structure and made Black dominate; the implemented version reserves ordinary
Black weight and raises the confidence gate.

Replacing the four-file CMYK save with one flattened colour line program was
rejected because it would break the physical pen-swap and registration
workflow.

## Risks and follow-up

The 6 mm coverage window, 72 % secondary-ink ratio, keyline confidence, and
source-simplification ratio are software-selected from synthetic geometry and
the current selfie. They have not been validated on paper or against a source
photo comparable to the Reddit portrait.

Coherent paths can still be limited by real silhouette boundaries and the
image's structure. The current source remains much busier and higher-key than
the reference, so exact tonal and color matching cannot be claimed. Pen spread,
four-pass registration, connector visibility, elapsed time, and the best
pitch/layer combination remain physical validation work.

`structure_tensor.py` now owns source simplification, tensor construction,
legacy tracing, shared tracing, and coherent ink assignment. Split geometry
generation from ink assignment before adding another renderer; the concrete
acceptance criteria are tracked in `docs/project/ROADMAP.md`.

## Files

- `software/converter_core/structure_tensor.py`: shared tensor components,
  per-layer fallback angles, coherent ink-plane assignment, and keyline gate.
- `software/converter_core/cmyk.py`: coherent renderer entry point,
  edge-preserving source preprocessing, and transparent-image handling.
- `software/generator_tabs/cmyk_tab.py`: style option, recommended recipe,
  source simplification, shared build path, and manifest metadata.
- `software/tests/test_cmyk_edge_flow.py`: coherent-run, color-plane, keyline,
  fallback, and edge-preserving regressions.
- `software/tests/test_cmyk_separation.py`: transparent-pixel regression.
- `software/tests/test_cmyk_tab.py`: style build, recommended defaults, layer
  angles, and manifest coverage.
- `software/README.md`: current user behavior and starting recipe.
- `docs/proposals/flow-field-cmyk.md`: implemented coherent-flow architecture.
