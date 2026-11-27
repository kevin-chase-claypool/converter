---
id: WSW-20261126-014
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - fixed-baselines
  - clearance
  - wavelength
  - preview
  - regression
related:
  - WSW-20261126-013
  - ADR-009
---

# Keep visible fixed-baseline waves near pen clearance

## Summary

Fixed-baseline variable-depth rows no longer collapse into a near-straight
hatch when the selected pitch is only slightly above the pen plus edge-gap
clearance. The waveform now uses the available margin to stretch its
wavelength and control row-to-row phase divergence before the exact pen
clearance limiter is applied.

## Reason

At a `1.21 mm` effective pitch with a `0.90 mm` pen, the required centreline
clearance is `1.15 mm`. The generated yellow preview contained 2,167 wave rows
with only `0.002-0.060 mm` vertical range and a `0.041 mm` median: visually
straight lines even though the fixed-baseline mode and spacing guard were
active.

Two safety mechanisms were responsible. The amplitude was capped at half the
remaining clearance, allowing only `0.03 mm` of displacement. Removing that
cap alone was insufficient because the short two-pitch wavelength made steep
row segments approach each other in Euclidean distance, causing the pair
limiter to damp entire rows.

## Implementation

- Removed the blanket half-clearance amplitude cap.
- Accepted the full amplitude produced by scene depth and the configured wave
  scale, while retaining the exact shortest-segment pen-envelope check.
- Stretched the fixed-baseline wavelength when clearance is tight, based on
  the maximum local amplitude and the geometric slope that still preserves
  the required Euclidean separation.
- Reduced independent row phase and tone-driven frequency divergence near the
  clearance limit. Rows then express depth primarily through amplitude; broad
  independent phase/frequency returns as clearance headroom increases.
- Added a `0.02 mm` internal search target over the published pen clearance to
  absorb SVG/G-code quantization and rotating interpolation.
- Retained pairwise row damping as the final local safety fallback.

## Verification

- The new regression at `1.21 mm` pitch, `0.90 mm` pen, and `1.15 mm`
  clearance failed before the fix with a median row range of `0.0345 mm`.
- After the fix, the same deterministic case measures a `0.6965 mm` median
  row range with no row-scale reduction.
- The focused CMYK, Xθ/Yθ, final-coordinate checker, coupon, and contour-order
  suites pass `150` tests.
- Complete converter discovery passes `663` tests with one expected OpenGL
  context skip.

## Struggles and rejected approaches

- The first attempted fix merely removed the amplitude cap. Independent row
  phases then forced the pair limiter to reduce safe rows to roughly
  `0.02-0.04 mm`, leaving the same straight-line symptom.
- Replacing independent phases with a permanently shared carrier restored
  visible rows but discarded the requested row-local frequency behavior even
  when physical clearance allowed it.
- Keeping the original two-pitch wavelength ignored that steep, adjacent wave
  chords can have a shorter Euclidean distance than their vertical baseline
  separation.
- Holding a fixed global amplitude budget was rejected because it repeats the
  earlier failure mode where one strict area flattens unrelated regions.

## Risks and follow-up

- Near the pen-clearance limit, the visible waveforms are intentionally
  broader and more phase-aligned than at wider pitch. This is a geometric
  safety consequence, not a return to equidistant rows.
- Physical ink spread and machine-following error still require the pending
  `cmyk-variable-depth-wave-coupon.gcode` print.
- The wavelength is selected in source space before the final global bed fit;
  the final-coordinate checker remains authoritative for emitted geometry.

## Files

- `software/converter_core/cmyk.py`: clearance-aware wavelength, phase blend,
  internal safety margin, and full visible amplitude.
- `software/tests/test_cmyk_tab.py`: screenshot-geometry regression.
- `software/README.md`: current fixed-baseline Wave behavior.
- `docs/decisions/ADR-009-post-registration-bed-compensation.md`: updated
  near-clearance decision consequence.
- `docs/project/ROADMAP.md`, `docs/project/ENGINEERING_LOG.md`, and generated
  change indexes: implementation and verification status.
