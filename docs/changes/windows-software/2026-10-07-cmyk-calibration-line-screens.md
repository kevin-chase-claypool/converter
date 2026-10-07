---
id: WSW-20261007-008
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_sheet.py
  - software/generator_tabs/cmyk_tab.py
  - tools/cmyk_calibrate.py
  - software/tests/test_cmyk_sheet.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - calibration
  - line-screen
  - crosshatch
  - test-print
related:
  - WSW-20261007-002
  - WSW-20261007-007
---

# Let the CMYK calibration sheet follow the screen style

## Summary

The calibration sheet no longer forces halftone dots. A new **Sheet screen**
selector in the Calibration group offers "Match the Screen style" (default),
"Line screen (straight strokes)", "Crosshatch levels", and "Halftone dots".
The second ladder row adapts to the chosen screen: line pitch (0.6-3.0 mm at
full tone) for the line screen, hatch levels (2-5 at 80 % tone) for
crosshatch, and dot size (20-140 % at 50 % tone) for dots. Dense ink spots
use a tight mark spacing for line screens, and the sheet header, captions,
and manifest all name the actual screen. Line sheets draw continuous strokes
instead of thousands of dots: the default 200 x 200 mm line sheet builds
about 170/250/150 C/M/Y polylines (K carries the labels and fiducials) where
the dot sheet needs roughly 2,600 marks per ink.

## Reason

Owner: "i dont want to do this with dots. my printer is not good with dots.
it is good with straight lines though." A calibration sheet must exercise the
marks the machine actually prints well and the style the owner will use for
artwork; dot ladders are useless to a line-screen workflow.

## Implementation

- `software/generator_tabs/cmyk_sheet.py`: `build_sheet(..., screen=,
  levels=)`; the builder screens every cell through
  `converter_core.cmyk.screen_channel` with the chosen style; per-screen
  ladder row, captions, header line, dense spots (tight parallel lines, or a
  tight crosshatch for the hatch screen), and manifest settings. Step cells
  record their `pitch_mm` or `levels` value in the manifest.
- `software/generator_tabs/cmyk_tab.py`: the **Sheet screen** combo defaults
  to "Match the Screen style" (line screen and crosshatch map through
  directly; other styles use dots); the control is part of the layer cache
  key, and the group text explains the ladder mapping.
- `tools/cmyk_calibrate.py`: the ladder report covers both the dot block
  name (`dots`) and the new shared name (`steps`).

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 365
  tests (1 skipped: the pre-existing headless shader compile).
- New tests: the line sheet swaps the dot ladder for pitch labels and values
  (0.6/0.8/1/1.4/1.8/2.4/3) and draws fewer marks than the dot sheet, the
  crosshatch sheet sweeps hatch levels 2-5, unknown screens are rejected,
  and the tab's sheet follows the Screen style with the explicit override
  respected.
- Rendered the default line sheet (200 x 200 mm, pitch 1.2 mm) to PNG and
  inspected it: density ladders, pitch ladder, overdraw, GCR ramp,
  crossing-line mixes, dense spots, paper, and fiducials all fit the page.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- A builder attribute named `screen` shadowed the `screen()` method
  (`TypeError: 'str' object is not callable`); it is now `screen_style`.
- One universal ladder was rejected: a dot-size ladder is meaningless to a
  line printer, so the ladder follows the chosen screen and the header
  states which ladder the sheet swept.
- Crosshatch tone thresholds mean the 10-20 % coverage cells legitimately
  print empty; that is the style's quantization and is kept visible on the
  sheet instead of being hidden.

## Risks and follow-up

- The line sheet has not been plotted yet; the plotter remains the ground
  truth for how the inks actually mix.
- `WSW-20261007-007` describes the dot-only sheet; this note supersedes that
  behavior. Wiring the measured profile into a multiply print-simulation
  preview is still the follow-up milestone.

## Files

- `software/generator_tabs/cmyk_sheet.py`: screen-aware sheet layout,
  ladders, and manifest.
- `software/generator_tabs/cmyk_tab.py`: Sheet screen control, cache key,
  and UI text.
- `tools/cmyk_calibrate.py`: ladder report for both block names.
- `software/tests/test_cmyk_sheet.py`, `software/tests/test_cmyk_tab.py`:
  coverage for the line and crosshatch sheets and the match behavior.
- `software/README.md`: CMYK section documents the sheet screen.
