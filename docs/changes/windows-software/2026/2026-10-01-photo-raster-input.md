---
id: WSW-20261001-008
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
  - software/qt_svg_to_gcode.pyw
tags:
  - fill
  - tone
  - raster
  - photo
  - interface
related:
  - WSW-20261001-007
  - WSW-20261001-004
  - software/README.md
---

# Photos import directly and plot as sine-wave tone

## Summary

`Browse` now accepts `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, `.tiff`
and `.gif` alongside `.svg`. A photo needs no SVG wrapper: it is always hatched
from its pixels, its luminance is the tone, and with
`Fill pattern = gradient waves (sine_gradient)` that tone is drawn as wave
amplitude - dark features swell the waves, light ones flatten them. Verified on
the requested photo (`C:\Users\jacks\Downloads\IMG_0514.JPG`, 773 x 1031): at
`Fill spacing 4`, `Fit = Fill bed`, the whole program is 92 contours /
73,996 points / 272 x 363 mm on paper and builds end to end in 4.0 s.

## Reason

"i want to be able to import this jpg, make it black and white and maintain the
gradients by using the sine wave approach", sent with a portrait photo. The
converter could already hatch a *rendered* image - that is what the image-tone
source does for an SVG with an embedded `<image>` - but the file dialog only
offered `.svg`, so a photo had to be wrapped by hand first.

## Implementation

- `converter_core/geometry.py`: `RASTER_IMAGE_EXTENSIONS` and
  `is_raster_image(path)`; `svg_fill_sources` reports `image: 1` for a raster
  without parsing it; `resolve_fill_source` returns `tone` for a raster whatever
  `Fill source` says, because there are no vector regions to hatch.
- `qt_svg_to_gcode.pyw`:
  - `pick_svg` offers an `Artwork` filter with SVG and image patterns, and the
    log line says `Image selected` for a raster.
  - `raster_shade_contours` loads a raster with `QImage`, converts it to ARGB32,
    and treats one view unit as one source pixel - exact tone sampling with no
    renderer and no resampling, capped at 2400 px on the long side.
    `maybe_flip`, `darkness_at` and every tone pattern then work unchanged.
  - `load_contours` skips `parse_svg_geometry` for a raster and generates the
    tone fill only.
  - `image_bounds_mm` and `fitted_settings_for_image` size a raster from its
    image bounds; the preview thread applies that fit *before* the fill is
    built, because the fill spacing is millimetres and cannot be resolved until
    the paper scale is known. This is also why the worker skips its usual
    second parse for rasters: the fit is already final.
- `auto_configure_shading` already set tone-friendly starters for image-tone
  artwork; its log now says `photo tone` for a raster.

## Verification

- 159 tests pass, including the new `software/tests/test_raster_import.py`:
  raster extensions are recognised, a raster resolves to `tone` even with
  `Fill source = SVG shapes`, a photo produces fill that fits the reach circle,
  the image fit does not depend on the stale scale left in the field, and the
  point count scales with paper area over spacing squared.
- The requested photo through the real window and pipeline
  (`fitted_settings_for_image` -> `load_contours` -> `plan_program` ->
  `build_preview_moves` -> `contours_to_gcode`):

  | Fill spacing | Scale | Points | Paper | Total | G-code lines |
  |---|---|---|---|---|---|
  | 4 mm | 0.3517 | 73,996 | 272 x 363 mm | 4.0 s | 68,428 |
  | 3 mm | 0.3517 | 131,132 | 272 x 363 mm | 7.2 s | 121,132 |

- Render check `samples/preview/photo-sine-gradient-4mm.png` (scratch, not
  committed): the face, the log and the shirt read through wave amplitude with
  the background filling in at a similar density, which is the expected
  behaviour of a luminance-driven amplitude - a photo has tone almost
  everywhere, so very little paper stays blank.

## Struggles and rejected approaches

- First cut returned the fill straight from `load_contours` and let the worker
  fit it afterwards. The fit runs on the fill contours, which are inset by the
  ink threshold, and the fill cannot be generated before the paper scale is
  known, so the first pass either exploded (spacing read at scale 1.0 on a
  4000-pixel image) or the artwork crept larger on every build.
- Considered generating the tone fill in paper millimetres for rasters only.
  Rejected: the raster, `darkness_at` and every pattern helper work in view
  coordinates, and mixing conventions between SVG and raster inputs would be a
  second units bug.
- Considered requiring the user to wrap the photo in an SVG. Rejected: the
  wrapper changes nothing about the result and everything about the workflow.

## Risks and follow-up

- Tone is linear luminance with a 0.04 ink floor and no curve control, so a
  photo with a large bright area draws near-flat hairlines there instead of
  leaving paper blank. A tone curve (`Image gamma` / contrast) is the obvious
  next control if the plots read washed out.
- `Fill spacing` is the only calibration for how much of the photo survives: a
  coarse pitch keeps the large shapes and loses the fine detail, which is a
  judgement to make on paper.
- Very large photos are downscaled to 2400 px before sampling; that cap is a
  constant, not a setting.

## Files

- `software/converter_core/geometry.py`: raster detection and fill-source rules.
- `software/qt_svg_to_gcode.pyw`: image loading, raster branch, image fit, file
  filter, log text.
- `software/tests/test_raster_import.py`: the new test module.
- `software/README.md`: how to import a photo and what the tone means.
