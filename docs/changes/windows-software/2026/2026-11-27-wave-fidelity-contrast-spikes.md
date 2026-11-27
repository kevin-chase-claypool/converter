---
id: WSW-20261127-009
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/wave_rows.py
  - software/generator_tabs/cmyk_tab.py
  - tools/cmyk_wave_fidelity.py
  - software/tests/test_wave_rows_geometry.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_wave_fidelity.py
tags:
  - cmyk
  - wave-screen
  - fidelity
  - local-contrast
  - edge-spike
  - source-pixel-sampling
  - clearance
related:
  - WSW-20261127-006
  - WSW-20261127-008
  - ADR-015
---

# Make fidelity Wave amplitude follow immediate local contrast

## Summary

`waves_fidelity` now derives waveform amplitude from immediate adjacent
scene-lightness contrast instead of a spatially smoothed absolute-tone field.
Uniform areas remain flat. A narrow edge creates a narrow amplitude spike whose
height scales with the light/dark difference. Absolute per-ink tone remains a
separate field that controls row density.

## Reason

The owner described the intended screen in physical terms: college-ruled rows
crossing the image should flatten over a uniform white area, spike abruptly
when they cross a dark perpendicular line, and immediately return to flat after
the line. Amplitude is a function of the difference between local lightness or
darkness and its immediate neighbour.

The previous fidelity path deliberately smoothed depth along `1.5` row pitches
and across seven rows, then added a `0.8` amplitude floor. A thin facial or
mustache edge therefore became a gradual tone change. A synthetic white field
with one narrow dark stripe had about `1.81 mm` of background peak-to-peak
motion before the fix, so the intended spike could not stand alone.

## Implementation

- `waves_fidelity` passes shared scene luminance as its depth source. The
  separated per-channel arrays continue to control absolute row density, so a
  hue edge does not create unrelated amplitude patterns in every plate.
- The fidelity depth source is sampled one source pixel to either side of every
  normal carrier sample. The local min/max difference captures a one-pixel edge
  even when it falls between the usual output samples.
- The contrast field is not box-smoothed. A small `2.5 %` dead band suppresses
  compression and paper-texture noise while preserving the remaining
  proportional response.
- A gain of `4.0` scales ordinary photo differences toward visible movement.
  There is no nonzero amplitude floor: uniform tone produces zero amplitude.
- `Depth intensity` scales this contrast response. Fixed-baseline
  `waves_fixed` keeps its previous smoothed channel-depth behavior.
- The shared phase carrier, fixed row baselines, per-column envelope,
  edge-aware density cells, slope cap, and final shortest-segment clearance
  check remain authoritative. The fidelity envelope uses an additional local
  margin and a final amplitude-scale fallback only if exact clearance still
  fails.
- The set manifest records
  `wave_amplitude_mode: shared_luminance_adjacent_contrast`, the contrast gain,
  and the zero amplitude floor.
- The objective oracle now routes `waves_fidelity` through the same shared
  scene-depth input as the production tab rather than the obsolete per-channel
  depth route.

## Verification

- The new stripe regression requires a flat background below `0.05 mm`.
  After the change, the median background motion is `0.004 mm` and the median
  stripe response is `0.971 mm`.
- A second regression requires the amplitude response to a `40 %` light/dark
  difference to be more than `2.5x` the response to a `10 %` difference.
- A one-source-pixel line regression requires a median spike above `0.08 mm`;
  it fails at `0 mm` without the source-pixel window and passes with it.
- Existing fidelity tests continue to cover all four screen angles, shared
  phase, fixed row indices, the pen-plus-edge contract, density gating,
  minimum run length, zero-depth collapse, and live-pitch intensity behavior.
- `software.tests.test_wave_rows_geometry` passes `18 / 18`.
- `software.tests.test_cmyk_tab` passes `142 / 142`.
- `software.tests.test_cmyk_wave_fidelity` passes `20 / 20`.
- Complete converter discovery passes `743` tests with one expected
  OpenGL-context skip.
- The live-failed recipe at a `256 px` render remains a red oracle baseline.
  The amplitude behavior is corrected, but color/coverage gates and the
  regional amplitude/depth gates remain open. The final run completed in about
  `19 s` with the bounded source-pixel window rather than the roughly `79 s`
  cost of inserting every detected edge as a new output sample.

## Struggles and rejected approaches

- Removing all spatial smoothing while retaining the old `0.8` floor still
  left uniform fields wavy. The floor was removed for fidelity mode.
- Using per-channel tone as the fidelity amplitude source produced
  channel-dependent noise and made the four plates less coherent. Shared scene
  luminance now drives contrast, while per-channel coverage drives density.
- Adding every fine-sampled edge to a global output lattice preserved the
  one-pixel test but expanded the portrait pass to roughly `79 s` and weakened
  the composite. A local source-pixel window retained the test without
  multiplying output samples.
- Increasing the gain to `8.0` saturated moderate differences and broke the
  proportional-height regression. The gain remains `4.0`.

## Risks and follow-up

- The corrected local-spike response is not yet reflected by sufficient
  composite-fidelity gains. Current RGB/lightness/edge metrics did not improve
  over the prior fidelity integration, and the live oracle still has color,
  coverage, depth-delta, and regional wave gates open.
- Strong edges can ask for more amplitude than the pen envelope permits at the
  live tight pitch. The exact clearance gate remains authoritative and may cap
  some spikes.
- A physical coupon is still required to show whether the abrupt amplitude
  pulses read as intended through pen width, ink spread, pressure, paper
  absorption, and rotating-bed following error.

## Files

- `software/converter_core/wave_rows.py`: local source-pixel contrast window,
  zero-floor dependency fidelity amplitude, clearance envelope, and
  source-resolution tests support.
- `software/converter_core/cmyk.py`: production source-pixel size forwarding
  and current-mode documentation.
- `software/generator_tabs/cmyk_tab.py`: shared-luminance route, tooltip, and
  manifest amplitude semantics.
- `tools/cmyk_wave_fidelity.py`: oracle parity with the production fidelity
  depth source.
- `software/tests/test_wave_rows_geometry.py`: narrow-stripe, proportional
  spike, and one-pixel edge regressions.
- `software/tests/test_cmyk_tab.py`: routing and manifest regressions.
- `software/tests/test_cmyk_wave_fidelity.py`: oracle routing regression.
- `software/README.md`, `docs/integration/INTERFACES.md`,
  `docs/decisions/ADR-015-cmyk-fidelity-wave-density.md`,
  `docs/project/ROADMAP.md`, and `docs/project/ENGINEERING_LOG.md`: current
  behavior, verification, and unresolved fidelity gaps.
