---
id: WSW-20260930-009
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - generative
  - pattern-generator
  - seeds
related:
  - WSW-20260930-008
  - software/README.md
---

# Kaleidoscope: seeds choose a design, not just its phases

## Summary

Different seeds used to draw the same skeleton with the textures swapped: the
ring count, band radii, centre, rim and densities were all fixed by the
intricacy level, so seeds looked like variations of one design. The seed now
controls the structure - a composition style, the ring count, the band-width
ladder, the centre/rim proportions, how tightly each layer packs its detail and
whether a shape repeats once or twice per wedge. Across seeds 0-9 at intricacy
8 the drawing volume now spans 6,524-14,287 wedge points (2.2x) with ten
distinct contour and point counts, and the name of the style is shown next to
the seed in the app.

## Reason

The operator reported that "the seeds are not unique enough. there needs to be
more diversity added to the seeds". The seed previously only shifted which of
eleven families landed in which ring, plus a few phases, so the designs shared
their whole layout.

## Implementation

- `converter_core/generative.py`:
  - New `STYLES` and `style_for(seed)`: `floral`, `geometric`, `woven`,
    `beaded` and `mixed`, each a pool of shape families. A seed draws from one
    pool and the ring order is a deterministic Fisher-Yates shuffle
    (`_shuffled`) instead of a fixed stride, so family sequences differ between
    seeds rather than rotating.
  - `_roll(seed, slot)` / `_pick` / `_density` supply well-mixed deterministic
    values per (seed, slot). They use a SplitMix-style integer finaliser rather
    than a Weyl sequence in the seed: a linear sequence advances by a fixed step
    and can only reach a few bins of any small choice, which was measurably
    starving some styles (an early survey hit only three of five).
  - Seed-driven structure: ring count (`3 + (2*level)//3` plus -1/0/+1), band
    ladder exponent (0.60-1.20, so band widths rebalance from rim-heavy to
    centre-heavy), centre fraction, gap fraction, outer radius fraction, rim
    scallop spacing and line count, starburst presence and spoke spacing,
    rosette depth, and per-family packing density (0.80-1.30).
  - Families gained seed-driven variety of their own: leaf and lens rings may
    repeat once or twice per wedge, barb fork rate, mesh slant direction, lace
    eye rows, scallop wave count (1-4), chevron inner rows and apex beads,
    feather spine position, tulip lobe split and bead placement.
  - Per-gap dressing is now one of plain / studs / dots / both, chosen per seed
    (and per gap for the mixed choice).
- `qt_kaleidoscope.pyw`: the source label and build log show the style, e.g.
  `seed 3, intricacy 9 (floral)`.

## Verification

- Seeds 0-9 at intricacy 8, 12 divisions, 181.3 mm: styles cover four of the
  five pools, contour counts span 258-585 and points 6,524-14,287, with ten
  distinct values in each - no two seeds share a weight.
- Level 10 across seeds 0-99 keeps the density floor: 351-509 wedge contours
  and 8,424-12,216 mirrored contours in the sampled set.
- New test `test_seeds_produce_structurally_different_designs` requires at least
  three styles, six distinct contour counts, six distinct point counts and a
  1.3x spread in drawing volume across eight seeds. All ten test modules pass.
- The stray-chord regression was refined again: deliberate slanted mesh strokes
  are also long two-point contours, so it now only flags a chord whose end sits
  on the clip frame while the other end is more than 5 mm inside it.
- Visual check: `samples/png/gen_seed_variety.png` (seeds 0-11 at intricacy 9)
  shows distinct layouts, centres, band profiles and weights.
- `python tools\docs_index.py --write` / `--check` pass.

## Struggles and rejected approaches

- The first seed-driven pass used a Weyl sequence directly in the seed for the
  choices. Because a Weyl sequence advances by a constant step, seeds 0-9
  landed in only three of five style bins. Replacing the choice function with a
  scrambled hash fixed the distribution without losing determinism.
- Seed-driven ring counts and band ladders make some seeds lighter than others,
  so the level-10 density floor in the test was lowered to 300 wedge contours /
  9,000 points / 8,000 mirrored contours, which the lightest sampled seed still
  clears.

## Risks and follow-up

- Two seeds can still pick the same style; the pools exist to make that
  acceptable rather than impossible. If more separation is wanted, the next
  lever is per-style rim and centre treatments.
- Structure variation means some seeds are noticeably heavier to plot than
  others at the same intricacy; the log reports the contour count but there is
  still no plot-time estimate.

## Files

- `software/converter_core/generative.py`: styles, scrambled seed choices,
  seed-driven structure and per-family variety.
- `software/qt_kaleidoscope.pyw`: style shown beside the seed.
- `software/tests/test_generative.py`: seed-diversity test and refined chord
  regression.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
