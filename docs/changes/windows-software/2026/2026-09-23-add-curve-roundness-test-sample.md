---
id: WSW-20260923-004
date: 2026-09-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core
tags:
  - sample
  - gcode
  - curve-flattening
---

# Add a curve-roundness test sample

## Summary

Added `samples/svg/curve-roundness-test.svg`: three same-radius "circles" drawn
three ways, plus an ellipse and a cubic-bezier path, so the converter's curve
flattening can be compared directly in one plot.

## Reason

The house-and-sun's sun is a 12-sided polyline, so it plots as a visibly
facetted dodecagon no matter what settings are used. There was no sample that
demonstrated the difference between a polygon and a real curve element, which is
the actual lever for roundness (the `tolerance` setting, which flattens
`<circle>`/`<ellipse>`/bezier geometry).

## Implementation

- `samples/svg/curve-roundness-test.svg`: stroke-only (`fill="none"`), so the
  converter draws centerlines. Contains, left to right, a 12-sided polygon, a
  true `<circle>`, and a 36-sided polygon of the same radius; below them an
  `<ellipse>` and a cubic-bezier `<path>`.

## Verification

- Converts to 5 contours, one `M3` each. Point counts per element: 12-gon 13,
  `<circle>` 361, 36-gon 37, ellipse 361, bezier 241 — the curve elements are
  flattened finely, the polygons are not.
- `python tools\docs_index.py --write` and `--check` pass. Bench plot still
  required to confirm the visual result.

## Struggles and rejected approaches

Editing the house-and-sun's sun rather than adding a sample was rejected: that
sample is a known-good motion reference, and changing it would disturb existing
comparisons.

## Risks and follow-up

`<path>` arc commands (`A`) are parsed as a straight line to the endpoint, so
arc-based circles would still plot as chords. The sample uses `<circle>` and
bezier geometry, which are handled; fix the arc handling separately if a source
tool emits arcs.

## Files

- `samples/svg/curve-roundness-test.svg`: new sample.
