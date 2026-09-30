---
id: WSW-20260930-014
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
  - WSW-20260930-013
  - motifs/README.md
---

# Realistic nature motifs and deeper motif rings

## Summary

`motifs/nature/` now holds 150 real organism silhouettes from PhyloPic - birds,
cats, elephants, fish, dolphins, spiders, ants, jellyfish, butterflies, crabs,
tortoises and plants - each with taxon, contributor and licence recorded in
`CREDITS.md` / `manifest.json`. The earlier code-drawn set moved to
`motifs/nature-drawn/`. In motif mode each shape is now drawn at full size with
two smaller nested copies inside it, so the outlines read like the hatching
inside an engraved leaf rather than a flat cut-out.

## Reason

The operator rejected the drawn set ("these are not 'natural' pngs i meant
realistic things from nature. so good pngs") and re-stated the goal: a design
"akin to the complexity of this and as beautiful with natural shapes", pointing
at the 9,045-path reference mandala.

## Implementation

- `tools/fetch_phylopic_motifs.py` (new): samples PhyloPic's index, keeps only
  CC0 / public domain / CC BY / CC BY-SA images, downloads the vector file,
  rasterises it with Qt (`QSvgRenderer`), trims it to the subject, squares it
  with a margin and writes a 512 px 1-bit black-on-white PNG. It writes
  `manifest.json` and `CREDITS.md` for attribution.
- `tools/fetch_nature_motifs.py` (new, Wikimedia Commons route): searches
  silhouette categories and pressed-leaf collections, keeps only images with a
  clean light border, thresholds with Otsu, keeps the largest connected
  component (so labels and rulers are dropped), and writes the same outputs.
  Commons throttles bulk downloads, so it is throttled with backoff.
- `motifs/nature/` = 150 PhyloPic silhouettes; `motifs/nature-drawn/` = the
  earlier 110 code-drawn shapes (`git mv`, history preserved).
- `converter_core/generative.py`, motif mode:
  - each motif copy now carries up to two nested copies from the ring's pool at
    0.70 and 0.46 scale, with a small rotation each, which is what makes a real
    outline read as engraved shading;
  - copies per ring dropped from up to six to at most three with a packing
    factor of 0.75-1.10, so shapes stay large and legible;
  - the separator bundle uses `level // 4` lines in motif mode and the
    concentric shading-band experiment was removed - it turned gaps into heavy
    black rings that swallowed the shapes.

## Verification

- `tools/fetch_phylopic_motifs.py --limit 150 --pages 60` produced 150 motifs
  from a spread of PhyloPic pages; the contact sheet
  `samples/png/phylopic_all.png` was reviewed, and all entries are recognisable
  organisms.
- Motif designs rendered through the app path: `samples/png/gen_real_motifs3.png`
  (seed 7 / intricacy 9 and seed 12 / intricacy 10) shows nested animal and
  plant outlines in concentric rings with thin separators and stud rows -
  3,744 and 4,248 mirrored contours.
- All eleven test modules pass, including the motif tests (replacement,
  overlap inside bounds, deterministic pools, empty-list fallback, seed
  variation); `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- The first Commons attempt downloaded human silhouettes, carvings and photos
  with dark skies: keyword search is not enough. The fix was to restrict to
  silhouette categories and pressed-leaf collections and to reject anything
  whose border is not a clean light backdrop.
- PhyloPic serves white-on-transparent vector art; the first conversion shipped
  white-on-black PNGs because the threshold step inverted the polarity. The app
  traces dark pixels, so black-on-white is required.
- Two attempts at adding density made things worse and were removed: a
  concentric shading band per gap painted heavy black rings, and up to six
  overlapping copies per ring turned the animals into texture.
- Wikimedia rate-limited the first bulk run (HTTP 429); the Commons tool now
  throttles, backs off and accepts a candidate budget, and the shipping set came
  from PhyloPic instead.

## Risks and follow-up

- PhyloPic is animal-heavy: plants, shells and flowers are thin on the ground.
  The Commons tool can top those up when its rate limits allow.
- Shapes are still scaled to their band, so a very wide animal in a thin ring
  becomes squat; a `Motif scale` control is the next useful knob.
- Licences are recorded per file, but credit lines are only in
  `motifs/nature/CREDITS.md`; anything CC BY that is redistributed separately
  needs that file to travel with it.

## Files

- `tools/fetch_phylopic_motifs.py`, `tools/fetch_nature_motifs.py`: downloaders.
- `motifs/nature/` (150 PNGs + `CREDITS.md` + `manifest.json`),
  `motifs/nature-drawn/` (the moved set), `motifs/README.md`.
- `software/converter_core/generative.py`: nested motif copies, packing and
  separator changes.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
