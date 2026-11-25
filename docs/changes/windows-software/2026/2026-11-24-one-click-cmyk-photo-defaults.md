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
- The converter was restarted and Golden Sunset loaded its previous saved
  recipe: `0.75 mm` pitch, `0.5 mm` smoothing, one Flow layer, `0.05 mm`
  tolerance, and seed 8. The recommended action replaced those screen controls
  with Edge-flow, three layers, `2.5 mm` smoothing, a `1.20 mm` effective
  pitch, `0.10 mm` tolerance, and seed 7.
- The action preserved the restored physical setup: `200 x 200 mm` page,
  `200 %` artwork scale, `0.90 mm` pen, zero pen offsets, Xθ/Yθ bed motion,
  `59 mm` center-hold diameter, and `-0.910 / -4.490 mm` artwork placement.
- Golden Sunset Preview completed in `31.4 s` with 873,992 preview moves and
  a `4 h 7 m 22 s` controller-time estimate. The four saved files have
  matching SHA-256 values in the set manifest and identical page, placement,
  reach-guard, and chaining headers.
- Saved M3/M5 counts are C `523/524`, M `589/590`, Y `629/630`, and K
  `636/637`. `check_gcode_motion.py` passes every file for the bed-step cap,
  A-rate limit, and no bare `G0` rotation; maximum XY radii are
  `179.319/179.283/179.389/179.354 mm` for C/M/Y/K.
- Preflight warns that C/M/Y/K have `8/35/40/15` planner moves above the
  `0.100 mm` path budget, with worst reported bows of
  `0.153/0.245/0.250/0.269 mm`. These are tolerance warnings, not hard-guard
  failures, and require visual inspection on a physical sheet.
- No machine motion was started. The four saved programs are ready for the
  next supervised physical print check.

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
The Golden Sunset page retains its saved `200 %` scale, so its corners are
clipped by the circular reach guard without changing the centre composition.
A physical four-pass sheet remains necessary to validate density, connector
ink, registration, black overlap, pen-set separation, and whether the bounded
preflight deviations are visible.

## Files

- `software/generator_tabs/cmyk_tab.py`: recommended action, baseline defaults,
  and adaptive pitch helper.
- `software/tests/test_cmyk_tab.py`: recipe, preservation, and default
  regressions.
- `software/README.md`: one-click CMYK workflow and current defaults.
- `docs/project/ENGINEERING_LOG.md`: implementation and verification milestone.
