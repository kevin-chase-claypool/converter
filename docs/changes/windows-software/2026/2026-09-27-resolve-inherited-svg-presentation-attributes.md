---
id: WSW-20260927-001
date: 2026-09-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/geometry.py
tags:
  - converter
  - svg
  - style-inheritance
  - shading
  - hatch
  - fill
  - line-art
related:
  - WSW-20260926-002
---

# Resolve inherited SVG presentation attributes

## Summary

The converter now resolves SVG presentation attributes through the element tree.
A wrapper such as `<g fill="none" stroke="#000000" stroke-width="0.7">` reaches
its children, so enabling shading no longer turns single-pen line art into a
hatched solid fill.

## Reason

Shading produced hatch strokes across the interior of outline paths instead of
staying inside the regions the artwork intended to shade. The owner reported it
as "the lines don't stay within the borders of what is being shaded."

`style_value()` read presentation values from the element alone. Every sample
under `samples/svg/` declares its pen style once on a wrapping group - the normal
output of Illustrator, Inkscape, and the project's own generators - so the
declaration never reached any child. Each child then fell back to the SVG
initial value `fill: black` and was treated as a solid filled region.

Because `_element_is_visible()` accepted "has a visible fill" as proof of
visibility, the same phantom fill was also the only reason those elements were
drawn at all. One defect, two symptoms.

## Implementation

`software/converter_core/geometry.py`:

- `own_style_value()` holds the previous element-local lookup; `style_value()`
  now falls through to an inherited mapping. Passing no mapping keeps the old
  behaviour, so the helper stay usable standalone.
- `inherited_style()` extends a parent mapping with the inheritable properties
  (`fill`, `fill-opacity`, `stroke`, `stroke-opacity`, `stroke-width`,
  `visibility`, `opacity`).
- `style_hidden()` honours `display="none"` as a subtree suppression and
  `visibility="hidden" | "collapse"` as an inherited value.
- `stroke_width()`, `has_visible_stroke()`, `has_visible_fill()`,
  `fill_darkness()`, `stroke_darkness()`, `_element_is_visible()`, and
  `element_contours()` take an optional inherited mapping. `element_contours()`
  gained the parameter last so existing positional callers are unaffected.
- `parse_svg_geometry()`'s `walk()` resolves each element's style once and
  passes it to both the element and its children. `<use>` targets inherit from
  the referencing element.

The `fill` initial value is still black when nothing declares it, so artwork
that genuinely relies on an implicit fill is unchanged.

## Verification

Measured on `samples/svg/kindergarten-house-sun.svg`, which declares
`<g fill="none" stroke="#000000" stroke-width="0.7" ...>`, with `Fill spacing 4`
and `crosshatch`:

| | contours | two-point segments |
|---|---|---|
| Before the change | 346 | 335 |
| After the change | 20 | 9 |
| Hatching disabled (reference) | 20 | 9 |

The 9 two-point segments are artwork elements, not hatch: the shading-on and
shading-off results are now identical. A `<g fill="black">` rectangle still
hatches (20 lines), so real fills are unaffected.

- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 31
  tests. The 6 new cases live in `software/tests/test_svg_style_inheritance.py`.
- `python -m py_compile software\qt_svg_to_gcode.pyw` passes.

## Struggles and rejected approaches

- The first reproduction was a hand-built triangle, which clipped correctly and
  pointed away from the real cause. The defect only appears when a style is
  declared on an ancestor, so the reproduction had to use a `<g>` wrapper.
- Treating "has a stroke and declares no fill" as stroke-only was rejected. It
  would fix the reported file but silently drops artwork that genuinely depends
  on the implicit black fill, and it contradicts the SVG initial-value rule.
- Fixing `has_visible_fill()` alone was rejected: `_element_is_visible()` and the
  stroke resolution share the same blind spot, so `fill="none"` on a group would
  have made its children vanish entirely instead of drawing them as line art.

## Risks and follow-up

- Inherited `opacity` approximates a subtree composite rather than reproducing
  it. A `<g opacity="0.5">` now lightens its children's effective tone, which is
  closer to a renderer than ignoring the value, but it is still an
  approximation.
- Pen-relative shading (`spacing = pen_diameter / coverage`, so tone follows the
  loaded pen) is the owner's stated next request. It was deliberately deferred
  until the fill regions were correct, because tuning density over the wrong
  regions would have masked this defect.
- `docs/project/ENGINEERING_LOG.md` is 5,665 lines, well past the ~1,000-line
  archive threshold in `AGENTS.md`. Separately, its 74 newest entries sit above
  the log's `---` separator and are therefore absent from the generated topic
  index; `python tools\docs_index.py --check` passes because the check only
  compares the regenerated index against the chronology below the separator.
  Both are recorded on the roadmap rather than fixed inside this change.

## Files

- `software/converter_core/geometry.py`: inherited style resolution.
- `software/tests/test_svg_style_inheritance.py`: new regression coverage.
- `software/README.md`: documents the inherited-style behaviour.
