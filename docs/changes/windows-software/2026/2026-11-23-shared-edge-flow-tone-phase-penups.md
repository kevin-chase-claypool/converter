---
id: WSW-20261123-018
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: superseded
components:
  - software/converter_core/structure_tensor.py
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_cmyk_tab.py
  - software/tests/test_generator_tabs.py
  - software/README.md
  - docs/proposals/flow-field-cmyk.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - edge-flow
  - shared-path
  - tone-gating
  - black-overprint
  - photo-reproduction
  - auto-prediction
  - pen-down
  - toolpath-efficiency
related:
  - WSW-20261123-019
  - WSW-20261123-017
  - WSW-20261123-016
  - WSW-20261123-011
---

# Correct shared Edge-flow tone gating, penups, and generator fits

Superseded by `WSW-20261123-019`, which restores independent per-ink Edge-flow
as the production style and keeps this corrected shared renderer as an explicit
experimental option.

## Summary

Shared Edge-flow geometry remains, but each CMYK ink now uses an independent
deterministic tone phase and a normalized occupancy budget. Similar channel
tones no longer select the same arc-length segments and render as a black mass.
The existing adjacent pen-down chain is enabled for Edge-flow, reducing M3/M5
cycles while adding only local connector ink. Explicit **Fit inside** and
**Fill bed** now also reach Preview and Save for generator tabs instead of
being reset to manual 1:1.

## Reason

`c3f07ed` introduced one streamline network for all four inks. Every channel
used the same `path_key`, layer, and arc-length threshold, so similar coverage
fields selected the same runs. For `IMG_0514.JPG` on the live `200 x 200 mm`
page, `0.52 mm` effective pitch, `0.5 mm` pen, and five layers, a rendered
1200-pixel check put `95.4 %` of the inked union below `0.2` luminance; `13.1 %`
of that union had all four inks. The coverage-based Auto estimate still claimed
`4.7/255`.

A full revert removes the black mass but restores four independent path
networks. The parent-snapshot render measured `67.6 %` dark and only `0.59 %`
four-ink overlap, but visibly returned the separated rainbow/speckle paths that
motivated `c3f07ed`. Reverting therefore fixes the symptom by discarding the
requested shared registration geometry.

The owner also confirmed that `260 %` is intentional for this portrait: the
enlarged image is a deliberate circular crop that fills the bed. The
`305.46 mm` bounding radius and reach warning are expected for that
composition; **Fit inside** is only the option for keeping the entire uncropped
image and must not be applied automatically.

## Implementation

- Each shared path is still traced once and sampled by every ink at the same
  coordinates.
- `edge_flow_coverage_factor()` applies the pen-width/pitch area factor and a
  layer normalization shared by the tracer and Auto. Five layers deepen detail
  without multiplying one channel into full occupancy.
- Each channel gets a deterministic phase salt in `_path_tone_threshold()`.
  Similar tones now select different local runs on the common path instead of
  the identical runs.
- Auto receives the active Flow-layer count and scores the same occupancy
  factor. The UI labels the result a coverage RGB estimate rather than a
  paper-validated error.
- The CMYK tab applies the existing nearest-endpoint chain to Edge-flow within
  the operator's `5 mm` keep-down gap. The same-streamline `4 mm` bridge stays
  in place. Connectors are visible ink but are local and materially reduce
  penups.
- Generator tabs still default to manual 1:1, but a fit action records an
  explicit override for the current artwork. The effective settings and reach
  warning use that scaled radius, so the action is no longer cosmetic.

## Verification

- The new rendered-overlap regression renders all four pen masks with the
  configured pen width. It fails the old correlated gate at `12.57 %`
  four-ink overlap and passes the corrected gate with no four-ink overlap in
  the minimal test, `50.1 %` dark union pixels, and `648` total marks.
- On the live portrait recipe at `260 %`, the corrected gate reduced raw marks
  from `27,176` to `18,081`, four-ink overlap from `13.05 %` to `0.49 %`, and
  dark ink-union pixels from `95.38 %` to `64.66 %`. Mean rendered luminance on
  the ink union rose from `0.098` to `0.267`.
- Applying the existing `5 mm` chain to that corrected render reduced M3
  sequences from `18,081` to `7,965`; ink area grew from `32.96 %` to `36.30 %`
  and dark union pixels changed from `64.66 %` to `65.13 %`.
- Auto on the live portrait now reports a `32.8/255` coverage estimate instead
  of `4.7/255`; it chooses a darker compensation curve that still needs paper
  validation.
- `IMG_0514.JPG` at `260 %` has a `305.46 mm` artwork radius against the
  `180 mm` reach. This is the operator's intentional circular crop, so the
  saved production layout remains manual `1.0 / 260 %` with offsets
  `-3.17, -28.74 mm`. Fit inside would instead produce about `153.21 %` final
  equivalent scale for an uncropped image.
- During live inspection, the old `settings_for_source()` path discarded an
  explicit generator fit and kept restoring manual scale `1.0`. The new
  generator-fit regression verifies that the fit mode and sub-1 scale reach
  Preview, Save, and the effective reach calculation when the operator chooses
  that option.
- `python -m unittest software.tests.test_cmyk_tab -v` passes all `139` tests.
- Complete converter discovery passes `665` tests with one expected
  OpenGL-context skip.
- `python tools\docs_index.py --write` rebuilt five indexes, and
  `python tools\docs_index.py --check` passes for all `529` change notes.

## Struggles and rejected approaches

Keeping the shared `path_key` and adding only a Black coverage cap removed some
four-way overlap but left every similar tone field correlated. Dividing the
occupancy by the full layer count removed black mass but under-inked the photo.
The square-root layer factor matched the measured rendered channel area more
closely and retained useful density.

Fully reverting `c3f07ed` was rejected because it restores the independent
rainbow tracks. Disabling the connector chain preserved exact co-location but
nearly doubled the corrected M3 count, so it conflicts with the operator's
print-time requirement.

## Risks and follow-up

- The square-root layer occupancy is calibrated from the current software
  renderer, not a printed sheet. Paper density, felt spread, connector marks,
  and wet four-pass registration remain unverified.
- Auto is now less optimistic but still models occupancy rather than a complete
  rasterized line image.
- The `260 %` live artwork is intentionally outside the page bounding circle,
  so its corners/outer page are clipped. Preserve that composition unless the
  owner explicitly wants the whole uncropped image.
- Edge-flow chaining adds visible short connectors. The first physical print
  must judge whether their time savings are worth the added marks.

## Files

- `software/converter_core/structure_tensor.py`: per-channel tone salts,
  shared occupancy factor, and gated-run contract.
- `software/converter_core/cmyk.py`: Edge-flow-aware Auto coverage model and
  Flow-layer plumbing.
- `software/generator_tabs/cmyk_tab.py`: Auto layer input, honest estimate
  label, and Edge-flow adjacent chaining.
- `software/qt_svg_to_gcode.pyw`: explicit generator fit ownership and
  effective reach display.
- `software/tests/test_cmyk_tab.py`: rendered black-mass regression, shared
  geometry support, Auto honesty, layer forwarding, and penup chaining.
- `software/tests/test_generator_tabs.py`: generator Fit-inside propagation and
  effective radius.
- `software/README.md`: current behavior, corrected Auto result, pen-down
  tradeoff, and the intentional `260 %` crop versus optional Fit inside.
- `docs/proposals/flow-field-cmyk.md`: implemented shared phase/occupancy
  model.
- `docs/project/ROADMAP.md`: physical-validation status and corrected metrics.
