---
id: WSW-20261024-006
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: superseded
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - wave-screen
  - row-spacing
  - overlap
  - parallel
  - amplitude
  - all-inks
related:
  - WSW-20261024-004
  - WSW-20261024-005
  - WSW-20261024-009
  - 2026-10-23-m-13-cmyk-yellow-feed-sensitivity
---

# Keep all CMYK wave rows on one shared waveform

## Summary

Wave-screen rows now use one common sinusoidal amplitude profile at each
horizontal position. Adjacent rows cannot move toward each other and overlap
or spread apart into wider gaps because image tone no longer changes their
vertical displacement independently.

## Reason

The complete yellow print reproduced the large bands and diagonal omissions
already visible in the rendered source SVG. Hardware tests also showed that
large pen-down A rotation and `$123=600` acceleration did not reproduce the
original pattern in controlled wave patches.

The remaining defect is the Wave screen's geometric construction. Row-specific
tone controls amplitude, so neighboring rows follow different curves. Smoothing
those values reduced but did not eliminate convergence and divergence.

The fully shared profile was superseded by `WSW-20261024-009`: it fixed
crossings and runaway gaps, but also removed the vertical tone variation that
creates the Wave screen's visual depth.

## Implementation

- `_wave_rows` keeps the local row tone only as an ink-presence mask.
- Vertical displacement uses the mean tone for each horizontal sample across
  all wave rows; every row shares that amplitude profile.
- Blank image regions still split or omit marks, so image boundaries remain.
- Wave screen no longer represents vertical tone through row-to-row height
  differences. This is required for a constant visible gap.

## Verification

- A failing regression reproduced `0.87 mm` amplitude variation between rows
  under a vertical tone gradient. The new shared profile keeps variation below
  `0.01 mm`.
- The all-angle row-spacing regression still covers the four CMYK screen
  angles and requires less than `0.15 mm` adjacent-gap variation.
- A blank-band regression confirms waves still stop over empty image regions.
- Full converter discovery passes 503 tests with one OpenGL-context skip.
- The first full yellow print from this implementation was materially better:
  the catastrophic overlap and wide-gap pattern was gone and rows remained
  parallel. Individual waves were still visibly faceted, which led to
  `WSW-20261024-007`.

## Struggles and rejected approaches

- Four-row tone smoothing plus a slew limit (`WSW-20261024-004`) reduced but
  could not remove convergence and overlap.
- The one-sheet parked/rotating matrix (`WSW-20261024-005`) reproduced the
  source waveform cleanly at `$123=6000` and `$123=600`, including large
  pen-down rotations. This isolated the remaining appearance to the generated
  pattern rather than motion.
- Keeping any row-specific amplitude was rejected because tone differences
  necessarily change neighbouring gaps.

## Risks and follow-up

- Wave-screen images will look flatter vertically because tone no longer
  changes crest height. Ink presence still follows the image.
- Every existing Wave-screen SVG and CMYK G-code file must be regenerated.
- The print confirmed parallel row spacing. A fresh full yellow print after
  `WSW-20261024-007` is still required to confirm the smoother chord sampling.

## Files

- `software/converter_core/cmyk.py`: shared horizontal waveform profile.
- `software/tests/test_cmyk_tab.py`: parallel-row, all-angle, and blank-mask
  regressions.
- `software/README.md`: current Wave-screen behavior.
- `docs/report/lab-notes/2026-10-23-m-13-cmyk-yellow-feed-sensitivity.md`:
  diagnosis and next physical verification.
- `docs/testing/TEST_PLAN.md`, `docs/project/ROADMAP.md`, and
  `docs/project/ENGINEERING_LOG.md`: current status.
