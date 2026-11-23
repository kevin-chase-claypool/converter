---
id: WSW-20261122-003
date: 2026-11-22
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/structure_tensor.py
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - edge-flow
  - structure-tensor
  - color-detail
  - portrait
  - image-screening
related:
  - WSW-20261122-002
  - WSW-20261122-004
---

# Preserve color-only detail in edge-flow CMYK

## Summary

Edge-flow CMYK now builds its shared direction field from all processed RGB
channels instead of reducing the source to luminance first. Chromatic
boundaries with little or no luminance difference can therefore steer the
streamlines instead of disappearing into the fixed-angle fallback.

The processed-RGB guide was shared immediately. A later fix,
`WSW-20261122-004`, also makes the traced streamline network and layer
placement common; without that step the per-ink masks still produced visible
rainbow fringes at the same edge.

## Reason

The first edge-flow implementation used `tones["depth"]`, derived only from
luminance, as its tensor guide. In the displayed childhood portrait, several
face, clothing, and background separations carry more chroma than brightness.
Those edges were absent from the tensor, so broad luminance isophotes replaced
finer forms and the result lost substantially more detail than the reference
conversion.

## Implementation

- `prepare_image_tones()` retains its post-adjustment RGB image as the
  internal `flow_rgb` guide.
- `screen_channel()` accepts an optional `flow_guide` image.
- The structure-tensor builder accepts either a 2D luminance field or a
  channel-last color image. For RGB, it sums each channel's
  `Jxx/Jxy/Jyy` gradient tensor before blurring and solving the tangent
  orientation.
- The CMYK tab passes `flow_rgb` for every ink. Wave screens continue to use
  the separate luminance `depth` field, so this change does not alter the
  existing Wave behavior.
- The saved manifest identifies the guide mode as
  `shared_processed_rgb_structure_tensor`. `WSW-20261122-004` extends this
  identifier to `shared_processed_rgb_structure_tensor_union_coverage` after
  shared streamline geometry is added.

## Verification

- A new red-green test uses two equal-luminance colors with a strong boundary.
  Before the fix, the API did not accept the color guide. After the fix, the
  output streamlines align with the color boundary instead of the horizontal
  fallback angle.
- All seven focused edge-flow tests pass.
- A software render of the reported `IMG_0514.JPG` with the retained RGB guide
  preserved substantially more facial, shirt, wood, and background detail than
  the luminance-only version. The image still needs a physical pen test.
- The software-selected starting recipe is recorded in `software/README.md`.
  It uses three flow layers, `2.0 mm` smoothing, and a `0.31 mm` seed pitch;
  the lighter two-layer version lost tonal depth and the four-layer version
  reduced separation. The live 1600 px preview reported pen-down counts of
  C 4252, M 4910, Y 5709, and K 5821.
- The complete converter discovery suite passes `630` tests with one expected
  OpenGL-context skip.
- Documentation indexing and link validation pass for all `510` change notes.

## Struggles and rejected approaches

Using the separated C/M/Y/K tone maps as independent tensor guides would make
each plate choose a different direction in mixed-color regions. Blending only
the luminance tensor back toward the per-channel tone was rejected because
color-only boundaries can disappear entirely from luminance.

The existing per-ink tone masks and four density layers remain necessary; a
color-aware direction field alone does not create ink where a plate has no
coverage.

## Risks and follow-up

The RGB tensor increases detail sensitivity and may follow JPEG color noise or
compression artifacts. Users can raise Flow smoothing when that happens. The
software preview is not a physical result: line separation, four-ink overlay,
and pen saturation still require the pending edge-flow bench print.

## Files

- `software/converter_core/structure_tensor.py`: multi-channel structure
  tensor.
- `software/converter_core/cmyk.py`: retained processed RGB guide and public
  flow-guide parameter.
- `software/generator_tabs/cmyk_tab.py`: passes the shared RGB guide.
- `software/tests/test_cmyk_tab.py`: equal-luminance color-boundary regression.
- `software/README.md`: current color-aware behavior.
- `docs/project/ROADMAP.md`: physical-validation status.
- `docs/project/ENGINEERING_LOG.md`: implementation event.
