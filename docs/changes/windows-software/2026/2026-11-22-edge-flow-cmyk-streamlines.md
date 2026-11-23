---
id: WSW-20261122-002
date: 2026-11-22
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/structure_tensor.py
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/cmyk_sheet.py
tags:
  - cmyk
  - edge-flow
  - structure-tensor
  - streamlines
  - portrait
  - image-screening
  - calibration
  - reddit
related:
  - WSW-20261023-001
  - WSW-20261122-003
  - docs/testing/CMYK_CALIBRATION.md
---

# Add edge-flow streamline screening to the CMYK tool

## Summary

The CMYK tool has a new **Edge-flow streamlines (structure tensor)** Screen
style. It builds one shared edge-following direction field from scene
luminance, then traces separate tone-masked streamline sets for cyan,
magenta, yellow, and black. Darker areas receive additional offset layers.
Flat or low-coherence regions fall back to the ink's fixed screen angle.

The existing rectilinear fill remains the shipped default and existing saved
recipes retain their current screen behavior.

## Reason

The linked r/PlotterArt portrait demonstrates a useful visual distinction from
ordinary dot, line, and rectilinear screens: the lines follow facial contours
and other image structure rather than a single global screen angle. The
artist described using image gradients, a blurred structure tensor, evenly
spaced streamlines, extra layers in dark areas, and a fixed-angle fallback.

That method was implemented as a separate CMYK screen so it does not change
the tuned row-lock, rectilinear, Wave, calibration, or four-pass registration
workflows. No third-party source code was copied; the repository uses its own
NumPy/Pillow implementation, tests, and job contract.

## Implementation

- `converter_core/structure_tensor.py` computes gradients of the shared
  luminance guide, builds `Jxx/Jxy/Jyy`, blurs those tensor components with
  three separable box passes, and blends the minor-eigenvector tangent toward
  the selected fixed angle according to coherence.
- Streamline seeds use a staggered deterministic grid. Trace integration is
  midpoint-normalized and stops at the image boundary, below the per-ink tone
  threshold, or when another streamline in the same density layer already
  occupies the cell.
- Layer 0 covers all visible ink. Later layers apply progressively higher ink
  thresholds, so dark regions gain line density while light paper remains
  open.
- `screen_channel(style="edge_flow")` accepts Flow smoothing and Flow layers.
  The existing Dot pitch, Path tolerance, Max marks/ink, overdraw, seed,
  registration crosses, pen offsets, CMYK recipe sidecar, preview, and save
  pipeline remain authoritative.
- The direction field is shared across inks, but each ink is masked by its own
  separated coverage. This keeps the C/M/Y/K passes visually registered on the
  same forms without forcing equal ink density.
- The calibration sheet can match edge-flow output. Its manifest records the
  screen style, pitch, smoothing, layer count, and shared-guide mode.

## Verification

- New red-green tests cover edge alignment on a known diagonal structure,
  fixed-angle fallback on a flat guide, extra dark-tone layers, UI
  build/round-trip, and calibration-sheet matching. All `108` CMYK-tab tests
  pass.
- All `16` CMYK sheet/scan-tool tests pass, including the expanded calibration
  screen choice.
- The complete converter discovery suite passes `628` tests with one expected
  OpenGL-context skip. Documentation indexing and link validation pass for all
  `509` change notes.
- A 900 px portrait render produced non-empty C/M/Y/K layers in `1.69 s`
  software time at `1.2 mm` seed pitch, `2.5 mm` smoothing, and three layers.
  Visual inspection confirmed that lines follow the face and clothing forms;
  this was a software render, not a plot.
- The target tests include all existing CMYK screen styles, so the new branch
  did not replace the legacy rectilinear, Wave, stipple, contour, or dot paths.

## Struggles and rejected approaches

The original Reddit post does not publish the author's script, and Reddit's
anonymous page required a challenge on this host. The public Redlib mirror
provided the post and the author's method comment; implementation was rebuilt
from that described behavior rather than copied.

Pillow's float-image Gaussian blur rejected `F` mode on the installed Pillow
version. The first blur attempt failed tests; the final separable box-pass
implementation keeps the NumPy-only dependency path and is covered by the
orientation tests.

A per-ink tensor was rejected because the four plates would drift onto
different directions in colour regions and lose the coherent portrait look.
Using fixed row spacing for every tone was rejected because it discards the
artist's darker-area extra-layer behavior.

## Risks and follow-up

The software path is verified, but no four-pen physical sheet has validated
the best pitch, smoothing, layer count, or ink order. `Max marks/ink` can
coarsen the effective seed pitch; that is intentional and recorded, but the
preview does not yet label the exact internally increased pitch. The method
also depends on a pre-cropped source with useful luminance structure; a photo
of a print includes the wall and paper edges as real image structure.

The initial shared luminance-only guide lost color-only detail and was
superseded by the processed-RGB guide in `WSW-20261122-003`.

The next physical gate is a one-page A4 portrait at `1.2 mm` pitch, `2.5 mm`
smoothing, three layers, normal GCR, and one HOME + REGISTER, followed by a
comparison of line separation, pen-up drag, four-ink overlay, and elapsed time.

## Files

- `software/converter_core/structure_tensor.py`: shared tensor field and
  streamline tracer.
- `software/converter_core/cmyk.py`: new `edge_flow` public screen branch and
  parameters.
- `software/generator_tabs/cmyk_tab.py`: Screen controls, recipe persistence,
  layer build arguments, and manifests.
- `software/generator_tabs/cmyk_sheet.py`: edge-flow calibration matching.
- `software/tests/test_cmyk_tab.py`: red-green geometry, density, fallback,
  UI, and calibration tests.
- `software/tests/test_cmyk_sheet.py`: edge-flow patch spacing and page-bound
  coverage.
- `tools/cmyk_calibrate.py`: calibration CLI accepts the new sheet screen.
- `software/README.md`: current user behavior and limitations.
- `docs/testing/CMYK_CALIBRATION.md`: edge-flow sheet handoff.
- `docs/project/ROADMAP.md`: pending physical validation task.
- `docs/project/ENGINEERING_LOG.md`: implementation event.
