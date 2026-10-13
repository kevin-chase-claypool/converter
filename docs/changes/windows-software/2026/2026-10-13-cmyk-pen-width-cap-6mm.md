---
id: WSW-20261013-001
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
tags:
  - cmyk
  - pen-width
  - tombow
  - controls
related:
  - docs/testing/CMYK_CALIBRATION.md
---

# CMYK Pen width cap raised to 6 mm for brush pens

## Summary

The CMYK tab's **Pen width** spinner (Screen group) is capped at 6.0 mm instead
of 1.2 mm. The fine end of a Tombow Dual Brush pen (~0.8 mm nib, and the 0.1 mm
floor is unchanged) still sits inside the range; the brush end lays several
millimetres depending on pressure and the downstream model already clamps to
0.1-8.0 mm, so the old cap was the only thing rejecting a legitimate physical
pen.

## Reason

Operator request (2026-10-13): "my pen diameter only goes up to 1.2, but i need
to check that limitation against the tombow dual water based pen tips." The
Tombow Dual Brush's brush tip draws strokes wider than 1.2 mm at normal working
pressure, and water-based ink spreads further on absorbent paper, so the cap
prevented entering the real tool width for spacing and ink simulation.

## Implementation

One line in `software/generator_tabs/cmyk_tab.py`: the `double_spin` call's
`high` goes from 1.2 to 6.0 (default 0.3, step 0.05, two decimals unchanged).
No model or emitter change: `_pen_width_mm` already clamps to 0.1-8.0 and every
consumer (dot pitch match, fill spacing, pen-width compensation) reads the
value, not the spinner range.

## Verification

- Source inspection of the tab and the downstream clamp.
- The CMYK tab's test module has no assertion on the spinner's maximum, so no
  test change is needed; a fresh `python software\qt_svg_to_gcode.pyw` run is
  the bench check when the brush pen is next used.

## Struggles and rejected approaches

None; single-range change on the operator's request.

## Risks and follow-up

- Planner behaviour at very wide pen widths (multi-pass "Fill wide strokes",
  dot pitch matching) inherits from the pre-existing 8 mm model clamp and was
  not re-tested in this session; the operator's next brush-pen plot is the
  check.

## Files

- `software/generator_tabs/cmyk_tab.py`: spinner range.
- `docs/project/ENGINEERING_LOG.md`: session entry.
