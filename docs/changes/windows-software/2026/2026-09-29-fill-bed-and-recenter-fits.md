---
id: WSW-20260929-001
date: 2026-09-29
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
  - software/qt_svg_to_gcode.pyw
tags:
  - converter
  - usability
  - scale
  - reach
  - placement
related:
  - WSW-20260928-002
  - WSW-20260927-007
---

# Fill bed sizing and recentring for the fit actions

## Summary

The single **Fit to bed** button is replaced by two fits that say what they do:

- **Fill bed** sizes the artwork's bounding box to the drawable diameter, so the
  box edges touch the reach circle and the drawing fills the bed. The four
  corners fall outside the circle and are clipped. It sizes in both directions.
- **Fit inside** keeps every point inside the reach circle, so nothing is
  clipped; the bounding box corners land on the ring and the box edges sit
  inside it.

Both fits now also recenter the artwork on the bed center, clearing any manual
or dragged `Artwork offset`.

## Reason

The owner reported that the button "shrinks the image down within the bed way
smaller than the bounds" and that "the image bounds should touch the printable
bounds", adding "and it should center it".

`fit_scale_to_radius()` sizes the *circumscribed circle* of the bounding box:
after fitting, the box corners sit on the ring and the box edges are well inside
it. On the owner's `1157957 (1).svg` that gives a 300 x 225 mm drawing inside a
382.8 mm-wide drawable circle - correct for "nothing may be clipped", but it
reads as an undersized picture rather than a filled bed.

| fit | scale | bounds | artwork radius vs 191.4 mm reach |
|---|---|---|---|
| none (`Scale 1.0`) | 1.0 | 1440 x 1080 mm | 899.8 mm, 4.7x too big |
| **Fit inside** | 0.2085 | 300 x 225 mm | 187.4 mm, corners touch |
| **Fill bed** | 0.2605 | 375 x 281 mm | 234.2 mm, corners clipped |

The drawing was also left where it had been dragged: a fit changed the size but
kept the placement offset, so the result could sit off-center in the bed.

## Implementation

`software/converter_core/geometry.py`:

- `artwork_span()` returns the bounding-box `(width, height)` at the current
  scale.
- `fit_scale_to_span()` returns the exact factor that makes the longer
  bounding-box side span a target, so artwork smaller than the bed grows and
  artwork larger than the bed shrinks. `fit_scale_to_radius()` keeps its
  shrink-only contract.

`software/qt_svg_to_gcode.pyw`:

- Buttons `Fill bed` and `Fit inside` replace the single `Fit to bed`. Each is
  enabled only while it would change the scale, or while an artwork offset is
  still set and a recenter is available.
- `fit_to_bed(fill=False)` is the shared implementation. Both paths clear
  `artwork_offset_x_mm` / `artwork_offset_y_mm`, report the scale change and the
  recenter in the log, and leave the rebuild to the usual Preview press.
- The clipping notice names both actions instead of instructing a single one,
  and scales its wording: "most of the drawing is outside" above 1.5x the reach,
  "the corners fall outside" below it.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 72 tests pass.
  New cases in `software/tests/test_fit_to_bed.py` cover `artwork_span()` for a
  square and a rectangle, filling the bed down from oversized artwork and up
  from small artwork, and the no-op cases for empty, zero, and negative spans.
- Offscreen UI probe against the real `MainWindow` with a 1440 x 1440 mm square
  and the reach at 191.4 mm:

| step | result |
|---|---|
| oversized, offsets 12.5 / -8.0 | both buttons enabled, red guide, notice names both |
| `Fill bed` | scale `1 -> 0.2605`, span `375.12 mm`, corner radius `265.2 mm`, offsets `0 / 0` |
| `Fit inside` afterwards | scale `0.2605 -> 0.1842`, offsets stay `0 / 0` |
| inside the reach | `Fill bed` enabled to grow back, `Fit inside` disabled, green guide |
| fresh build | stale notice cleared; tolerance, scale, and fill-spacing edits re-mark it |

- Rendered contour plots of `1157957 (1).svg` at both scales confirm the visual
  difference: `Fit inside` leaves margin on all four sides, `Fill bed` touches
  the circle on all four sides with clipped corners.

## Struggles and rejected approaches

- Making the single button fill the bed and dropping the inside fit was
  rejected: clipping the corners is right for full-bleed artwork and wrong for a
  logo, so both behaviours stay available and are named.
- Reporting the clipped *area* percentage in the notice was rejected. It depends
  on the artwork silhouette, so the notice stays with the radius ratio the
  clipping actually uses.

## Risks and follow-up

- **Fill bed clips the corners.** That is the requested behaviour, but it is
  content loss, so the guide still turns red after such a fit and `Fit inside`
  remains one press away to undo it.
- Both fits keep the 2% safety margin, so the bounds land 3.8 mm inside the
  drawable diameter rather than exactly on it.
- After a fit the stored contours still describe the previous scale until
  Preview is pressed, so the notice and the stale banner remain until then.

## Files

- `software/converter_core/geometry.py`: `artwork_span`, `fit_scale_to_span`.
- `software/qt_svg_to_gcode.pyw`: two fit actions, recentring, notice wording.
- `software/tests/test_fit_to_bed.py`: span-fit coverage.
- `software/README.md`: current fit behaviour.
- `docs/HANDOFF.md`: Qt UI section.
