---
id: WSW-20261031-001
date: 2026-10-31
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - variable-frequency
  - phase-locked
  - row-spacing
  - banding
related:
  - WSW-20261030-003
  - ADR-009
---

# Phase-modulate the Wave carrier to break vertical banding

## Summary

The CMYK equidistant Wave screen now varies its carrier frequency smoothly
across the image. Every row still receives the same phase and vertical
displacement at a given X coordinate, preserving the exact row lattice while
breaking repeated vertical crest/trough columns.

## Reason

The previous carrier used one wavelength equal to twice the row pitch across
the complete image. Dark tone changed the common waveform depth, but every row
crest remained aligned vertically. That coherent periodicity can produce
visible stripe-like moiré even when row baselines are exactly spaced.

Independent per-row frequency or phase was rejected because it changes the
same-column offsets between neighboring rows and can cause row convergence.
The frequency instead varies only along the row coordinate and is shared by
all rows in that ink layer.

## Implementation

- Added a deterministic shared-phase frequency-modulated Wave carrier to
  `converter_core/cmyk.py`.
- Combined two smooth modulation periods to avoid a simple repeating frequency
  pattern. Default instantaneous-frequency variation is `18 %`.
- Kept the base wavelength tied to twice the effective row pitch and retained
  the common tone-driven amplitude profile.
- Increased path sampling density using the maximum instantaneous frequency so
  the existing `0.05 mm` chord-tolerance contract remains satisfied.
- Added **Vary Wave frequency across image (break banding)** to the CMYK Screen
  group, enabled by default and available only for Wave screen.
- Set manifests now record `wave_frequency_mode` and
  `wave_frequency_variation_pct`.

## Verification

A synthetic uniform-tone audit at `4 mm` row pitch and seed `7` measures:

- Constant carrier crest interval: `7.972 mm`.
- Variable carrier crest interval: `6.756-9.168 mm`.
- Adjacent row gaps at every sampled column: exactly `4.000000 mm`.
- Each row baseline remains fixed; no row-specific phase or vertical offset is
  introduced.

The focused CMYK tab suite passes `99` tests.

## Struggles and rejected approaches

The first all-color rotating-bed inspection compared cyan, magenta, and black
without rotating their reconstructed bed paths into the effective screen
frame. That produced false spacing failures. After applying the screen-angle
transform, all four planned layers passed:

- Cyan spread: `0.001961 mm`
- Magenta spread: `0.002683 mm`
- Yellow spread: `0.000280 mm`
- Black spread: `0.001614 mm`

That result establishes that fixed-frequency Wave banding is a separate issue
from the row-spacing invariant.

## Risks and follow-up

The modulation is deliberately shared across rows, so it cannot alter
row-to-row centerline spacing by construction. Physical banding may also have
motion or pen-pressure causes; only a comparison coupon can determine how much
the new carrier removes.

## Files

- `software/converter_core/cmyk.py`: phase-modulated shared Wave carrier.
- `software/generator_tabs/cmyk_tab.py`: Wave-only control and manifest data.
- `software/tests/test_cmyk_tab.py`: frequency variation, pitch, dark-tone, and
  manifest regressions.
- `software/README.md`: current operator controls and behavior.
- `docs/testing/TEST_PLAN.md`: measurement method and acceptance criteria.
- `docs/project/ROADMAP.md`: current banding investigation status.
- `docs/project/ENGINEERING_LOG.md`: implementation and verification event.
