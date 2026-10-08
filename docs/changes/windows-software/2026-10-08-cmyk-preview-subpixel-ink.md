---
id: WSW-20261008-015
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
  - preview
  - ink-simulation
  - fidelity
related:
  - WSW-20261008-014
  - WSW-20261007-007
---

# The ink simulation stops multiplying ink it cannot draw

## Summary

At a fit-to-window zoom the simulated strokes are thinner than one screen
pixel, but they were still drawn one pixel wide at full ink, so an isolated
stroke deposited several times the ink the pen puts on paper. On the owner's
portrait that made every light and mid tone read roughly twice as dark as the
plot will be, and the natural way to "fix" it was to crank ink gamma until
the flat skin dropped below the ink floor and only facial features survived.
Each simulated stroke now fades toward white by the fraction of a pixel it
covers (0.30 mm pen at 1.6 px/mm = 0.49), so the fit view keeps the paper's
real average density. Zooming in past one pixel per pen restores full-strength
strokes.

## Reason

Owner: "auto was way off on gamma. cranking it up got me closer to where i
could at least see facial features, but it's still not great", with gamma 2.2
on `momandbennett.jpg` - which prints 0.638 mean paper luminance against the
photo's 0.434, i.e. the print was being made much lighter than the photo to
compensate for the preview.

## Implementation

- `software/qt_svg_to_gcode.pyw`: `GLPreview.sim_ink_strength()` returns
  `clamp(pen width x pixels per millimetre, 0, 1)`, quantised to 1/64 so a
  window resize rebuilds the colour buffers a handful of times; the
  `artwork_solid` vertex colours mix the ink toward white by the remainder,
  and `paintGL` rebuilds the cache when the strength changes.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 401 tests
  pass, 1 skipped (the pre-existing headless shader compile).
- New test: a 400 mm artwork in a 400 px view gives a strength of 0.25 for
  the 0.30 mm pen with the faded vertex colour, and resizing to 2400 px
  restores a strength of 1.0.

## Struggles and rejected approaches

- Changing the GL blend function to honour alpha was rejected: the vertex
  colour mix needs no shader or blend-mode change, so the risk to the
  (headless-untestable) shader path stays at zero.

## Risks and follow-up

- Dark areas lose a little ink in the simulation too (overlapping rows each
  deposit the sub-pixel fraction), so a fully covered region reads slightly
  lighter than the paper at fit zoom; zoom in for full-strength strokes.
- The strength uses the widget width against the adjusted bounds, so a very
  non-square viewport under- or over-estimates by the aspect correction.

## Files

- `software/qt_svg_to_gcode.pyw`: sub-pixel ink strength in the simulation
  pass.
- `software/tests/test_generator_tabs.py`: strength and vertex-colour test.
- `software/README.md`: preview description.
