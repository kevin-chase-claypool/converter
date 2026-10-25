---
id: WSW-20261024-010
date: 2026-10-24
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
  - depth
  - luminance
  - amplitude
related:
  - WSW-20261024-009
  - WSW-20261024-007
  - 2026-10-23-m-13-cmyk-yellow-feed-sensitivity
---

# Drive CMYK wave depth from scene luminance

## Summary

CMYK Wave-screen amplitude now follows the shared scene luminance instead of
each ink channel's coverage. Ink coverage still controls where that layer draws,
but broad image shading again creates visible depth even when an individual
separation channel is locally flat.

## Reason

The first bounded-density print had stable spacing but remained visually
monotonous. The operator correctly identified that the individual waves hardly
varied, which removed the combined-wave depth that defines the pattern.

The bounded-depth implementation was using each C/M/Y/K channel as both its ink
mask and its amplitude source. For the Ben1 source at 1600 px, the 5th-95th
percentile span was `0.414` for magenta and `0.798` for yellow, while scene
luminance had a `0.776` common span. Similar or flatter channel values across a
large inked area therefore produced nearly uniform wave heights.

The bounded-depth print also showed one locally tight pair in the first magenta
contour. Decoding its machine path back through bed rotation and compensation
matched the generated source to within `0.00006 mm`, so this was source
geometry rather than an A-axis or pen-engage error. The luminance change does
not remove the bounded-spacing tradeoff; no-touch remains a physical acceptance
criterion.

## Implementation

- `prepare_image_tones` returns a `depth` field derived from processed scene
  luminance.
- `screen_channel` accepts an optional `depth_tone` field for wave amplitude
  while retaining the channel tone only as the ink-presence mask.
- The CMYK tab supplies the common luminance field to all four ink layers.
- The existing seven-row smoothing and `12 %` adjacent-gap limit remain, so
  stronger depth does not restore the original unbounded crossings.
- Other screening styles and calibration-sheet calls do not change.

## Verification

- A separate-field regression confirms an ink mask can remain completely
  uniform while a luminance gradient still changes wave amplitude.
- An image-processing regression confirms the luminance depth field varies
  even when one CMYK channel has zero range.
- A CMYK integration regression confirms all four wave layers receive the
  luminance field.
- Focused wave-depth, bounded-spacing, smooth-chord, and blank-region tests
  pass.
- `python -m unittest -v software.tests.test_cmyk_tab`: 74 tests pass.
- Full converter discovery passes 509 tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Using one shared amplitude profile removed all vertical depth.
- Using each ink channel independently restored more apparent variation but
  produced crossings and extra-wide gaps.
- Raising Dot pitch would scale the whole wave without adding tonal contrast.
- Returning to unsmoothed per-row amplitudes would reintroduce the original
  failure.

## Risks and follow-up

- Scene luminance is a common depth signal, not an independent tone value for
  each ink. This is intentional: it keeps the four layers visually coherent and
  avoids assuming that a saturated colour plate is a dark value.
- Bounded amplitude variation can still bring differently clipped portions of
  nearby rows visually close. Verify actual ink-edge clearance, not only
  centerline spacing, on the next print.
- A fresh yellow and magenta print is required to judge the stronger depth and
  the bounded row spacing together.

## Files

- `software/converter_core/cmyk.py`: luminance field and shared depth sampler.
- `software/generator_tabs/cmyk_tab.py`: supplies depth to all four layers.
- `software/tests/test_cmyk_tab.py`: separate-field and integration tests.
- `software/README.md`: current Wave-screen behavior.
- `docs/report/lab-notes/2026-10-23-m-13-cmyk-yellow-feed-sensitivity.md`:
  physical observation and next print.
- `docs/testing/TEST_PLAN.md`, `docs/project/ROADMAP.md`, and
  `docs/project/ENGINEERING_LOG.md`: current M-13 status.
