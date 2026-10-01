---
id: WSW-20261001-009
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
tags:
  - fill
  - performance
  - fit
  - interface
related:
  - WSW-20261001-007
  - WSW-20261001-008
  - software/README.md
---

# Auto fit measures the artwork before it fills it

## Summary

The preview's auto fit now measures the artwork with an outlines-only read and
then builds the fill once, at the fitted scale. Previously the first read built
a complete fill at whatever scale the Scale box still held, and the fit threw
that geometry away and re-read. On artwork with a large viewBox that first fill
was the whole stall: a 3000 x 2000-unit gradient asked for `Fill spacing 4` and
generated 4.5 million points at scale 1.0 before the fit could run, so the
window sat at `Parsing SVG geometry | 49.6 s`.

The stage line now says `Measuring the artwork`, then
`Building fill geometry`, so the two passes are visible.

It also turned out the reported file (`IMG_0514.svg`) was a bitmap trace of the
photo rather than the photo or gradient artwork, which is a separate trap: a
trace has no gradients and hatches one lattice per traced layer. The app now
recognises that shape of file and says so in the log.

## Reason

Reported twice as the same symptom: the sidebar set correctly
(`Fill spacing 4`, `gradient waves (sine_gradient)`, `Wave size 0`) and the
build stuck at 10 % for about fifty seconds. A raster input was already
protected - `WSW-20261001-008` sizes a photo from its image bounds before
filling - but an SVG with a large viewBox still filled at the stale scale.

## Implementation

- `qt_svg_to_gcode.pyw`:
  - `load_contours(..., fill=True)` gains the `fill` switch. `fill=False`
    returns outlines only, which for the vector source means
    `hatch_spacing = 0` and for the image-tone source means skipping
    `raster_shade_contours` entirely.
  - `raw_geometry_key` includes `fill`, so the measuring read cannot be served
    as the fill read.
  - `Worker.run` measures first when the fit mode is `fill` or `inside`, then
    fits, then generates the fill once. A manual fit skips the measuring read
    and fills once. A raster is sized from its image bounds as before.
  - If the measuring read returns no contours at all - an SVG whose only
    content is an embedded photo - the fit falls back to the viewBox, which
    `artwork_bounds_mm` now provides for both rasters and SVGs (it replaces the
    raster-only `image_bounds_mm`).
  - `auto_configure_shading` logs a `looks like a traced bitmap` warning when
    the artwork has 40 or more filled elements and no image or gradient. The
    reported file turned out to be exactly that: a VTracer trace of the photo,
    273 flat black paths. A trace has no gradients left, resolves to `SVG
    shapes`, and hatching its layers separately is what ran for minutes; the
    warning points at the source raster instead.

## Verification

- 161 tests pass, including a new contract in
  `software/tests/test_tone_fill_scale.py`: the measuring read returns under 20
  points where the filled read returns more than 100,000, on the same artwork
  and scale, and a classification test in
  `software/tests/test_raster_import.py` for the 60-shape trace case.
- Full pipeline (fit -> fill -> plan -> preview -> G-code) with the Scale box
  left at 1.0, which is the worst case:

  | Input | Fitted scale | Points | Total | Before |
  |---|---|---|---|---|
  | 3000 x 2000-unit gradient SVG | 0.1295 | 61,660 | 3.67 s | 4.5M points in the discarded pass, the reported 49.6 s stall |
  | `IMG_0514.JPG` (773 x 1031) | 0.3517 | 73,996 | 4.24 s | unchanged (already pre-fitted) |

- The reported traced SVG (`IMG_0514.svg`, a VTracer trace: 273 filled paths,
  4,841 cubic curves) still grinds: its vector fill was cancelled after 52 s in
  a benchmark, because the shape path hatches each of the 273 traced layers
  separately. That is inherent to the input, not to this change - the fix for
  the user's goal is to open the source `.jpg`, which builds the same drawing in
  4.2 s.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- The first version of the raster fix (`WSW-20261001-008`) solved the same
  problem for photos only, by pre-fitting from the image bounds. That left the
  identical waste for SVG inputs, which is what this change closes.
- Considered capping the first fill instead of skipping it. Rejected: any cap
  is a silent quality change, and the geometry is discarded anyway.
- Considered keeping a second cache entry so a repeat build could skip the
  measuring read. Rejected for now: the measuring read is milliseconds, and a
  second cache slot has to be invalidated with the same care as the first.

## Risks and follow-up

- An auto fit now always parses the artwork twice, by design. The measuring pass
  is outlines only, so the cost is in the artwork's element count, not its fill.
- Artwork whose outlines are empty *and* whose viewBox is much larger than the
  drawn content now fits to the viewBox instead of to the fill bounds. That is
  the same rule a photo follows, and it is visible in the log's
  `Auto-fit (Fill bed): Scale ...` line.

## Files

- `software/qt_svg_to_gcode.pyw`: the `fill` switch, cache key, worker sequence,
  artwork-bounds fallback, stage labels.
- `software/tests/test_tone_fill_scale.py`: the measuring-pass contract.
- `software/tests/test_raster_import.py`: renamed to the shared bounds helper.
- `software/README.md`: the auto-fit note.
