---
id: WSW-20261126-013
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/geometry.py
  - software/converter_core/gcode.py
  - software/generator_tabs/cmyk_tab.py
  - tools/check_cmyk_wave_spacing.py
  - tools/make_cmyk_wave_coupon.py
  - samples/gcode/cmyk-variable-depth-wave-coupon.gcode
  - software/tests/test_cmyk_tab.py
  - software/tests/test_wave_x_theta_rows.py
  - software/tests/test_check_cmyk_wave_spacing.py
  - software/tests/test_cmyk_wave_coupon.py
tags:
  - cmyk
  - wave-screen
  - fixed-baselines
  - variable-depth
  - phase
  - frequency
  - clearance
  - row-lock
  - x-theta
  - manifest
related:
  - WSW-20261024-013
  - WSW-20261025-003
  - WSW-20261030-003
  - WSW-20261101-007
  - WSW-20261126-012
  - ADR-009
---

# Add variable-depth Wave with fixed row baselines

## Summary

Added the separate production style **Variable-depth Wave - fixed baselines**
(`waves_fixed`). Every row keeps the same equally spaced notebook-paper
baseline while local scene depth drives that row's amplitude, phase, and
winding rate. Visible instantaneous gaps may vary because rows do not share
one waveform, but rows may not touch, cross, or violate the pen envelope.

The style retains row-lock bed compensation and the explicit-row shared
rotating-bed A schedule. Set manifests now record the final fitted baseline
pitch and per-ink row grids. The final-coordinate checker understands both
fixed baseline spacing and variable row waveforms.

Added `cmyk-variable-depth-wave-coupon.gcode`, an ordinary-paper black-pen
comparison of XY-only and Xθ/Yθ at `3.36 mm` and `4.20 mm` pitch. It is ready
for the pending physical validation.

## Reason

`waves_even` preserves exact instantaneous row spacing by translating one
common waveform to every row. That prevents independent row depth and makes
all rows crest together. The legacy diagnostic restores row depth but applies
raw compensation and has no shared rotating-bed A schedule, so it is not a
production-safe combination.

The required model is different from both: fixed equal baselines, independent
row waveforms, compatible row-lock compensation, and a final machine-space
check. The existing manifest also recorded the tab-local pitch before the
global bed fit. A job advertised `1.21 mm` while emitting approximately
`2.129 mm` rows after a `1.76x` fit, so the checker searched for the wrong
scale even though the emitted rows were uniform to `0.00445 mm`.

## Implementation

- `screen_channel()` recognizes `waves_fixed` without changing the stored
  `waves_even` or legacy `waves_zero` paths.
- `_wave_rows()` keeps `row_i(x) = baseline_i + wave_i(x)`. Smoothed depth
  controls row amplitude and phase rate; a deterministic row phase plus the
  existing image-wide frequency modulation produces independent waveforms.
- The desired amplitude is bounded by the same-column half-pitch safety limit.
  The exact finite-segment check damps only an offending adjacent pair when a
  steep flank still violates the pen-plus-`0.25 mm` envelope.
- `WaveTrail` now carries a baseline point and row policy through SVG output,
  parsing, Y flip, artwork/pen scaling, offsets, clipping, planning, and
  overdraw. The final planner checks the scaled physical row clearance again.
- Fixed-baseline G-code records the final pitch, origin, row count, effective
  screen angle, and a per-contour row/baseline annotation. It retains the
  row-locked projection and shared-A headers.
- Set-manifest version 5 records the pre-fit tab pitch separately from the
  final measured baseline pitch, final fit scale, per-channel row grids, and
  `instantaneous_gap_semantics: varies_by_design`.
- The CMYK UI exposes the new production style, names the guard **Preserve
  fixed row baselines**, and passes it without the diagnostic override only
  when row-lock compensation and the required rotating-bed row order are
  active.
- The fixed-baseline path disables imported-outline pen-width shrink for its
  self-screened rows so the configured physical clearance is not narrowed.
- `check_cmyk_wave_spacing.py` keeps the `waves_even` adjacent-gap audit and
  adds a fixed-baseline audit that reads the final row annotations, verifies
  uniform baseline pitch, validates variable row envelopes and pen clearance,
  and accepts the manifest's intentional variable-gap semantics.
