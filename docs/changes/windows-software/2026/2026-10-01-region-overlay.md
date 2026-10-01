---
id: WSW-20261001-002
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
tags:
  - kaleidoscope
  - generative
  - interface
related:
  - WSW-20261001-001
  - software/README.md
---

# Region overlay: neighbouring bands braid instead of tiling

## Summary

The random pattern generator has a new `Region overlay` control (0-0.8, default
0.20). It sets how much neighbouring regions share: 0 tiles the shape rings edge
to edge, 0.3 makes every band overlap a third of its height with the next one,
0.6 and up interpenetrate heavily. The bands grow as they overlap so the same
disc is still covered, which means each ring draws a larger version of itself -
the shapes keep their proportions and are never stretched to fill a gap.

## Reason

"something that i want to be able to modify is how much one region overlays into
another, this will help the image look complex", followed by "i dont want them
to stretch the overlaid region" and "i just want the regions to overlap".

## Implementation

- `converter_core/generative.py`:
  - New `band_layout(seed, level, radius, region_overlay)` returns the radial
    bands. With `rings` bands over a span `S`, the band height becomes
    `S / (1 + (rings - 1) * (1 - overlay))` and the pitch `height * (1 - overlay)`,
    so neighbours share exactly `overlay * height` and the last band still ends
    at the same outer edge as before.
  - `random_pattern` takes `region_overlay` and draws every family inside its
    band from that layout. The separator gap closes as the overlay grows
    (`gap * (1 - overlay)`), because overlapping bands do not need the moat the
    tiled layout needed.
  - The first attempt handed each family an *enlarged* band, which stretched the
    shapes; that was replaced by this band-overlap layout.
- `software/qt_kaleidoscope.pyw`: `Region overlay` spin box in the Kaleidoscope
  group (0-0.8, 0.05 steps, two decimals), passed to the generator and saved
  with the rest of the settings.

## Verification

- `band_layout` at overlay 0 tiles edge to edge (each band's outer edge equals
  the next band's inner edge); at 0.3 the overlap is exactly 30 % of the band
  height and the outer edge is unchanged; values are clamped to 0-0.8.
- The drawing stays inside the design radius at overlay 0, 0.4 and 0.8, and is
  never empty.
- Render check `samples\preview\gen_overlay2.png`: overlay 0 / 0.3 / 0.7 at seed
  42, intricacy 8 - tiled, braided and heavily interpenetrating respectively.
- App check: overlay 0.00 gives 24,792 contours and 0.60 gives 20,472 for the
  same seed (fewer, larger, mutually overlapping shapes), and the value is
  remembered across a restart.
- All fourteen test modules pass; `docs_index --write/--check` pass.

## Struggles and rejected approaches

- Enlarging the band a family draws into stretched its shapes - rejected
  immediately by the operator and reverted.
- Sliding each ring's content outward kept the shapes' size but moved the ring
  away from its own inner edge, which reads as displacement rather than
  overlap; the band-overlap layout keeps every ring centred on its own region
  while sharing the strip.

## Risks and follow-up

- Heavy overlay grows the shapes, so the design gets darker and the plot longer;
  the value is a taste knob, not an accuracy one.
- The motif rings keep their own internal overhang on top of this, so engraving
  bands become dense quickly above about 0.5.

## Files

- `software/converter_core/generative.py`: `band_layout`, `region_overlay`.
- `software/qt_kaleidoscope.pyw`: the control and its persistence.
- `software/tests/test_generative.py`: `RegionOverlayTests`.
- `software/README.md`, `docs/project/ENGINEERING_LOG.md`.
