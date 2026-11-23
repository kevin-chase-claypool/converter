---
id: WSW-20261123-006
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - edge-flow
  - fine-detail
  - pen-width
  - portrait
related:
  - WSW-20261123-003
  - WSW-20261123-005
  - docs/proposals/flow-field-cmyk.md
---

# Add a pen-aware Edge-flow fine-detail preset

## Summary

The CMYK tab now has an explicit **Fine detail** action for Edge-flow
portraits. It derives pitch, Flow smoothing, layer count, and Path tolerance
from the current Pen width and Artwork scale, making facial features more
precise with `0.6-0.8 mm` pens.

## Reason

At a `0.6 mm` pen and `260 %` artwork scale, the saved recipe used `4.0 mm`
Flow smoothing, five Flow layers, and `0.45 mm` source pitch. The preview kept
the image's broad color field, but the blurred direction field and stacked
shadow networks merged the eye, nose, and lip structure into heavy contour
knots.

Software comparisons showed that the tuning relationship should follow the
physical pen, not a fixed page distance. Lower smoothing exposed eye and
nostril boundaries; fewer layers prevented dark networks from burying the
face; and a pitch near `1.5` effective pen widths retained enough white paper
between strokes.

## Implementation

- **Fine detail** selects Edge-flow and sets Dot pitch to `1.5 / scale` pen
  widths.
- Flow smoothing becomes `2.5` pen widths, clamped to `1.2-2.0 mm`.
- Flow layers become two for pens at or below `0.7 mm`, otherwise three.
- Path tolerance is lowered to at most `0.10 mm`; an already finer value is
  retained.
- The action intentionally changes the saved screen layout. Edge-flow Auto
  remains image-only and never changes pitch.
- For a `0.6 mm` pen at `260 %` scale, the preset selects `0.35 mm` source
  pitch (`0.91 mm` effective), `1.5 mm` smoothing, two layers, and `0.10 mm`
  tolerance.

## Verification

- A tab regression checks the `0.6 mm` / `260 %` preset and the `0.8 mm` /
  `150 %` case, including the effective pitch, smoothing, layers, tolerance,
  status message, and Edge-flow selection.
- A software comparison at `600 px` shows the selected preset retaining the
  eye, nose, and lip boundaries with fewer merged shadow contours than the
  current five-layer `4.0 mm` screen.
- Complete converter discovery passes `639` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

Reducing pitch alone did not restore precision because it also increased seed
density and could over-ink the face. Lowering tone density alone left the
direction field too blurred. The selected preset changes only the edge-flow
geometry controls that directly determine the physical feature scale.

Keeping five layers and merely reducing smoothing produced sharper directions
but still buried them under overlapping dark networks.

## Risks and follow-up

The automatic preset is a software-selected starting point. Pen spread, ink
opacity, and paper still require a physical four-pass comparison. Compact
features such as the mouth can still benefit from the separate continuous
Black-keyline treatment noted in `WSW-20261123-003`.

## Files

- `software/generator_tabs/cmyk_tab.py`: Fine-detail control and pen-aware
  preset calculation.
- `software/tests/test_cmyk_tab.py`: preset regression for `0.6 mm` and
  `0.8 mm` pens.
- `software/README.md`: operator behavior and example values.
- `docs/proposals/flow-field-cmyk.md`: current preset parameters.
- `docs/project/ENGINEERING_LOG.md`: evidence and verification record.
