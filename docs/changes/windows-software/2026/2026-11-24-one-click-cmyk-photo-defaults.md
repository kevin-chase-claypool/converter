---
id: WSW-20261124-005
date: 2026-11-24
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - edge-flow
  - photo-defaults
  - one-click
  - auto-color
  - physical-validation-pending
related:
  - WSW-20261123-019
  - WSW-20261123-016
  - WSW-20261123-011
---

# Make Edge-flow CMYK photo defaults one-click

## Summary

The existing CMYK tab now starts with a prominent **Use recommended photo
defaults** action. One press installs the complete Edge-flow photo recipe, runs
automatic image colour analysis, and leaves the physical page and machine
placement settings unchanged.

## Reason

The Reddit-reference workflow was already implemented as gradients, structure
tensor, tensor blur, evenly spaced streamlines, dark-tone layers, and fixed
fallback angles. Reaching it still required coordinating many advanced
controls, so a normal photo could be screened with the wrong style, density,
continuity, or colour curve unless the operator knew the reference recipe.

## Implementation

- A new **Recommended** group at the top of the CMYK tab explains that the
  one-click action is the normal photo path and the remaining controls are
  advanced options. No new tab was added.
- `apply_reference_defaults()` disables calibration mode, selects per-ink
  Edge-flow, installs the photo baseline, and invokes the existing image Auto
  analysis. If no artwork is loaded, it prepares the recipe and asks the
  operator to open an image before pressing it again.
- The action preserves page width/height, artwork scale, pen width, all four
  X/Y pen offsets, and the selected bed-motion mode.
- The recommended source pitch targets the larger of `1.2 mm` or `1.25` pen
  widths on paper, converts through the current artwork scale, clamps to the
  supported range, and rounds to the `0.05 mm` control increment.
- The shipped baseline is per-ink Edge-flow; three Flow layers; `2.5 mm`
  smoothing; continuous Black keylines off; Pen-down chain on with a `5.0 mm`
  gap; `0.10 mm` Path tolerance; 200000 Max marks/ink; saturation 90 %;
  contrast 220 %; brightness 80 %; ink gamma 0.60; GCR 90 %; C/M/Y/K weights
  100/100/100/100 %; and an unsharp mask of 100 % at `1.5 mm`. The established
  seed remains 7.
- A successful action reports the selected layers, smoothing, effective
  on-paper pitch, and the next steps: **Preview**, then **Save 4 G-code
  files**.

## Verification

- The focused recommended-defaults, shipped-defaults, manifest, and shared
  Edge-flow tests pass.
- The complete converter discovery suite passes **688 tests with one expected
  OpenGL-context skip**.
- The first full run exposed stale assumptions for the intentional 100 %
  sharpening default and seed change; seed 7 was restored because it was not
  part of the requested recipe.
- A second full run exposed a scale-invariance assertion whose `0.05 mm`
  tolerance was tighter than the new `0.10 mm` path budget. The measured
  difference was `0.0639 mm`; the test now uses the recipe's `0.10 mm`
  physical tolerance.
- No machine motion was started. Golden Sunset Preview and four-file G-code
  inspection remain the next runtime gate before any physical print.

## Struggles and rejected approaches

- Creating another CMYK tab was rejected because the existing tab already owns
  the four-file preview, save, offsets, registration, and kinematics workflow.
- Changing the page, scale, pen width, offsets, or bed motion from the preset
  was rejected because those describe the installed physical layout and must
  survive a screening reset.
- Treating the new seed 8 as part of the requested default set was rejected
  because the seed was not specified and changes the established saved-layout
  behavior. The action preserves seed 7.

## Risks and follow-up

Auto still refines colour controls for the loaded image, so the exact colour
curve can differ from the baseline. The pitch/smoothing/layer/continuity recipe
and physical settings are deterministic. Existing artwork recipes retain their
saved advanced controls until the operator deliberately presses the button.
A physical four-pass sheet remains necessary to validate density, connector
ink, registration, black overlap, and pen-set separation.

## Files

- `software/generator_tabs/cmyk_tab.py`: recommended action, baseline defaults,
  and adaptive pitch helper.
- `software/tests/test_cmyk_tab.py`: recipe, preservation, and default
  regressions.
- `software/README.md`: one-click CMYK workflow and current defaults.
- `docs/project/ENGINEERING_LOG.md`: implementation and verification milestone.
