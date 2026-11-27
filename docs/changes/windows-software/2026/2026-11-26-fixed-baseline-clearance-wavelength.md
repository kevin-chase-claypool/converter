---
id: WSW-20261126-014
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/geometry.py
  - software/converter_core/gcode.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_contour_order.py
tags:
  - cmyk
  - wave-screen
  - fixed-baselines
  - period
  - amplitude
  - depth
  - clearance
  - user-interface
  - regression
related:
  - WSW-20261126-013
  - ADR-009
---

# Control tonal Wave period while preserving fixed baselines

## Summary

Variable-depth Wave now exposes **Wave period** in row pitches and
**Period variation** in percent. The base period controls the overall cycle
width; local image depth shortens the period and increases amplitude in dark
areas, while light areas lengthen the period and flatten it. Equal row
baselines remain fixed.

Each ink now uses its own separated local coverage after GCR to drive that
waveform. Cyan, magenta, yellow, and black therefore have independent period
and amplitude structures that combine in the finished CMYK print.

The previous near-clearance fallback automatically stretched the period and
shared the carrier across rows, which made the waveform excessively broad and
removed the tonal period hierarchy. Clearance violations are now handled by
column-local damping so unaffected parts of each row keep their depth.

## Reason

At a `1.21 mm` effective pitch with a `0.90 mm` pen, the required centreline
clearance is `1.15 mm`. The generated yellow preview contained 2,167 rows with
only `0.002-0.060 mm` vertical range and a `0.041 mm` median: visually
straight lines even though the fixed-baseline mode and spacing guard were
active.

The first safety fallback capped amplitude to half the `0.06 mm` clearance
margin. After that was removed, whole-row pairwise damping still flattened
entire rows when local phases approached. The model needed a user-controlled
period and local-only safety correction.

## Implementation

- Added **Wave period** with a default of `2.0 x pitch` and range `0.5-12.0`
  row pitches.
- Added **Period variation** with a default of `60 %`. Dark rows shorten their
  period and deepen the wave; light rows lengthen it and flatten toward the
  baseline.
- The same depth controls amplitude and period. A `0 %` variation keeps a
  common period while amplitude still follows depth.
- Hidden shared-scene depth was replaced by each channel's own local tone.
  GCR therefore redistributes waveform depth between black and CMY instead of
  all four inks tracing one common image field.
- Clearance is enforced in two stages: a shortest-segment check for each
  adjacent pair, then column-local offset reduction only where rows actually
  approach. Whole-row damping remains a final fallback, not the primary path.
- Added a `0.02 mm` internal clearance target to absorb SVG/G-code
  quantization and rotating interpolation.
- The controls are persisted in the per-image CMYK recipe and version-5 set
  manifest, including final on-paper base period evidence.
- SVG row metadata and the fixed-baseline G-code header now record the selected
  period pitches and tonal period variation.
- Preflight warns when local clearance damping is strong enough to limit the
  configured depth, directing the operator to increase pitch or reduce period
  variation.
- An analytic minimum-pitch check rejects impossible period/clearance
  combinations before tone sampling. At the reported `1.21 mm` pitch this
  returns immediately instead of spending more than 150 seconds per layer and
  emitting straight lines.
- **Match pen** uses that same calculation, so it sets a Wave-safe effective
  pitch rather than only the bare pen-plus-gap minimum.

## Verification

- The period-control regression fails with the old API and now confirms that
  `1.5 x pitch` produces materially more cycles than `3.0 x pitch`.
- A dark-to-light depth regression confirms dark rows use a shorter period
  than light rows.
- At the screenshot geometry, the old build produced identical crossing
  counts for light and dark rows. The corrected build produces about `42-48`
  light-row crossings versus `60-65` dark-row crossings, while retaining
  fixed `1.21 mm` baselines and the required pen clearance.
- The fixed-baseline SVG test verifies that period and variation metadata
  survive serialization and artwork scaling.
- The real-pipeline Save regression verifies that period controls round-trip,
  reach the recipe and manifest, and appear in emitted G-code.
- A per-channel regression confirms each ink receives a distinct depth field,
  and a GCR regression confirms higher GCR moves depth from cyan coverage into
  black.
- The impossible screenshot configuration fails in under `0.5 s` before any
  row pass. A 300 mm layer at a safe pitch completes in about `1.8 s`.
- The focused CMYK, Xθ/Yθ, checker, coupon, and contour suites pass `156`
  tests.
- Complete converter discovery passes `669` tests with one expected OpenGL
  context skip.

## Struggles and rejected approaches

- Automatically stretching the period avoided collisions but caused the
  reported “WAAAAY too wide” waveform and erased the tonal period hierarchy.
- Capping amplitude from the clearance margin alone made every row nearly
  straight.
- Scaling both rows whenever any part approached flattened the complete row,
  including regions that had ample local clearance.
- Permanently sharing the carrier across rows preserved spacing but removed
  the requested dark-versus-light frequency depth.

## Risks and follow-up

- At very tight pitch, the requested period/amplitude combination is rejected
  with a clear minimum. Increasing Dot pitch, reducing Period variation, or
  reducing Dot size restores room for visible tonal depth.
- The final physical coupon must still confirm ink spread and machine-following
  behavior. Software geometry alone does not prove paper-level clearance.
- The source-space period is scaled by the final bed fit; the generated
  manifest records the final fitted base period.

## Files

- `software/converter_core/cmyk.py`: period controls, tonal frequency/amplitude,
  column-local clearance damping, and internal safety margin.
- `software/converter_core/geometry.py`: period metadata through WaveTrail and
  SVG serialization.
- `software/converter_core/gcode.py`: period evidence in the final G-code
  header and baseline grid.
- `software/generator_tabs/cmyk_tab.py`: controls, live period readout,
  per-channel depth routing, recipe/manifest persistence, Wave-safe Match pen,
  and clearance-limit warning.
- `software/tests/test_cmyk_tab.py`,
  `software/tests/test_contour_order.py`: period and serialization regressions.
- `software/README.md`, `docs/decisions/ADR-009-post-registration-bed-compensation.md`,
  `docs/project/ROADMAP.md`, `docs/project/ENGINEERING_LOG.md`, and generated
  change indexes: current behavior and verification.
