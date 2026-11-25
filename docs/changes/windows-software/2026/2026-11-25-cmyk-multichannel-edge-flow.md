---
id: WSW-20261125-002
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/structure_tensor.py
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - edge-flow
  - structure-tensor
  - streamline
  - image-gradients
  - color-detail
  - portrait
  - physical-validation-pending
related:
  - WSW-20261123-019
  - WSW-20261123-002
---

# Guide CMYK streamlines with a multichannel image field

## Summary

Edge-flow CMYK now derives one smooth direction field from luminance and the
separated C/M/Y/K tone gradients. All four independently seeded ink networks
follow that shared image form through moderate coherent structure, continue
through temporary single-ink tone gaps, and fall back to their fixed screen
angles only where the field is weak or ambiguous.

## Reason

The implementation already followed the public Reddit workflow's broad steps,
but its guidance gate required unusually strong gradients. On the supplied
`IMG_0514.JPG` comparison, the tensor controlled only about 14% of the field
strongly; the median pixel was almost entirely on per-ink fallback directions.
That left broad facial planes crosshatched by four unrelated angles even though
the source contained usable contours and tonal gradients. The guide was also
built only from processed scene luminance, so boundaries carried mostly by
colour were underrepresented in the production path.

## Implementation

- `prepare_image_tones` now exposes an internal flow guide assembled from the
  existing C, M, Y, K, and scene-depth arrays without allocating a second
  full-resolution image.
- The structure-tensor calculation accepts a sequence of same-sized channel
  fields, accumulates `Ix²`, `IxIy`, and `Iy²` from each, and blurs the combined
  tensor as before.
- The tensor noise floor now rejects truly weak texture rather than ordinary
  soft gradients. Coherence and strength are combined through a continuous
  square-root blend, so moderate structure keeps the shared direction while
  flat fields still use each ink's fixed fallback angle.
- Per-ink Edge-flow tracing accepts a separate support field. The CMYK tab uses
  shared scene depth for path continuation and the ink's own tone for its
  visible intervals. A cyan highlight gap no longer cuts the entire form before
  a later cyan contour can be reached.
- The normal production mode remains four independent, separately saved ink
  networks. The experimental shared coordinate-network mode remains available
  separately, and pitch, layer count, pen width, page registration, and G-code
  contracts are unchanged.

## Verification

- Field instrumentation on the supplied portrait at `2.5 mm` paper smoothing
  changed the mean guidance weight from `0.284` to `0.681`; the fraction at
  `>= 0.90` changed from `0.140` to `0.423`, and the post-change median was
  `0.766`.
- A synthetic moderate linear gradient that previously stayed mostly on the
  fallback screen is now `>= 75%` aligned to its tensor tangent; weak and flat
  fields still retain the configured fixed angle.
- The focused Edge-flow and CMYK-tab modules pass `83` tests. The focused CMYK
  photo module passes `17` tests.
- Complete converter discovery passes `683` tests with one expected
  OpenGL-context skip in `153.902 s`.
- A software contact sheet rendered the normal per-ink, experimental shared,
  and old channel-gated continuation paths for visual inspection
  (`tmp/edge-flow-variants.png`, not a tracked artifact).

## Struggles and rejected approaches

Increasing seed density alone was rejected because the mismatch was direction,
not pitch. Replacing the independent networks with the shared coordinate
network was also rejected: that path already exists as a comparison mode, and
it suppresses the reference print's separate per-ink behavior.

Using only luminance with a weaker gate exposed colour-only boundaries poorly.
Stacking another full-resolution RGB array would consume substantial memory at
the supported high source resolutions, so the implementation reuses the
already-separated tone arrays.

The first, higher absolute tensor floor treated broad but clear gradients as
noise. A dedicated moderate-gradient regression now prevents that regression.

## Risks and follow-up

The stronger field can bend a screen more aggressively across low-contrast
texture than the previous setting. The existing `Flow smoothing` control
remains the tradeoff between fine wrinkle detail and calm, long contours.

All verification is software-only. Physical four-pass density, pen spread,
paper response, registration, and the best pitch/layer pair still require a
printed comparison against the Reddit reference.

## Files

- `software/converter_core/structure_tensor.py`: multichannel tensor support,
  stronger moderate-gradient guidance, and separate path-support sampling.
- `software/converter_core/cmyk.py`: internal flow-guide construction and
  per-ink support plumbing.
- `software/generator_tabs/cmyk_tab.py`: supplies the multichannel guide and
  shared depth support to both Edge-flow modes.
- `software/tests/test_cmyk_edge_flow.py`: moderate-gradient guidance and
  colour-only edge regressions.
- `software/tests/test_cmyk_tab.py`: verifies the shared guide and support field
  reach every per-ink network.
- `software/README.md`: current production behavior and tuning guidance.
- `docs/proposals/flow-field-cmyk.md`: updated implemented design.
