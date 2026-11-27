---
id: WSW-20261127-004
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/wave_rows.py
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - fixed-baselines
  - amplitude
  - wavelength
  - module-split
  - regression
related:
  - WSW-20261126-013
  - WSW-20261126-014
  - WSW-20261127-003
  - ADR-009
---

# Make fixed-baseline Wave amplitude proportional to wavelength

## Summary

**Variable-depth Wave - fixed baselines** now sizes its crest height from the
carrier wavelength instead of a fixed half-pitch. Full-tone crest height is
`min(pitch, 0.25 * wavelength)` times the Dot-size gain, so a long **Wave
period** still reads as a visible sinusoid rather than a near-straight line.
The shared nested phase carrier and the fixed equal row baselines are
unchanged.

As part of the change, the Wave screening machinery (constants, clearance
helpers, tone smoothing, and `_wave_rows`) was moved out of `cmyk.py` into
`wave_rows.py`, the module that already owns rotating-bed Wave scheduling.
`cmyk.py` re-exports those names, so existing importers are unaffected.

## Reason

The previous amplitude was `0.5 * pitch` for every period. At the shipped
default period (`2 x pitch`) that is an amplitude-to-wavelength ratio of
`0.25`, which is clearly wavy. The owner's unsuccessful manual pass raised
**Wave period** to `4 x pitch`, which doubled the wavelength while leaving the
crest at `0.5 * pitch` - a ratio of `0.125` that reads as straight lines, and
an ink-density (tortuosity) range of only about `1 + (A*k)^2 / 4 ~= 1.15`.
Depth intensity then had no perceptible amplitude to shape.

On the supplied source image at the failure-state settings (effective
`3.22 mm` pitch, period `4`), the old full-tone crest was `1.61 mm`; the new
full-tone crest is `3.22 mm`.

## Implementation

- Added `WAVE_AMPLITUDE_FRACTION = 0.25` in `wave_rows.py`.
- `_wave_rows` computes a fixed-baseline `wave_amplitude =
  min(spacing, wavelength * WAVE_AMPLITUDE_FRACTION) * amplitude_scale` and
  uses the true carrier wavenumber `2*pi/wavelength` for the path-tolerance
  sample-step bound, so longer periods keep the sine faceted within the
  configured path budget.
- The fixed-baseline branch keeps one shared `nested_phases` carrier and
  per-row amplitude `wave_amplitude * smoothed_tone`, preserving the existing
  clearance contract: rows that share a phase translate in parallel, so equal
  amplitude never changes the row gap.
- Non-fixed Wave modes keep the previous `0.5 * pitch` amplitude unchanged.
- Moved the Wave constants, `fixed_wave_minimum_pitch_mm`, `_local_frame`,
  clearance/segment helpers, tone smoothers, and `_wave_rows` from `cmyk.py`
  to `wave_rows.py`. `cmyk.py` imports them back for re-export, so
  `converter_core.cmyk.screen_channel` and external callers are unchanged.

## Verification

- The complete `software.tests.test_cmyk_tab` suite passes `135` tests,
  including the fixed-baseline zero-depth, nested-phase, period-control,
  depth-intensity, texture-ripple, and coverage-fragment regressions.
- `test_wave_x_theta_rows`, `test_check_cmyk_wave_spacing`, and
  `test_cmyk_wave_coupon` pass `19` tests; `test_shading` and
  `test_sine_gradient` pass `45` tests.
- On the source photo at the failure-state settings, per-row peak-to-peak
  amplitude for cyan/magenta/yellow is now about `6.4 mm` (full crest
  `3.22 mm`), twice the previous `1.61 mm` ceiling. Black rows remain flat
  only because the current GCR/tone chain yields `0-0.15` black coverage -
  a separation defect, not a geometry defect.
- The headless oracle (`tools/cmyk_wave_fidelity.py`) composite SSIM stays
  `~0.014` at the failure-state settings, confirming that geometry alone
  cannot correct the still-broken color separation; color fidelity is the
  separation workstream's responsibility.

## Struggles and rejected approaches

- A first mechanical module split left `fixed_wave_minimum_pitch_mm` behind in
  `cmyk.py` while `_wave_rows` (now in `wave_rows.py`) still called it. That
  is a runtime `NameError` for `waves_fixed`; the split was corrected to move
  the function with the constants it uses.
- Giving each fixed-baseline row an independent phase was rejected: it forces
  adjacent rows toward opposite crests and would reduce the safe amplitude to
  `(pitch - clearance) / 2`, which is near zero at tight pitch. The shared
  nested carrier is what permits large visible amplitude at a fixed baseline.
- Raising amplitude without rescaling the sample step would reintroduce sine
  facets; the curvature bound now uses the actual fixed-baseline amplitude
  and wavenumber.

## Risks and follow-up

- Larger amplitude means adjacent-row amplitude differences reach the
  clearance limit sooner at tone edges, where column-local damping still
  applies. Operators at tight pitch may need a larger Dot pitch or a smaller
  Period variation. A follow-up should make `fixed_wave_minimum_pitch_mm`
  account for the requested period/amplitude so Match pen recommends the
  truly safe pitch instead of only pen-plus-gap.
- The final physical coupon still must confirm ink spread and machine-following
  behavior; this change concerns software/G-code geometry only.

## Files

- `software/converter_core/wave_rows.py`: Wave machinery moved here, plus
  `WAVE_AMPLITUDE_FRACTION` and wavelength-proportional fixed-baseline
  amplitude.
- `software/converter_core/cmyk.py`: inline Wave machinery removed and
  re-exported from `wave_rows.py`.
- `software/README.md`, `docs/project/ROADMAP.md`,
  `docs/project/ENGINEERING_LOG.md`, and generated change indexes: current
  behavior and verification.
