---
id: WSW-20261123-016
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
  - docs/proposals/flow-field-cmyk.md
tags:
  - cmyk
  - auto
  - color-management
  - process-inks
  - edge-flow
  - portrait
related:
  - WSW-20261123-015
  - WSW-20261123-005
  - WSW-20261008-007
---

# Make CMYK Auto optimize the process-colour prediction

## Summary

**Auto (photo)** now refines its style-specific detail/exposure baseline
through the process-ink model. It searches Auto levels, brightness, contrast,
saturation, GCR, and gamma for lower predicted RGB error, retains tone/detail/
clipping penalties, resets all ink weights to 100 %, and reports the resulting
predicted RGB error in the status line.

## Reason

Separating against known process inks made the preview more predictable, but
Auto still used a detail-only search and Edge-flow used a fixed image-curve
heuristic. The owner asked why Auto did not use the now-accurate ink model to
choose the most accurate image controls.

## Implementation

- The previous style-specific recommendation remains the baseline: it supplies
  the detail search, Wave exposure path, sharpening, and screen-specific
  constraints.
- A shared Auto evaluator applies the image curve, process separation, and an
  approximate screen-coverage step, then predicts the final process RGB.
- Coordinate search compares colour RMSE, chroma error, mean-tone error,
  detail shortfall, and clipping across bounded candidates for Auto levels,
  brightness, contrast, saturation, GCR, and gamma.
- Ink weights are explicit colour biases, so Auto resets them to 100 % rather
  than silently carrying a previous manual correction.
- The status line now includes the four weights and predicted RGB error
  (`0-255` units) before asking the operator to Preview.
- Wave keeps its exposure-preserving setup because its row geometry cannot use
  the same direct coverage estimate without a separate physical model.

## Verification

- Focused Auto tests pass `12` cases covering dark/bright photos, sparse and
  fine screens, vivid subjects, detail retention, Edge-flow pitch ownership,
  and Wave exposure behavior.
- The complete CMYK tab suite passes `137` tests. Complete converter discovery
  passes `662` tests with one expected OpenGL-context skip.
- A synthetic Edge-flow colour card verifies that the selected Auto result has
  lower process-model RGB error than the former Auto baseline.
- For `IMG_0514.JPG` at `0.52 mm` effective pitch, the old heuristic predicts
  `33.9/255` mean RGB RMS while the new Auto selects Auto levels off,
  brightness `140 %`, contrast `140 %`, saturation `90 %`, GCR `100 %`,
  gamma `0.75`, all weights `100 %`, and predicts `4.7/255`.

## Struggles and rejected approaches

Applying the same coverage estimate to Wave produced a poor `56.5/255`
prediction because row geometry, amplitude, and masked length do not equal a
simple ink-area fraction. Wave therefore retains its existing exposure path
until a dedicated row-coverage model is validated.

Optimizing weights independently allowed large global darkening corrections
that reduced RGB error by making the whole print lighter. Auto now fixes the
weights at 100 % and lets the image curve solve exposure and contrast.

## Risks and follow-up

The reported prediction uses an approximate screen-area model, not a raster
of the final vector screen. It is a relative optimization target, not a
physical proof. Measured pen/paper response and a four-pass print remain
required. Wave color fitting remains a separate follow-up.

## Files

- `software/converter_core/cmyk.py`: process-aware Auto evaluator and search.
- `software/generator_tabs/cmyk_tab.py`: image-curve output, weight reset,
  tooltip, and predicted-error status.
- `software/tests/test_cmyk_tab.py`: Auto accuracy and regression coverage.
- `software/README.md` and `docs/proposals/flow-field-cmyk.md`: current Auto
  behavior and portrait result.
