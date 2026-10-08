---
id: WSW-20261008-008
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - cmyk
  - calibration
  - ink-simulation
related:
  - WSW-20261008-007
  - WSW-20261007-022
  - WSW-20261007-014
---

# Load measured ink profiles into the simulation

## Summary

The preview panel gains an **Ink profile...** button. It loads the
`*-profile.json` that `tools/cmyk_calibrate.py` writes from a scanned
calibration sheet, and the Ink simulation then multiplies the pens'
measured transmittances instead of the display ink colours - the last step
of the calibration loop this repository already built. The loaded values
are logged, and the Ink simulation tooltip names the active profile. The
pale/drawn progress view keeps the display colours by design.

## Reason

Ranked improvement 1 from
`docs/research/2026-10-08-cmyk-vs-open-source.md`: every reference tool
concedes its preview is approximate (DrawingBotV3: "may differ from the
final plot; experimentation may be needed"), while our sheet plus analyzer
can measure the real inks - but nothing consumed the profile.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `rgb_floats` and an `ink_colors` override
  in `ink_vertex_colors`; `GLPreview.set_sim_ink_colors` (clamped channel ->
  (r, g, b) map) feeding the solid multiply buffer;
  `MainWindow.load_ink_profile(path=None)` validates
  `kind == "cmyk-ink-profile"`, applies the inks, and reports them in the
  log. The **Ink profile...** button sits beside the Ink simulation
  checkbox.
- `software/README.md`: preview-panel note.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 394
  tests (1 skipped: the pre-existing headless shader compile). New tests:
  measured colours override the display colours in `ink_vertex_colors`, and
  loading a profile JSON (real temp file) drives the GL solid buffer to the
  measured values.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Auto-discovering a profile beside the artwork was rejected: the scan tool
  names profiles after the scan file, so guessing would surprise more often
  than help. Loading is explicit.
- Recolouring the pale/drawn progress view with measured inks was rejected:
  that view identifies layer identity; the measured colours belong to the
  finished-print simulation only.

## Risks and follow-up

- The profile applies to the session until another is loaded; persistence
  per pen set is a follow-up. Exposure of measured values as editable
  sliders (DrawingBotV3-style per-pen multipliers) remains ranked item 6.

## Files

- `software/qt_svg_to_gcode.pyw`: override plumbing, loader, button.
- `software/tests/test_generator_tabs.py`: override and loader tests.
- `software/README.md`: documentation.
