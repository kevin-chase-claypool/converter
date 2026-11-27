---
id: WSW-20261127-003
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - fixed-baselines
  - depth-intensity
  - tone-smoothing
  - preview
  - regression
related:
  - WSW-20261126-013
  - WSW-20261126-014
  - ADR-009
---

# Make Wave depth intensity decisive without nested tone ripples

## Summary

**Variable-depth Wave - fixed baselines** now uses separate smoothed depth and
ink-presence fields plus a bounded smooth-step intensity curve.

- The depth field is smoothed along each row by `1.5` row pitches as well as
  across seven rows.
- Ink presence is smoothed independently by `2.5` row pitches along each row
  and across three rows before the visibility threshold is applied.
- `Depth intensity = 100 %` remains neutral.
- Values below `100 %` soften amplitude and period differences.
- Values above `100 %` make narrow light/dark differences increasingly
  decisive, reaching full smooth-step contrast at `200 %` and narrower
  thresholds through `300 %`.
- The mapping no longer clips broad tonal regions to 0/1 immediately and does
  not multiply tiny pixel-level residuals into large nested waves.
- Textured dark coverage no longer chops one designed carrier into repeated
  miniature waveforms.

## Reason

The preview showed a slow designed sine carrier with a smaller high-frequency
zigzag riding on top, especially in black. The depth field was vertically
smoothing rows but using raw along-row ink texture directly. That texture
modulated wave amplitude and phase at source-pixel frequency. Increasing Depth
intensity amplified the double-wave artifact.

The first correction smoothed only the depth source. The zoomed black preview
still broke rows wherever raw channel coverage crossed `INK_FLOOR`, producing a
sequence of short sinusoidal fragments that looked like waves inside each
larger wave. The visibility decision also needed its own pen-scale smoothing,
separate from the curve that controls amplitude and period.

At the same time, the previous centered linear intensity curve could either
clip broad areas or leave the remaining narrow light/dark tonal range too
close to the same waveform. The control therefore appeared ineffective even
though it changed the numeric field.

## Implementation

- Added a horizontal box smoother for the depth field. Its width follows the
  final row pitch, so changing physical scale keeps the smoothing scale.
- Added a separate smoothed presence field for the `INK_FLOOR` visibility
  decision. This field uses a wider `2.5`-pitch horizontal window and a
  three-row vertical window, preserving genuine blank regions while joining
  texture-induced gaps inside dark areas.
- Preserved the existing vertical row smoothing and all row baseline,
  clearance, compensation, and A-schedule contracts.
- Replaced the linear centered contrast mapping with a bounded smooth-step
  blend. The curve has a finite response around midtone and reaches a stronger,
  narrower threshold as intensity approaches `300 %`.
- `0 %` still collapses depth drive to its neutral value; `100 %` remains
  identity.
- Updated the control tooltip and current-state documentation.

## Verification

- A new textured-depth regression creates an intentional broad tone wave plus
  per-pixel black texture. Before smoothing, the resulting high-frequency
  ripple was `0.294 mm`; after the fix it is below `0.10 mm`.
- A coverage-texture regression alternates sub-floor and dark channel values
  pixel by pixel. The generated carrier must remain continuous across the dark
  region instead of fragmenting into repeated miniature waveforms.
- A fresh app preview at `2.00 mm` pitch, period `4`, period variation `40 %`,
  and Depth intensity `300 %` produced `142,387` moves in `3.7 s`. The
  black-only close-up showed a single smooth carrier, clear light/dark
  amplitude changes, and no second waveform riding on the carrier.
- A second regression applies a narrow `16 %` tonal difference at a
  `2.2 mm` row pitch. Maximum Depth intensity now produces more than `3.5x`
  the light/dark amplitude contrast of neutral intensity.
- The existing light-to-dark amplitude-contrast and preset/recipe forwarding
  regressions still pass.
- Focused generator, CMYK, registration, and rotating-row suites pass `193`
  tests with one expected OpenGL-context skip.
- Complete converter discovery passes `685` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- Applying a stronger pointwise power curve removed texture smoothing gains:
  near `0.5`, the curve amplified a minuscule residual into a visible ripple.
- Increasing only the slider maximum would preserve the nested-wave defect.
- Smoothing the final row path would alter the designed sine shape rather than
  removing the incorrect depth source.

## Risks and follow-up

- Aggressive intensity intentionally produces abrupt light/dark waveform
  changes. Operators may need to reduce **Period variation** if those changes
  become visually busy.
- Depth smoothing can merge details narrower than roughly `1.5` row pitches,
  and the separate presence field can bridge sub-pen-scale gaps up to roughly
  `2.5` pitches. That is desirable for scene depth and continuous strokes, but
  may reduce very small local tonal accents.
- Physical behavior still requires a sparse coupon print; software preview and
  G-code geometry do not validate ink spread.

## Files

- `software/converter_core/cmyk.py`: separate depth/presence smoothing and the
  bounded depth-intensity curve.
- `software/generator_tabs/cmyk_tab.py`: updated control explanation.
- `software/tests/test_cmyk_tab.py`: nested-ripple, coverage-fragment, and
  narrow-range contrast regressions.
- `software/README.md`, `docs/decisions/ADR-009-post-registration-bed-compensation.md`,
  `docs/project/ROADMAP.md`, `docs/project/ENGINEERING_LOG.md`, and generated
  change indexes: current behavior and verification.
