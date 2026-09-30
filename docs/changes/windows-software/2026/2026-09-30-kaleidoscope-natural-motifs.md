---
id: WSW-20260930-010
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - generative
  - motifs
  - raster
related:
  - WSW-20260930-009
  - software/README.md
---

# Kaleidoscope: natural PNG motifs as the source of pattern diversity

## Summary

The random pattern generator can now draw its shape rings from a folder of
black-and-white PNG/JPG silhouettes - leaves, shells, fish, feathers - instead
of the built-in families. The seed combines them: each ring draws from a pool of
one to three motifs, copies pick from that pool as they step around the ring,
a share overlay a smaller second motif to form hybrids, and every copy is
larger than its band and drifts so the shapes overlap. Separators, studs and the
rim stay drawn, so the result is still a mandala.

## Reason

The operator asked to "use natural (i.e. shapes in nature) black and white png
files to be the source of the diversity", then clarified that the seed should
"randomly combine" the shapes and that "shapes should overlap".

## Implementation

- `converter_core/generative.py`:
  - `random_pattern(..., motifs=[...])` accepts traced artworks. When they are
    present every shape ring is filled with motif copies and the drawn families
    are skipped; empty or missing entries fall back per ring.
  - `motif_plan(seed, intricacy, count)` returns a *pool* of motif indices per
    ring (1 + intricacy // 4 of them, capped by the folder size) built from the
    same seed-driven choices the generator uses, so a caller can trace exactly
    the motifs a design will place.
  - `_motif_ring` sizes every motif by `_radial_support` - how far the shape
    actually reaches along the outward direction - so a copy is guaranteed to
    cross its band edge whatever its rotation. Copies are 0.62-0.80 of the band
    height in radial reach with at most 0.10 of drift, packed 1.05-1.60 along
    the arc, so both radial and neighbour overlap are structural rather than
    accidental. `limit` and `floor` keep the spill inside the design radius and
    clear of the pole.
  - Motif mode uses fewer, thicker rings (`2 + intricacy // 3`) than the drawn
    mode, because a ring of small repeated shapes reads as texture while a ring
    of a few large ones reads as the shape.
  - A small centre motif is added at higher intricacy when the seed asks for it.
- `qt_kaleidoscope.pyw`:
  - `Motif folder...` collects the raster files in a folder, `Use natural
    motifs in patterns` switches the mode on, and the Source label and log show
    the count next to the seed and style.
  - Motifs are traced with the same threshold / invert / trace-detail controls
    as imported artwork and cached per file, mtime and setting; only the motifs
    in the current seed's pool are traced, so a large folder is not traced
    wholesale.

## Verification

- New tests in `software/tests/test_generative.py`: motifs replace the drawn
  rings, placed copies overlap into the next ring while staying inside the
  design radius and off the pole, the motif plan is deterministic and grows
  with intricacy, an all-empty motif list still produces a drawing, and the
  seed varies both the pool contents and the designs. All ten test modules
  pass.
- Headless app run with a three-file folder (leaf, shell, fish drawn as
  black-on-white PNGs): seeds 4/11/23 at intricacy 8 and 4/11/42 at intricacy
  10 build in 0.15-0.68 s with pools of one to three motifs per ring and
  2,400-6,408 mirrored contours.
- Visual check `samples/png/gen_motifs_overlap.png`: recognisable leaf, shell
  and fish copies overlapping across rings, with the melded hybrid copies the
  pool mixing produces.
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- Sizing motifs by their circumradius did not guarantee overlap: a wide shape
  turned across the band reaches sideways, so the overlap test measured nothing
  for some seeds. Scaling by the radial support fixed it, and the test now uses
  a shape whose tip points outward so the claim is unambiguous.
- The first motif pass packed so many small copies that the natural shapes read
  as texture. Motif mode now trades ring count and copy count for size.
- `test_empty_motifs_fall_back_to_the_drawn_families` originally compared two
  full designs with `assertEqual`. The designs genuinely differ (motif mode
  changes the ring count), and unittest then built a difflib report over a
  200 KB repr, which took minutes - mistaken for a hang. Tests now compare
  `_fingerprint` values or counts, and the test asserts what actually matters:
  an empty motif list must still produce a drawing, and a real motif must
  change it.

## Risks and follow-up

- Quality depends on the source images: thin or very detailed artwork takes
  longer to trace and can overwhelm a ring; trace detail and threshold are the
  controls, and the cache keyed on them grows with use.
- Motif mode changes the ring count, so a design is only reproducible with the
  same folder contents and the same tracing settings.
- Overlap is deliberate but not infinitely forgiving: at very large
  `Fit radius` values the spill is proportionally the same, but a user who
  wants separated shapes has no switch for that yet.

## Files

- `software/converter_core/generative.py`: motif API, radial-support sizing,
  pool mixing, hybrid overlays, motif-mode ring count.
- `software/qt_kaleidoscope.pyw`: motif folder picker, tracing cache, mode
  plumbing and log output.
- `software/tests/test_generative.py`: motif tests, fingerprint comparisons and
  the overlap guarantee.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
