---
id: WSW-20261127-007
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_cmyk_separation_fidelity.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_generator_tabs.py
tags:
  - cmyk
  - color-management
  - alpha
  - process-ink
  - multiply-composite
  - fidelity
  - ink-profile
related:
  - WSW-20261123-015
  - WSW-20261127-006
  - ADR-015
---

# Preserve transparent source colour and match CMYK to the composite

## Summary

CMYK raster preparation now composites transparency over paper white, applies
EXIF orientation and valid ICC-to-sRGB conversion, and separates colours
against the same process-ink multiply response used by the preview. A loaded
measured ink profile reaches both separation and simulation, so they no longer
optimize and display different ink responses.

## Reason

The supplied Golden Sunset portrait is RGBA with 23.5% fully transparent pixels
and antialiased alpha at almost every edge. Direct `RGBA -> RGB` conversion
turned the transparent exterior black before auto-level and separation. The
top-left corner of the failed CMYK field was
`C/M/Y/K = 0.8674/0.8030/1.0000/0.1539` instead of paper.

The reverted converter also returned to complement-only separation. It knew
the nominal process ink response for preview but did not use that response
when choosing ink coverage. The resulting composite was washed or
colour-shifted, with magenta and yellow overcovered.

## Implementation

- Restored one color-managed image loader for Auto and image-tone preparation:
  EXIF transpose, paper-white alpha compositing, embedded ICC conversion to
  sRGB when valid, and safe RGB fallback.
- Added `separate_cmyk_composite()`: a bounded coordinate-descent solve against
  `product(1 - coverage * (1 - transmittance))`, initialized by the existing
  complement/GCR split and limited by total area coverage.
- Added `multiply_composite_rgb()` and shared nominal ink transmittances.
  The nominal values derive from the same process colours used by the preview.
- The OpenGL ink profile now calls a tab-level profile setter, invalidates the
  CMYK layer cache, and feeds the measured transmittances into separation as
  well as simulation.
- Auto's Wave exposure path was reduced from the washed manual range toward
  normal source exposure; user weights and gamma remain post-match controls.

## Verification

- Focused separation tests cover in-gamut RGB reproduction, natural/saturated
  colours, gamma direction, per-ink weights, total-ink limiting, black
  preservation, nominal/preview transmittance identity, transparent-pixel
  white compositing, and no false ink outside a transparent subject.
- The source-image ideal composite test improves against the actual RGBA file
  using the same loader and multiply model.
- The live fidelity oracle baseline after the integrated Wave/color work has
  family-portrait RGB MAE `0.204`, structure correlation `0.866`, edge
  correlation `0.310`, and luminance MAE `0.201`.
- Remaining fidelity limits are recorded by `WSW-20261127-006`; this note does
  not claim a physical print pass.

## Risks and follow-up

- Nominal process colours are not a spectral measurement of the installed pen,
  paper, pressure, or ink batch. Use a scanned ink profile for physical work.
- Four process inks cannot reproduce every sRGB colour. The solver minimizes
  error but does not expand the physical gamut.
- Physical ink spread and four-pass registration remain unverified.

## Files

- `software/converter_core/cmyk.py`: color-managed loading, composite solver,
  and shared transmittance matrix.
- `software/generator_tabs/cmyk_tab.py`: measured-profile cache invalidation
  and separation routing.
- `software/qt_svg_to_gcode.pyw`: profile propagation to the active CMYK tab.
- `software/tests/test_cmyk_separation_fidelity.py`,
  `software/tests/test_cmyk_tab.py`, and
  `software/tests/test_generator_tabs.py`: color, alpha, and profile tests.
