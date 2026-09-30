---
id: WSW-20260930-019
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - motifs
  - assets
  - generative
related:
  - WSW-20260930-018
  - motifs/README.md
---

# Engraving motifs: Haeckel plates cut into organisms

## Summary

`motifs/nature-engravings/` holds 88 organisms cut from public-domain engraving
plates - Ernst Haeckel's *Kunstformen der Natur* plus botanical and zoological
plates - with per-file credits. They are black-ink line drawings with real
hatching, which is the same vocabulary as the reference kaleidoscope artwork,
unlike the flat PhyloPic silhouettes they sit beside. Motif mode now uses them
as an ornamental **outer band** rather than tiling them through every ring, and
trims each engraving to its boldest 90 strokes so a detailed plate stays
plottable. The set is copied into `samples\png` so the app's remembered folder
uses it immediately.

## Reason

"every one of the pngs you found are not what i asked for. you downloaded
silouhette icons and full mandalas" and, before that, "the goal ... as
beautiful with natural shapes". The reference is hatched line art, so the motif
library needed engraved artwork rather than silhouettes.

## Implementation

- `tools/fetch_engraving_motifs.py` (new): finds freely licensed plates in
  Commons categories (`Kunstformen der Natur`, engravings of plants, botanical
  and zoological illustrations), downloads 1280 px thumbnails with throttling
  and backoff, trims the scan border, keeps ink with an Otsu threshold, finds
  the plate's drawing area between the widest white gutters, then crops that
  area on an overlapping 3x2 grid. Cells with too little ink, too much solid
  black, or that are really a caption line are dropped; crops are filtered
  again by ink density and spread, squared to 512 px 1-bit black on white, and
  written with `manifest.json` and `CREDITS.md`.
- `qt_kaleidoscope.pyw`: motif tracing now accepts detailed line art (rejects
  only above 4,000 contours / 60,000 points) and trims anything above
  `MOTIF_CONTOUR_BUDGET` (90) to its largest strokes, logging what it kept.
- `converter_core/generative.py`: in motif mode only the outer two rings use
  the motif pool; the rings inside use the drawn hatched families. Tiling an
  engraving through every ring produced speckle (143k contours, hours of pen
  cycles); the outer-band rule reads like the reference's ornamental border and
  lands at 13-18k contours.

## Verification

- `tools\fetch_engraving_motifs.py --plates 34 --limit 200` produced 147 crops,
  curated down to 88 by ink density (0.06-0.55) and ink spread (>= 0.5 of the
  tile). Contact sheets: `samples\preview\engraving_sheet3.png` and
  `samples\preview\engraving_final.png`.
- Designs through the app with the engraving folder:
  `samples\preview\gen_engraved4.png` - seed 5 / intricacy 9 = 18,408 contours,
  seed 23 / intricacy 10 = 12,960, with drawn hatching inside and the engraved
  band outside.
- All eleven test modules pass after updating the motif-policy test (a busy
  drawing is now trimmed, not rejected); `docs_index --write/--check` pass.

## Struggles and rejected approaches

- Connected-component segmentation shattered the engravings: line art is many
  unconnected strokes, so an organism is not one blob. Gutter detection then
  collapsed each plate to a single block, and a plain grid picked up captions
  and margins. The working recipe is: drawing area first, overlapping grid
  second, density/spread filters last.
- Letting engravings fill every ring produced 143,832 contours and read as
  speckle. Restricting them to the outer two rings, plus the 90-stroke budget,
  brought it to a plottable 13-18k.
- The earlier silhouette library and my own mandala renders both stayed in
  scope for a while; the renders were moved out of `samples\png` and the
  silhouettes now sit beside the engravings as a second option.

## Risks and follow-up

- Crops are automatic, so some contain a caption fragment or cut an organism in
  half; the set is curated but not perfect, and `New selection` in the app lets
  the operator move past a bad one.
- Engraving motifs are still far denser than drawn shapes; the outer-band rule
  keeps that in check, but a `motif stroke budget` control would let the
  operator trade detail for plotting time.
- CC BY plates need `CREDITS.md` to travel with the images if they are
  redistributed.

## Files

- `tools/fetch_engraving_motifs.py`: plate downloader and cropper.
- `motifs/nature-engravings/` (88 PNGs, `CREDITS.md`, `manifest.json`),
  `motifs/README.md`.
- `software/qt_kaleidoscope.pyw`: motif stroke budget and rejection threshold.
- `software/converter_core/generative.py`: outer-band motif placement.
- `software/tests/test_preview_view.py`: updated motif policy test.
- `docs/project/ENGINEERING_LOG.md`: session evidence.
