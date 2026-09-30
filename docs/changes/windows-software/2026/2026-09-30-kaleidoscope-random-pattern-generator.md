---
id: WSW-20260930-006
date: 2026-09-30
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - generative
  - pattern-generator
  - interface
related:
  - WSW-20260930-005
  - software/README.md
---

# Kaleidoscope: deterministic random-pattern generator

## Summary

The Kaleidoscope Converter can now draw its own source artwork. Ticking
`Generate a random pattern instead of artwork` turns the Source group into a
generator: `Seed` (with a `New seed` button) selects a design and `Intricacy`
(1-10) controls how much of it there is. The generated mandala goes through the
same wedge clip, mirror, offset, auto-fit, preview and G-code path as an
imported image, so a seed plus the other controls always reproduces the same
program.

## Reason

The operator asked for a randomizer that "just spits out a random pattern into
the divisions", with an adjustable intricacy, randomised through mathematical
sequences rather than noise - and then asked for the output to be beautiful.
A scatter of independent motifs satisfies the first request but not the second:
beauty in a mirror kaleidoscope comes from concentric structure whose curves
span the sampled wedge, because only then do the mirrored copies join into
continuous rings.

## Implementation

- New `converter_core/generative.py`:
  - Sequence helpers: `van_der_corput`, `weyl`, `fibonacci`, `primes`, the
    golden angle and `WEYL_ALPHA`. Every count, radius and phase is derived from
    one of them, so a seed is reproducible and seeds differ in a controlled way.
  - Seven band families (`FAMILIES` / `_FUNCTIONS`): `scallop` (undulating
    full-span arcs), `petals` (closed leaf garlands), `wicker` (opposed sine
    arcs that braid), `rays` (tapered beams with bead tips), `beads` (jewel
    strings on a gentle wave), `chevron` (triangle teeth) and `spiral`
    (pinwheel arms). Each is called as
    `family(r_in, r_out, wedge, level, seed, cancel_check)` and returns
    contours in millimetres, y up.
  - `random_pattern(seed, intricacy, radius_mm, wedge_deg)` composes a central
    rosette, a geometric ladder of `2 + intricacy // 3` concentric bands and a
    double outer rim with rim beads at higher intricacy. Families are chosen per
    band by `(seed + 3 * band) % 7`, so adjacent bands always differ, and the
    detail counts only ever grow with `intricacy`.
  - Every band curve reaches both seam angles (angle 0 and angle `wedge_deg`,
    the wedge the caller clips to), which is what makes the mirrored seams read
    as continuous rings with mirrored cusps instead of broken fragments.
- `qt_kaleidoscope.pyw`: the Source group gained the mode checkbox, `Seed`,
  `New seed` and `Intricacy`. In pattern mode the artwork controls (open
  button, threshold, invert, trace detail) are disabled; the seed and intricacy
  rebuild like a division change, and `_source_contours` routes the generator
  output through the existing offset, fit, clip and mirror pipeline.
- `converter_core/__init__.py` re-exports the new module so both apps (and the
  tests) reach it through `converter_core`.

## Verification

- New `software/tests/test_generative.py` (8 tests): same seed reproduces the
  drawing, different seeds differ, higher intricacy adds contours and points
  without losing any, points are finite and inside the design radius, the
  clipped pattern stays inside its wedge and keeps over 80% of its points, the
  mirrored design contains no stray straight chords and no point beyond the
  frame, and each family stays inside its band and the wedge.
- All ten test modules pass.
- Headless Qt run: switching the mode on with no artwork loaded builds 384
  contours fitted to exactly 181.3 mm; raising intricacy 5 to 9 grows the design
  from 10,248 to 22,824 points; `New seed` changes the design; `Fit design to
  bounds` re-fits to 181.3 mm; saving emits 33,852 lines and 1,008 pen cycles.
- Visual checks: rendered 3x3 seed/intricacy grids and the offscreen app preview
  through the real `kaleidoscope()` mirror step (`samples/png/gen_grid3.png`,
  `gen_preview.png`).
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- The first draft scattered independent motifs (roses, stars, spirals) around
  the origin. Rendered through the mirror step it read as noisy rather than
  designed, so it was replaced by the banded composition above.
- The first banded render showed long straight chords cutting each wedge. The
  cause was a call-site bug: `_rosette` expects `(radius, wedge, ...)` and was
  passed the band edges instead, so the centre rosette became a five-turn ring
  drawn at exactly the clip radius, which the disc clipper chopped into chords.
  Found by scanning the mirrored output for two-point contours over 10 mm; the
  fix is the argument order, and the chord scan is now a regression test.
- Beads and the centre circles deliberately overhang a seam a little; clipping
  and mirroring completes them into full beads, so the band test allows that
  bleed instead of forbidding it.

## Risks and follow-up

- Intricacy 9-10 in a 12-division 181.3 mm frame is roughly 34k G-code lines;
  the operator controls that with the intricacy knob, and there is no
  line-count warning yet.
- Family geometry is composed for the current wedge, so changing `Divisions`
  changes the design rather than merely re-slicing it. That is intended, but it
  means a design is only reproducible with the same division count.
- The pattern is limited to seven families and one composition; adding more
  families or a "variation" knob stays open as a future enhancement.

## Files

- `software/converter_core/generative.py`: new generator module.
- `software/converter_core/__init__.py`: re-export it.
- `software/qt_kaleidoscope.pyw`: random-pattern source mode.
- `software/tests/test_generative.py`: determinism, wedge, band and chord tests.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`: current state and
  session evidence.
