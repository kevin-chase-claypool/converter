---
id: WSW-20261007-021
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - rectilinear
  - bugfix
related:
  - WSW-20261007-020
---

# Fix rectilinear stitching on multi-dash rows

## Summary

The rectilinear stitcher only compared the previous row's *last* dash with
the next row's current dash, so any row that broke into several dashes -
every photo row - almost never joined: on two sample images the rectilinear
screen produced as many polylines as the plain line screen (396/429), so no
serpentine appeared in the preview. The stitcher now keeps every chain open
through the row and matches each dash to the best-overlapping chain of the
previous row (at most one run per chain per row, chains close when a row
does not continue them), with the connector still required to be over ink.
The same sample images now produce 203/214 polylines with chains of up to
~1800 points, and smooth content chains completely (the new test's
wave-tone map goes from 24 line runs to one chain).

## Reason

Owner: "something is wrong and making the serpentine nature of rectilinear
not occur. it seems to be the case with each of the colors."

## Implementation

- `software/converter_core/cmyk.py`: `_stitch_runs` rewritten as a row-wise
  matching pass - candidates are the open chains whose previous run
  overlaps the dash in local x, sorted by overlap, joined when the
  connector midpoint samples at or above the run threshold; uncontinued
  chains close at the end of each row.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 384
  tests (1 skipped: the pre-existing headless shader compile). New
  regression test: a wave-tone map (photo-like smooth variation) chains
  rectilinear rows into far fewer, longer polylines than the line screen.
- Deterministic repro: `samples/png/Untitled.png` 396 -> 203 polylines,
  `samples/svg/fill2.jpg` 429 -> 214, longest chains 1832/1586 points.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Allowing joins between dashes that merely come close was tried and
  measured zero benefit: a dash break is caused by sub-threshold tone, and
  the connector's ink check rejects the straight hop across it anyway, so
  the extra rule was removed.

## Risks and follow-up

- Chains still break at genuine near-white gaps by design; the serpentine
  covers contiguous inked regions, not paper.

## Files

- `software/converter_core/cmyk.py`: row-wise chain matching.
- `software/tests/test_cmyk_tab.py`: photo-like chaining regression test.
