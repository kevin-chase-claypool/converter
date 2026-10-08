---
id: WSW-20261008-007
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - svg
  - preview
related:
  - WSW-20261007-022
---

# Blend the CMYK layer SVGs multiplicatively

## Summary

`svg_document` now writes `style="mix-blend-mode: multiply"` on every ink
group. Opening the combined preview SVG (or a per-ink file) in Inkscape or a
browser shows the layers overprinting the way the Ink simulation and the
printed ink stack do, instead of painting the last layer opaquely.

## Reason

Reconciliation against prior art (`docs/research/2026-10-08-cmyk-vs-open-source.md`):
`ohnorobo/cmyk-splitter`'s combiner sets `mix-blend-mode: multiply` on each
layer; our exported SVGs rendered opaquely outside the app.

## Implementation

- `software/converter_core/cmyk.py`: the group attribute in `svg_document`.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 392
  tests (1 skipped: the pre-existing headless shader compile); the SVG group
  test asserts the blend style on every group.
- `python tools\docs_index.py --check` passes.

## Struggles and rejected approaches

- Adding the blend only to the combined document was rejected as needless
  branching; on a single-layer file the attribute is a no-op.

## Risks and follow-up

- Viewers without `mix-blend-mode` keep the old painter's-order look. G-code
  planning is unchanged: contours come from geometry, not stroke style.

## Files

- `software/converter_core/cmyk.py`: blend attribute.
- `software/tests/test_cmyk_tab.py`: assertion.
