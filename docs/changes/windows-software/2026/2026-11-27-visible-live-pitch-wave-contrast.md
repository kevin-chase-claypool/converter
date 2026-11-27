---
id: WSW-20261127-010
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/wave_rows.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_wave_rows_geometry.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - fidelity
  - live-pitch
  - contrast
  - row-thinning
  - clearance
  - visible-wave
related:
  - WSW-20261127-009
  - ADR-015
---

# Make live-pitch contrast waves visibly wavy

## Summary

`waves_fidelity` now preserves a visibly wavy edge at the owner's saved
`1.265 mm` final pitch instead of reducing it to nearly straight rows.
Per-row adjacent scene contrast still drives amplitude. Strong-contrast cells
retain alternating rows across a local three-cell band, creating enough
physical room for the spike while preserving the pen-plus-edge contract.

## Reason

The owner supplied a close-up of the saved recipe showing effectively straight
rows. The exact saved sidecar is:

- `waves_fidelity`
- `1.15 mm` pre-scale pitch / about `1.265 mm` final pitch
- `8 x` wave period
- `100 %` period variation
- `150 %` depth intensity
- `0.90 mm` pen
- `1.15 mm` centerline clearance

A live-pitch synthetic edge measured only `0.144 mm` median row peak-to-peak.
That matched the screenshot's almost-straight output. The row-local contrast
was correct, but the exact clearance machinery reduced nearly every row to
about `18-28 %` amplitude because:

1. keeping every adjacent row left only about `0.095 mm` nominal gap headroom;
2. an abrupt contrast pulse makes a steep local flank, reducing perpendicular
   row separation;
3. the fallback applied its scale across the whole image rather than creating
   room locally.

## Implementation

- Strong adjacent scene contrast remains sampled within one source pixel on
  each side of a row sample.
- A coarse cell with at least `38 %` contrast retains alternating rows in that
  cell and its immediate neighbours. This is a local row-thinning contract,
  not a global density reduction.
- Selected rows keep their local contrast amplitude. Neighboring rows that
  would collide are removed in that cell instead of forcing every row toward a
  straight line.
- The shared phase carrier remains; it is no longer incorrectly forced to
  carry one global contrast amplitude for every row.
- Run-boundary chords are tapered and excluded from the fidelity collision
  audit, preventing rotated artwork edges from damping the interior.
- Remaining clearance conflicts reduce only the participating rows. Exact
  pen-plus-edge clearance remains the final authority.
- The manifest records the row-local amplitude mode, contrast gain, zero floor,
  `2`-row contrast stride, `0.38` thinning threshold, and fidelity carrier
  scale.

## Verification

- The new live-recipe regression fails at `0.144 mm` and now passes at
  `0.485 mm` median peak-to-peak, with a required minimum of `0.45 mm`.
- The exact saved-sidecar oracle at `512 px` reports worst-region median
  amplitude `0.576 mm`, clearing its `0.50 mm` gate.
- `software.tests.test_wave_rows_geometry` passes `19 / 19`.
- The focused CMYK verification set passes `217` tests.
- Complete converter discovery passes `744` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- Simply increasing contrast gain did not survive the final clearance check.
- A local per-column bridge helped only marginally (`0.144 -> 0.282 mm`) and
  still left the rows visually muted.
- Keeping all adjacent rows while bypassing clearance reached about
  `0.88 mm`, but violated the pen envelope and was rejected.
- A global alternating-row rule produced strong waves but severely reduced
  CMYK coverage. The final rule thins only strong-contrast cells and their
  immediate neighbours.
- Smoothing the contrast flanks broadly reduced the collision but directly
  worked against the requested immediate response.

## Risks and follow-up

- Strong edges intentionally lose local row density because alternating rows
  are retained. Full-page CMYK coverage and color metrics regress relative to
  the muted continuous-row version; this is a visible-wave/detail tradeoff,
  not a solved composite-fidelity result.
- The saved-sidecar oracle still fails color, luminance, structure, and
  coverage gates. Physical ink spread and registration remain unverified.
- The app must be restarted or the image replanned after this core change;
  an already-open window retains the prior planner.

## Files

- `software/converter_core/wave_rows.py`: row-local contrast amplitude, local
  alternating-row thinning, boundary handling, and row-local clearance
  fallback.
- `software/converter_core/cmyk.py`: current Wave behavior documentation.
- `software/generator_tabs/cmyk_tab.py`: tooltip and manifest fields.
- `software/tests/test_wave_rows_geometry.py`: exact live-recipe visible-wave
  regression.
- `software/tests/test_cmyk_tab.py`: metadata and tooltip regressions.
- `software/README.md`, `docs/integration/INTERFACES.md`,
  `docs/decisions/ADR-015-cmyk-fidelity-wave-density.md`,
  `docs/project/ROADMAP.md`, and `docs/project/ENGINEERING_LOG.md`: current
  behavior, measurements, and unresolved risks.