- `make_cmyk_wave_coupon.py --fixed-baseline` generates the new physical
  comparison program.

## Verification

- Unit regressions confirm zero depth collapses every row to its exact
  straight baseline, nonzero scene depth creates visibly different row
  amplitudes and winding rates, and `2.80/3.36/4.20 mm` remain clear at all
  four CMYK angles.
- `test_wave_x_theta_rows.py` exercises both row orders at all four screen
  angles with row-lock compensation and the shared A schedule. The emitted
  baseline residuals stay below `0.005 mm`, and the checker observes varied
  row wave ranges without adjacent-segment contact.
- The UI regressions cover the new selector label, green fixed-baseline state,
  red missing-guard/row-order states, final G-code header enforcement, and
  preservation of baseline metadata through pen offsets.
- A real-pipeline tab regression plans and saves all four inks, writes the
  version-5 manifest, and passes the final-coordinate checker.
- Manifest coverage verifies a pre-fit `1.21 mm` recipe records the final
  `2.129 mm` baseline pitch and `1.7595x` fit scale.
- `test_cmyk_wave_coupon.py` verifies the new one-file coupon contains both
  XY-only and Xθ/Yθ motion and passes the strict motion guard.
- The checked-in coupon passes `check_gcode_motion.py --strict`: 3,649 drawing
  moves, maximum drawing-bed step `1.77 deg`, peak A rate
  `500 motor deg/s`, no rotated pen-up `G0`, and worst bounded bed path bow
  `0.015 mm`.
- Complete converter discovery passes `662` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- The existing `waves_even` style cannot represent independent row depth; it
  was retained unchanged rather than silently reinterpreted.
- The legacy `waves_zero` path lacks row-lock compensation and the shared A
  schedule; promoting it in place would change saved recipes and still fail
  the production safety contract.
- A global amplitude reduction preserves clearance but flattens unrelated
  rows. The fixed-baseline mode uses a per-row slope bound and pair-local
  damping instead.
- Baseline metadata could not be inferred from final wavy paths after scaling.
  It is carried explicitly through transforms and emitted with each contour.
- The first final-clearance helper rejected multi-patch coupons that reuse row
  indices. It now detects those independent grids and leaves the combined
  coupon as a visual/motion test while production layers retain the hard gate.

## Risks and follow-up

- No physical print of the new coupon has been completed. Ink spread, machine
  following error, and bed/A behavior can still consume the nominal clearance.
- Xθ/Yθ shared schedules add G-code subdivisions; print time and file size must
  be measured on the physical coupon.
- Global Fit can change the final paper scale. The manifest and checker now use
  the emitted scale, but the operator must still choose a physically safe
  finished pitch for the installed pen.
- Existing `waves_even` recipes remain available and separate. The new visual
  depth is not claimed as equivalent to continuous-tone rendering.

## Files

- `software/converter_core/cmyk.py`: fixed-baseline waveform generation,
  row-local phase/frequency, and pairwise clearance damping.
- `software/converter_core/geometry.py`: baseline metadata through WaveTrail,
  SVG parsing, scaling, and transforms.
- `software/converter_core/gcode.py`: final row grid, clearance, G-code
  annotations, and header evidence.
- `software/generator_tabs/cmyk_tab.py`: production UI state, save preflight,
  and manifest version 5.
- `tools/check_cmyk_wave_spacing.py`: fixed-baseline final-coordinate audit.
- `tools/make_cmyk_wave_coupon.py`: new physical comparison coupon generator.
- `samples/gcode/cmyk-variable-depth-wave-coupon.gcode`: generated coupon.
- `software/tests/test_cmyk_tab.py`,
  `software/tests/test_wave_x_theta_rows.py`,
  `software/tests/test_check_cmyk_wave_spacing.py`,
  `software/tests/test_cmyk_wave_coupon.py`, and
  `software/tests/test_contour_order.py`: regression coverage.
- `software/README.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`,
  `docs/decisions/ADR-009-post-registration-bed-compensation.md`, and
  `docs/project/ROADMAP.md`: current behavior, interface, decision, and pending
  physical gate.
