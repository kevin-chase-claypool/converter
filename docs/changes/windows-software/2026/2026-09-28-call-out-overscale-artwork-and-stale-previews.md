---
id: WSW-20260928-002
date: 2026-09-28
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
  - clipping
  - preview
related:
  - WSW-20260928-001
  - WSW-20260926-002
  - WSW-20260927-007
---

# Call out over-scale artwork and out-of-date previews

## Summary

Two planning mistakes that the preview could not show by itself are now visible
in it:

1. **Over-scale artwork.** When the measured artwork radius exceeds the reach
   circle, the guide turns red, the preview states the ratio, and a **Fit to
   bed** button sets `Scale` so the whole drawing fits. A cropped plot used to
   look exactly like a finished one.
2. **Out-of-date preview.** Building a preview is manual, so changing any
   plan-affecting setting now marks the window with `Settings changed since this
   preview - press Preview to rebuild it.`

## Reason

The owner reported that "the infill still looks terrible" and sent a preview in
which `Fill spacing mm` read `0` while the drawing clearly carried fill. Both
observations had the same root: the window could show a plot that no longer
matched the settings beside it, and it could show a fragment of an oversized
artwork as though it were the whole picture.

Measured on the owner's `1157957 (1).svg` (a VTracer export of a 1440 x 1080
bitmap) at the settings in that screenshot:

| | value |
|---|---|
| Artwork size at `Scale = 1.0` | 1440 x 1080 mm |
| Artwork radius | 899.8 mm |
| Reach cap | 191.4 mm |
| Result | 4.7x too big; only the middle 21% of the image is inside the reach |
| Pen-down path of what remains | 24.7 m (~35 min at 700 mm/min) |

Nothing in the preview distinguished that from a deliberate close-up, and the
clipping notice lived in a status line below the plot. At `Scale = 0.25` the
same file fits (360 x 270 mm) and the fill renders as a shaded drawing.

## Implementation

`software/converter_core/geometry.py`:

- `artwork_radius()` measures the farthest point from the artwork's
  bounding-box center. Placement centers that box on the bed center, so the box
  center - not any particular point of the drawing - is the correct origin.
- `fit_scale_to_radius()` returns the factor that fits already-scaled contours
  inside a target radius with a 2% margin. It returns `1.0` when the artwork
  already fits, when the geometry is empty, or when the target is not positive,
  so it is always safe to multiply into the current scale.

`software/qt_svg_to_gcode.pyw`:

- `clip_info()`, `update_clip_warning()`, and `fit_to_bed()`. The preview shows
  the ratio and enables the button only when the artwork is actually clipped;
  `Fit to bed` never enlarges artwork that already fits.
- `GLPreview.set_reach_warning()` draws the reach guide red instead of green
  while the artwork is clipped. The guide is the only overlay drawn at the same
  scale as the bed circle, so it is where over-scale artwork is visible without
  reading text.
- `mark_preview_dirty()` plus per-field signal wiring at the end of `build_ui`.
  Every settings field except `print_speed` and `motion_estimate_scale` marks
  the preview stale, as do the plan-affecting checkboxes; the two display-only
  preview toggles deliberately do not. `install_preview()` clears the mark.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 67 tests pass.
  8 new cases in `software/tests/test_fit_to_bed.py` cover radius measurement on
  an offset artwork, the fitted radius landing at `reach x 0.98`, no-op cases
  (empty, zero radius, negative radius, already fitting), and that fitting never
  scales up.
- Offscreen UI probe against the real `MainWindow`:

| step | result |
|---|---|
| 1440 mm artwork, reach 191.4 mm | `Fit to bed` enabled, warning shown, guide `#dc2626` |
| warning text | `Artwork radius 1018.2 mm is 5.3x the 191.4 mm reach, so only the middle of the drawing is plotted.` |
| after `Fit to bed` | scale `1.0 -> 0.1842`, stale warning shown, log line written |
| artwork inside the reach | button disabled, warning hidden, guide `#15803d`, no scale change |
| fresh build | stale warning cleared |
| edit tolerance / scale / fill spacing | stale warning shown |
| change fill pattern combo | stale warning shown |
| toggle Show X/Y pen-down path | not marked stale |

- `samples/svg/kindergarten-house-sun.svg` still converts end to end through the
  real `PreviewWorker`: 190 clipped contours, 567 moves, 2973 G-code lines.

## Struggles and rejected approaches

- Auto-fitting the scale when a file is selected was rejected. Size is not known
  until the geometry is parsed, and silently rewriting a field the user has set
  is worse than showing an explicit button next to the evidence.
- Reporting the clipped *area* fraction was rejected as a headline number: the
  exact fraction depends on the artwork silhouette, and the radius ratio is the
  quantity the clipping actually uses.
- Marking `print_speed` and `motion_estimate_scale` stale was rejected as noise.
  They change playback and the estimate only.

## Risks and follow-up

- `Fit to bed` measures the circumscribed radius of the bounding box, so a tall
  or wide artwork is fitted by its corners. That matches how clipping works, but
  it leaves visible margin around narrow drawings.
- After `Fit to bed` the stored raw contours still describe the old scale until
  the next build, so the warning stays until Preview is pressed. The stale
  banner is what tells the user that.
- Fill density is still a manual guess. The owner's recorded next request is
  pen-relative shading (`spacing = pen_diameter / coverage`), which would let a
  fill be chosen as "light / medium / solid" instead of a millimetre spacing.
  This change does not touch density.

## Files

- `software/converter_core/geometry.py`: `artwork_radius`, `fit_scale_to_radius`.
- `software/qt_svg_to_gcode.pyw`: clip warning, Fit to bed, reach warning colour,
  stale-preview indicator.
- `software/tests/test_fit_to_bed.py`: new coverage.
- `software/README.md`: current behaviour for both indicators.
- `docs/HANDOFF.md`: Qt UI section.
