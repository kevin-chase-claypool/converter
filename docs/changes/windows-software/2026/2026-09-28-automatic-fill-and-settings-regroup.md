---
id: WSW-20260928-001
date: 2026-09-28
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/geometry.py
  - software/qt_svg_to_gcode.pyw
tags:
  - converter
  - usability
  - fill
  - hatch
  - line-art
  - settings-layout
related:
  - WSW-20260927-001
  - WSW-20260926-002
  - WSW-20260924-006
---

# Automatic fill source and an intuitive settings layout

## Summary

Fill now works without the user choosing between vector fill and raster
shading. `Fill spacing mm` defaults to `4` mm instead of `0`, so fill is on out
of the box, and the `Raster shading` checkbox is replaced by a `Fill source`
choice that defaults to `Auto`:

| Fill source | Behaviour |
|---|---|
| `Auto (recommended)` | Hatches the SVG's own shapes; switches to image tone only when the artwork's tone lives in an embedded image or a gradient |
| `SVG shapes (stays inside)` | Always hatches the SVG's shapes and closed outlines |
| `Image tone (photos, gradients)` | Always hatches the rendered pixels |

Stroke-only line art is now fillable too: an element that declares no visible
fill contributes the regions its *closed* outlines enclose. Artwork that
declares `fill="none"` therefore gains interior fill instead of plotting as
outlines only, while open subpaths still contribute no fill region.

The sidebar was regrouped so each setting sits with the thing it changes. The
reported misplacement was `Pen stroke mm` under **Preview settings**; the audit
found three more. The new groups are **Geometry**, **Fill** (was *Shading*),
**Motion**, **Theta kinematics**, **Pen**, **Machine**, and **Preview settings**
(now preview-only).

## Reason

The owner reported that unchecking raster shading left outlines with no fill,
and that the converter was "much too complicated" and hard to use. Both were
structural, not a single wrong value:

1. Fill had two competing mechanisms whose result depended on what the SVG
   happened to contain. Vector fill hatches the regions the SVG declares;
   raster shading hatches the rendered pixels and can overshoot edges. The user
   had to know which one their file needed, and the app said nothing either way.
2. An element with `fill="none"` had no fill region at all, so "fill" silently
   produced nothing on line art. That is the exact case the owner hit.
3. `Fill spacing mm` defaulted to `0`, which means *disabled*, so a fresh
   session produced no fill and no explanation.

The settings audit found these misplacements, each of which changes the emitted
program rather than the view:

| Setting | Was | Now |
|---|---|---|
| `Pen stroke mm` | Preview settings | Pen |
| `Bed dia mm`, `Bed margin mm` | Preview settings | Machine |
| `Gantry reach radius mm` | Preview settings | Machine |
| `Park X/Y machine mm` | Pen | Machine |
| `Artwork offset X/Y mm` | Preview settings | Geometry |

`theta_mode` and `theta_resolver` were free-text fields; they are now combos of
the values the planner actually implements, so a typo can no longer fall back
to a different strategy silently.

## Implementation

`software/converter_core/geometry.py`:

- `closed_outline_regions()` turns an element's closed outline loops into fill
  regions when the element declares no visible fill. It requires an explicit
  closure within `2 x tolerance`, at least four points, and a non-degenerate
  area, so open segments never invent an interior.
- `element_contours()` selects the fill region set: filled contours when the
  element has a visible fill (density from `fill_darkness`), closed outline
  loops when it is stroke-only (density from `stroke_darkness`). An optional
  `stats` dict reports how many fill contours were produced.
- `svg_fill_sources()` classifies an SVG without parsing path geometry: counts
  of filled elements, stroke-only elements, embedded `<image>` elements, and
  `url(#...)` paint servers.
- `resolve_fill_source()` maps `settings.fill_source` plus that classification
  onto `shapes` or `tone`.

`software/converter_core/settings.py`:

- `hatch_spacing_mm` default `0.0 -> 4.0`; `raster_shading: bool` is replaced by
  `fill_source: str = "auto"`.
- `TEXT_FIELD_GROUPS` / `CHECKBOX_FIELDS` carry the new grouping, and the Qt
  sidebar now builds its checkboxes from `CHECKBOX_FIELDS` instead of adding
  them by hand, so a setting cannot drift between the core model and the UI.
- `FILL_SOURCE_CHOICES`, `VALUE_CHOICE_FIELDS`, and `FIELD_TOOLTIPS` are the
  single source for combo contents and the in-UI explanations.
- `validate_settings()` rejects an unknown `fill_source`, `hatch_pattern`,
  `theta_mode`, or `theta_resolver`.

`software/qt_svg_to_gcode.pyw`:

