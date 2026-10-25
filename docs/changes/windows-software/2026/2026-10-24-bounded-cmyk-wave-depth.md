---
id: WSW-20261024-009
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: superseded
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - wave-screen
  - depth
  - amplitude
  - row-spacing
  - overlap
related:
  - WSW-20261024-006
  - WSW-20261024-007
  - WSW-20261024-010
  - 2026-10-23-m-13-cmyk-yellow-feed-sensitivity
---

# Restore bounded CMYK wave-screen depth

## Summary

Wave-screen rows retain image-driven changes in wave height again, but adjacent
rows are limited to a small fraction of the configured pitch. This restores
the depth created by combined variable waves without allowing neighboring rows
to cross or spread into runaway gaps.

## Reason

`WSW-20261024-006` made every row use one shared amplitude profile to remove
overlap. The physical print confirmed that row spacing was fixed, but the
operator observed that the waves no longer varied enough to create depth.

The `1.2 mm` Dot pitch is not the cause. At `280 %` Artwork scale it produces a
`3.36 mm` on-paper pitch, and the previous shared profile removed vertical tone
variation regardless of pitch.

The per-channel depth field was superseded by `WSW-20261024-010`, which uses a
common scene-luminance field because an individual CMYK channel can remain
almost uniform across a large inked region.

## Implementation

- A seven-row moving average recovers broad local tone while suppressing
  pixel- and row-frequency noise.
- The smoothed tone changes each row's wave amplitude, restoring the tonal
  depth encoded by the image.
- Adjacent rows may change their vertical crest by at most `12 %` of nominal
  pitch. The resulting centerline gap remains between `88 %` and `112 %` of
  pitch for a shared sine phase.
- The sample-density and blank-image behavior from `WSW-20261024-007` remain
  unchanged.

## Verification

- A new vertical-gradient regression fails on the shared-amplitude version
  with effectively `0 mm` depth variation. The bounded-depth implementation
  restores approximately `0.89 mm` of amplitude range for a `4 mm` test pitch.
- All four CMYK screen angles keep adjacent visible gaps between `85 %` and
  `115 %` of pitch across row-frequency tone changes, with total spread below
  `30 %` of pitch.
- A second gradient regression verifies visible depth and the bounded envelope
  together.
- The path-tolerance and blank-image regressions continue to pass.
- `python -m unittest -v software.tests.test_cmyk_tab`: 72 tests pass.
- Full converter discovery passes 507 tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Keeping the entirely shared amplitude profile removed the intended visual
  depth.
- Returning to independent unsmoothed row amplitudes reproduces the crossing
  and wide-gap failure.
- Increasing Dot pitch would enlarge every wave but would not restore
  row-to-row tonal variation, and it would change spacing at the same time.

## Risks and follow-up

- Vertical tone detail narrower than the seven-row averaging window is
  deliberately suppressed to keep rows stable.
- A fresh full yellow print at `F700`, `$123=6000`, Dot pitch `1.2 mm`,
  Artwork scale `280 %`, and Path tolerance `0.05 mm` is required to judge the
  restored depth on paper.

## Files

- `software/converter_core/cmyk.py`: bounded seven-row depth field.
- `software/tests/test_cmyk_tab.py`: vertical-depth and bounded-gap tests.
- `software/README.md`: current Wave-screen behavior.
- `docs/report/lab-notes/2026-10-23-m-13-cmyk-yellow-feed-sensitivity.md`:
  physical result and next print.
- `docs/testing/TEST_PLAN.md`, `docs/project/ROADMAP.md`, and
  `docs/project/ENGINEERING_LOG.md`: current M-13 status.
