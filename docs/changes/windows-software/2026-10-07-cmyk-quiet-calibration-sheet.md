---
id: WSW-20261007-010
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_sheet.py
  - software/generator_tabs/cmyk_tab.py
  - tools/cmyk_calibrate.py
  - software/tests/test_cmyk_sheet.py
  - docs/testing/CMYK_CALIBRATION.md
  - software/README.md
tags:
  - cmyk
  - calibration
  - test-print
  - ai-handoff
  - line-screen
related:
  - WSW-20261007-009
  - WSW-20261007-008
---

# Strip the calibration sheet to what a scan needs

## Summary

The calibration sheet now prints only a two-line identification header:

1. `CMYK CALIBRATION - page <W>x<H> mm | margin <M> mm`
2. `screen lines | pitch <P> mm` (or `screen dots | pitch <P> mm | dot <D>%`,
   or `screen crosshatch | pitch <P> mm | levels <L>`)

All cell labels, captions, and the footer are gone; the cell values and
rectangles live in the manifest and in
[`docs/testing/CMYK_CALIBRATION.md`](../../testing/CMYK_CALIBRATION.md). With
the label strips removed the patch cells also grew (up to 26 mm tall), which
improves sampling, and the black pen no longer draws roughly 900 glyph
strokes - the K pass text drops from about 1,270 to 355 polylines on the
default sheet.

The fiducial detector was hardened to match: patches are now large and
square-ish enough to compete with the corner marks, so candidates are picked
by distance to each image corner (distinct marks, no window fractions) and
the four picks must be consistent in size or the tool asks for `--corners`.
`--pitch` and `--levels` were added to the layout rebuild for an accurate
report when the header shows them.

## Reason

Owner: "did you get rid of all of the extra text on the calibration sheet?
only put what the ai needs to analyze it." The AI pipeline reads the
manifest/layout, never the printed labels, so the labels were pure plot time
and clutter on a plotter that is slow at dense marks.

## Implementation

- `software/generator_tabs/cmyk_sheet.py`: sheet version 3; header reduced to
  the two identification lines; `_captions` and the caption/label/footer
  constants removed; cell height now uses the reclaimed space (clamped at
  26 mm); the text-width guard applies to the header only, so the sheet now
  fits pages from roughly 175 x 105 mm upward.
- `software/generator_tabs/cmyk_tab.py`: wording updated (quieter sheet, no
  "labeled" claim).
- `tools/cmyk_calibrate.py`: corner-distance fiducial picking with a
  size-consistency check; `--pitch`/`--levels` descriptive options for
  `--layout`.
- `docs/testing/CMYK_CALIBRATION.md`, `software/README.md`: document the
  quiet sheet, its row order, and the two-line header.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 369
  tests (1 skipped: the pre-existing headless shader compile).
- New test: every mark of the line, crosshatch, and dot sheets stays inside
  the page. The manifest-only build, GCR split, ladder sweeps, synthetic
  scan recovery, and CLI rebuild tests all still pass with the quiet layout
  and the new detector.
- Rendered the quiet line sheet (200 x 200 mm) and visually confirmed the
  header, unlabeled ladders, GCR ramp, mixes, spots, paper, and fiducials.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- The first detector used corner windows as image fractions, which broke
  once the sheet did not fill the frame and once patch cells grew; corner
  distance plus a size check is scale-free and frame-independent.
- Keeping labels in the preview but not on paper was rejected as extra
  machinery for no analysis benefit.

## Risks and follow-up

- The sheet is no longer readable by a human without the manifest or the
  handoff doc; that is intended for the owner's AI workflow.
- The scan-only path still needs the two-line header to be legible; deep
  crops need `--corners`.

## Files

- `software/generator_tabs/cmyk_sheet.py`: quiet layout, version 3.
- `software/generator_tabs/cmyk_tab.py`: wording.
- `tools/cmyk_calibrate.py`: corner-distance detector, rebuild options.
- `software/tests/test_cmyk_sheet.py`: page-bounds and rebuild coverage.
- `docs/testing/CMYK_CALIBRATION.md`, `software/README.md`: documentation.
