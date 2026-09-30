---
id: WSW-20260930-020
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - generative
  - style
related:
  - WSW-20260930-019
  - software/README.md
---

# Kaleidoscope: close the empty bands in motif patterns

## Summary

Motif patterns kept a white moat between the shape rings and before the rim in
every seed. Four layout rules were closing the disc: thin teardrop leaves left
wedges of blank paper beside them, ring gaps were 1.0-2.4 % of the radius,
the outer band stopped at 0.855-0.93 of the radius while the rim started at
0.94, and motif mode used only 3-5 thick rings instead of the drawn mode's 6-9.
Leaves are now fuller and doubled per wedge, gaps are 0.5-1.5 %, the outer
band reaches 0.90-0.948, motif mode uses the same ring ladder as the drawn
mode, and motif copies pack slightly tighter.

## Reason

"i really like the outer waves but i dont like how much empty space there is,
im seeing it in every seed" - with a screenshot of the app preview.

## Implementation

- `converter_core/generative.py`:
  - `_leaf_ring`: leaf power 0.45-1.05 becomes 0.32-0.77 (fuller profile, less
    white beside each leaf) and the two-leaves-per-wedge case rises from a
    third to about two thirds of seeds.
  - `random_pattern`: `gap` 1.0-2.4 % of the radius becomes 0.5-1.5 %; `outer`
    0.855-0.93 becomes 0.900-0.948 so the rim rings sit right behind the last
    band instead of leaving a moat.
  - Motif mode now uses `_ring_count` (the drawn mode's 6-9 rings) rather than
    `_motif_ring_count` (3-5 thick rings), so the disc is covered by bands.
  - Motif copies pack 0.85-1.25 instead of 0.75-1.10, so the outer waves
    overlap slightly instead of floating apart.
  - `motif_plan` returns one pool per ring with the inner rings empty (only the
    outer two carry motifs), and the centre-motif code picks the first
    non-empty pool - this also fixed an `IndexError` when the ring counts
    changed.

## Verification

- Three seeds at intricacy 7 with the engraving folder
  (`samples\preview\gen_fill4.png`): 19,824 / 25,032 / 18,384 mirrored contours,
  rings running from the rosette to the rim with no white moat in any of them.
- All eleven test modules pass, including the updated motif-plan test (the plan
  now has exactly two non-empty pools) and the family band tests (the fuller
  leaves still stay inside their bands).
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- Putting motifs in the outer *three* rings filled the gaps but tiled the
  engravings so densely that the design read as speckle (15,000-19,000
  contours of static). Two rings plus the layout changes keep it readable.
- Extending the drawn leaves by removing the ring gaps alone did not help; the
  moat came from several independent rules, not one.

## Risks and follow-up

- Level 7 with engravings is now 18,000-25,000 contours, roughly double the
  earlier motif designs; that is a longer plot in exchange for the fuller look.
- A dark engraving crop can still dominate its band (seed 11 in the sample);
  `New selection` re-draws the motif set.

## Files

- `software/converter_core/generative.py`: leaf fullness, gaps, outer band, ring
  ladder, packing, motif plan.
- `software/tests/test_generative.py`: motif-plan expectations.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
