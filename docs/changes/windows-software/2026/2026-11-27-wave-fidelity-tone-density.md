---
id: WSW-20261127-006
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/wave_rows.py
  - software/generator_tabs/cmyk_tab.py
  - tools/check_cmyk_wave_spacing.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_wave_rows_geometry.py
tags:
  - cmyk
  - wave-screen
  - fixed-baselines
  - tone-density
  - fidelity
  - dithering
  - clearance
  - manifest
related:
  - WSW-20261126-013
  - WSW-20261126-014
  - WSW-20261127-005
  - ADR-009
---

# Add tone-density fidelity to fixed-baseline Wave

## Summary

Added the production CMYK screen **Variable-depth Wave - fidelity (tone
density)** with stored value `waves_fidelity`. It keeps the existing fixed
candidate-row baseline lattice and Variable-depth Wave geometry, but
deterministically skips light candidate rows so separated per-ink coverage can
fall below the continuous-sine floor. Existing `waves_fixed` recipes retain
their prior geometry.

## Reason

At the owner's live pitch, `waves_fixed` retained a row anywhere channel
coverage exceeded the ink floor. Continuous rows imposed a roughly
pen-width/pitch coverage floor across most of the image, so cyan, magenta, and
black substantially overprinted their target tone even though the waveform
shape itself was visible. The fidelity oracle reproduced this with large
coverage bias and MAE failures.

## Implementation

- `screen_channel()` recognizes `waves_fidelity` as a fourth fixed-baseline
  production path without reinterpreting `waves_fixed`, `waves_even`, or the
  legacy diagnostic.
- Each ink computes a threshold from a stable bit-reversed row-index sequence
  keyed by the ink seed. The row is visible where its locally smoothed channel
  coverage exceeds a calibrated fraction of `threshold * pen/pitch`. The
  stroke-body calibration accounts for rasterized ink area below the nominal
  stroke rectangle and approximates the separated channel's target coverage
  while retaining every row in dark areas.
- Rows remain at `y0 + row_index * pitch`. Skipped candidates leave integer
  pitch multiples, so the baseline lattice, shared phase carrier, and final
  pen-plus-edge clearance contract stay intact.
- The amplitude envelope treats emitted rows as the active set. A skipped
  intermediate row can therefore leave the required extra geometric room
  between its visible neighbours without weakening the exact shortest-segment
  collision check.
- The UI treats the mode as production fixed-baseline Wave and records
  `fixed_baselines_tone_density`,
  `row_local_fixed_baseline_depth_and_tone_density`, and
  `varies_by_design_with_tone_density` in the set manifest.
- The final-coordinate checker accepts the new style, verifies emitted rows
  against the original uniform lattice, and validates clearance across the
  visible rows rather than requiring consecutive row indices.

## Verification

- Focused geometry suite: `11 / 11` pass, covering density tracking, light-row
  skipping, the original pitch lattice at all four ink angles, shared-phase
  crossing counts, no collisions, and monotone live-pitch depth intensity.
- Focused UI/checker tests: `4 / 4` pass, covering the selector label,
  production preflight, per-ink depth routing, and skipped-row lattice audit.
- Existing Wave spacing checker suite: `11 / 11` pass.
- A real four-ink fidelity save at the test page frame produced all four
  G-code files, manifest style `waves_fidelity`, and passed
  `check_cmyk_wave_spacing.py` for cyan, magenta, yellow, and black. Baseline
  residuals were at most `0.00086 mm`; visible row indices included gaps.
- The required unmodified `tools/cmyk_wave_fidelity.py --recipe live-failed`
  uses `waves_fixed` internally, so the fidelity candidate was scored by
  substituting `waves_fidelity` at its production screen call without editing
  the oracle. At 256 px it reduced failing checks from `16` to `11`.
- Coverage MAE changed cyan `0.3013 -> 0.1922`, magenta
  `0.2629 -> 0.2200`, yellow `0.2005 -> 0.2058`, and black
  `0.3451 -> 0.2170`. All per-region coverage-bias checks and correlation
  checks now pass.
- Depth-intensity median RMS delta increased from `0.00657` to `0.02278 mm`
  and the median ratio from `1.071` to `1.212`, but remains below the
  oracle's `0.05 mm` material-change gate.
- The full `software.tests.test_cmyk_tab` run was `139 / 140`; the sole
  failure was the pre-existing sharpening-gradient assertion, unchanged by
  this workstream.

## Struggles and rejected approaches

- A row-wide probability without conditioning on local coverage could not
  represent horizontal tone changes. The selected implementation uses one
  stable threshold per row and applies it to each smoothed channel cell, so
  light cells end a row while dark cells continue it without per-pixel random
  state.
- Applying the one-pitch amplitude envelope across skipped rows discarded the
  depth made possible by the gaps. The envelope now considers only emitted
  neighbours and their integer baseline separation.
- Increasing the base carrier amplitude globally was rejected because dark
  areas still have adjacent visible rows at tight pitch and the slope-reduced
  pen clearance remains authoritative.

## Risks and follow-up

- Fidelity remains software geometry and oracle evidence, not a physical print
  result. Ink spread, paper absorption, pressure, machine following error, and
  rotating-bed behavior still require a low-pitch coupon.
- The first oracle pass still failed coverage MAE by `0.0122-0.0400`, several
  colour limits, one regional wave-amplitude limit, and the depth-delta limit.
  The coarse-cell follow-up in `WSW-20261127-008` improved those results.
  Reaching every gate may require more than one stroke-width of effective ink,
  which the current single-pass screen cannot provide at the live pitch.
- Subsystem current-state documentation, generated indexes, the engineering
  log, roadmap, commit, and push remain for the coordinating workstream.

## Files

- `software/converter_core/wave_rows.py`: ordered row thresholds, visible-row
  amplitude envelope, and fidelity depth scaling.
- `software/converter_core/cmyk.py`: `waves_fidelity` routing and documentation.
- `software/generator_tabs/cmyk_tab.py`: production UI label, preflight,
  recipe routing, and manifest semantics.
- `tools/check_cmyk_wave_spacing.py`: skipped-row fixed-baseline acceptance.
- `software/tests/test_wave_rows_geometry.py`: density and safety regressions.
- `software/tests/test_cmyk_tab.py`: UI, preflight, checked-lattice, and
  per-ink routing regressions.