- The `Shading` group became `Fill`, with `Fill source` next to the fill
  geometry settings, and `Raster px/unit` visible whenever image tone is still
  possible.
- `load_contours()` resolves the source, keeps a cache key that includes it, and
  emits one log line through a new `PreviewWorker.notice` signal (queued to the
  UI thread) explaining what fill will do, including the "nothing to hatch"
  case and the `Fill spacing mm = 0` case.
- `auto_configure_shading()` no longer flips a raster checkbox. It reports what
  the file can be hatched from and supplies tone-friendly starter values only
  when the artwork's tone comes from an image or gradient.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 59 tests pass.
  New coverage in `software/tests/test_fill_source.py` pins the defaults,
  source resolution (filled art, line art, embedded image, gradient, explicit
  override), and the reported fill-contour count. The two cases in
  `test_svg_style_inheritance.py` that pinned "line art is never hatched" were
  replaced by the narrower rule (closed outlines fill inside, open outlines do
  not) plus an assertion that no fill leaves the closed outlines.
- `samples/svg/kindergarten-house-sun.svg`, `crosshatch`, `Fill spacing 4 mm`,
  scale 0.8, run through the real `PreviewWorker` offscreen:

| | clipped contours | G-code lines | fill |
|---|---|---|---|
| Before (auto enabled raster) | 150 | 1302 | none - outlines only |
| After (auto keeps vector fill) | 190 | 2973 | 172 hatch passes inside the closed outlines |

  Rendered contour plots confirm the house body, door, windows, and sun are
  hatched inside their own outlines while the open roof, chimney, sun rays, and
  grass stay line only.
- A traced bitmap (`3383795.svg`, 823 filled paths, 1080 x 1080) at scale 0.25:
  `Auto` resolved to `shapes`, 11870 hatch passes, 8148 clipped contours, 76876
  G-code lines in 9.6 s.
- A plotter-ready open-segment export
  (`Calder_Hall_XYTheta_440mm_plotter_ready.svg`, 2020 stroke-only paths): 164
  hatch passes from the closed glyph counters only; the drawing renders
  unchanged at plot scale.

## Struggles and rejected approaches

- Filling line art by implicitly closing every subpath was rejected. It is what
  SVG rendering does, but it is also exactly the behaviour
  `WSW-20260927-001` removed after the owner reported that shading turned line
  art into a solid fill that leaked outside the drawing. Closed loops only is
  narrower, explainable, and cannot leak.
- Detecting "does vector fill produce anything" by parsing the file when it is
  selected was rejected as unaffordable: the full parse of a 1.9 MB trace takes
  minutes, and the selection handler runs on the UI thread. `svg_fill_sources()`
  inspects elements and inherited style only.
- Keeping the `Raster shading` checkbox and only renaming it was rejected. The
  decision the user had to make - which mechanism suits this file - is the thing
  `Auto` now answers.

## Risks and follow-up

- **Fill is now on by default (4 mm).** Every conversion that previously
  produced outlines only now produces hatch inside filled shapes and closed
  outlines. Set `Fill spacing mm = 0` for outline-only plotting. This is a
  deliberate default change; the previous default made fill look broken.
- Artwork whose outlines are open, such as the Calder Hall and F15
  plotter-ready exports, has no bounded interior and cannot be vector-filled.
  The log now says so instead of leaving the user guessing.
- `Auto` only switches to image tone for embedded images and `url(#...)` paint
  servers. Artwork whose tone is carried by overlapping translucent vector
  fills still resolves to `shapes`; select `Image tone` by hand for that.
- Running the Qt preview in an offscreen harness exits with `0xC0000409` during
  interpreter teardown. The same crash reproduces on the pre-change tree and
  happens after the preview completes, so it is a harness/offscreen-plug-in
  artifact, not this change.
- `docs/project/ENGINEERING_LOG.md` remains far past the ~1,000-line archive
  threshold in `AGENTS.md`; that is already recorded on the roadmap.

## Files

- `software/converter_core/settings.py`: new grouping, fill default, fill source,
  choice fields, tooltips, and validation.
- `software/converter_core/geometry.py`: closed-outline fill regions, fill-source
  classification and resolution, fill-contour counting.
- `software/qt_svg_to_gcode.pyw`: Fill group, data-driven sidebar, fill log line,
  reworked auto-configuration.
- `software/tests/test_fill_source.py`: new coverage for defaults and source
  resolution.
- `software/tests/test_svg_style_inheritance.py`: line-art fill rule.
- `software/tests/test_infill_bridging.py`: `fill_source` replaces
  `raster_shading`.
- `software/README.md`: current fill behaviour, defaults, and settings groups.
- `docs/HANDOFF.md`: shading and Qt UI sections.
