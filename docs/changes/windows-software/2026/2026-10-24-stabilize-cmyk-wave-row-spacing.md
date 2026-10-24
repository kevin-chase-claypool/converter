---
id: WSW-20261024-004
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - wave-screen
  - row-spacing
  - amplitude
  - aliasing
  - cyan
  - magenta
  - yellow
  - black
related:
  - WSW-20261007-002
  - 2026-10-23-m-13-cmyk-yellow-feed-sensitivity
---

# Stabilize wave-screen row spacing across all CMYK inks

## Summary

Wave-screen rows now use a vertically smoothed, slew-limited tone signal for
their displacement instead of sampling each row independently. Local image
tone still changes wave amplitude, but detail at the row pitch can no longer
open and close adjacent gaps enough to resemble planner backlash. The shared
implementation applies to cyan, magenta, yellow, and black.

## Reason

The regenerated Ben1 CMYK set used the current compensation planner and
`F700`, yet all four layers showed row-spacing bands. Analysis of the yellow
source and G-code separated the causes:

- The source SVG row centres were exactly `3.08 mm` apart.
- Reconstructing the compensated G-code produced a `3.0736 mm` row fit with
  only `0.0082 mm` RMS and `0.0465 mm` maximum residual.
- At a fixed horizontal position, independently sampled row tone changed the
  visible spacing between wave curves by as much as `1.20 mm`.

The baseline grid was therefore stable before motion planning. The defect was
row-frequency amplitude aliasing in the generator, not X/Y acceleration, the
rotary planner, or ioSender.

## Implementation

- `_wave_rows` now samples the full local tone field before constructing runs.
- Displacement amplitude uses a four-row moving window, followed by a
  `0.04` maximum tone change between adjacent rows.
- With full dot size this limits one adjacent-gap change to about `2 %` of the
  configured pitch, or about `4 %` between successive gaps.
- The unsmoothed tone still controls whether a point receives ink, so blank
  paper and image boundaries remain sharp.
- Broad vertical shading remains encoded by wave amplitude; only changes at
  the row scale are suppressed.

## Verification

- Added a regression using row-frequency tone changes at all four installed
  screen angles (`15`, `75`, `0`, and `45` degrees). Adjacent visible gaps
  now vary by less than `0.15 mm`; the old implementation varied by more than
  `2.28 mm` at zero degrees.
- Added a complementary gradient regression confirming dark-side wave
  amplitude remains more than `2.3x` the light-side amplitude.
- `python -m unittest -v software.tests.test_cmyk_tab`: 68 tests pass.
- `python -m unittest -v software.tests.test_sine_gradient`: 14 tests pass.
- Full converter discovery passes 500 tests with one OpenGL-context skip.
- A post-fix physical CMYK print has not yet been made.

## Struggles and rejected approaches

- Lowering X/Y acceleration was rejected: the G-code's row-centre grid was
  already uniform before the controller ran it.
- Making every wave row use one page-wide amplitude was rejected because it
  would discard vertical image shading.
- Making wave amplitudes constant was rejected because it would flatten the
  portrait instead of fixing the row-scale aliasing.
- Editing the existing compensated G-code was rejected. It would not repair
  the source geometry and would leave the next save with the same behavior.

## Risks and follow-up

- Tone detail at or below the row scale is intentionally smoothed; broad
  facial and background shading remains.
- Physical M-13 acceptance is still required. Regenerate all four Ben1 files
  after restarting the converter, confirm `angular interpolation bed-frame`,
  and print yellow first at the same `F700` and controller settings.
- If spacing bands remain after a current-version print, compare the same
  layer in XY-only at the same feed before changing acceleration again.

## Files

- `software/converter_core/cmyk.py`: vertically smoothed and slew-limited wave
  displacement tone.
- `software/tests/test_cmyk_tab.py`: all-angle row-spacing and shading
  regressions.
- `software/README.md`: current wave-screen behavior.
- `docs/report/lab-notes/2026-10-23-m-13-cmyk-yellow-feed-sensitivity.md`:
  current evidence and post-fix verification status.
- `docs/testing/TEST_PLAN.md`: M-13 status.
- `docs/project/ROADMAP.md`: next physical acceptance step.
- `docs/project/ENGINEERING_LOG.md`: diagnosis and implementation record.
