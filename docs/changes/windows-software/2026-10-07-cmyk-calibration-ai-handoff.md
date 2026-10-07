---
id: WSW-20261007-009
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_sheet.py
  - tools/cmyk_calibrate.py
  - software/tests/test_cmyk_sheet.py
  - docs/testing/CMYK_CALIBRATION.md
  - docs/README.md
  - software/README.md
tags:
  - cmyk
  - calibration
  - test-print
  - ai-handoff
  - tools
related:
  - WSW-20261007-007
  - WSW-20261007-008
---

# Make CMYK calibration scans analyzable from the image alone

## Summary

The print-scan-analyze workflow now lives in the repository
(`docs/testing/CMYK_CALIBRATION.md`, linked from the documentation map and
the CMYK section of `software/README.md`), so a future AI session can work
from a scanned image with no extra context. To make that possible without a
saved manifest: the sheet header now prints the page size and margin on its
own line, and `tools/cmyk_calibrate.py` can rebuild the deterministic layout
from those numbers (`--layout 216x279 --margin 6 --screen crosshatch`).
`build_sheet(..., marks=False)` produces the manifest without screening any
marks, so the rebuild matches a plotted sheet exactly. The tool's default
profile path is now `<scan stem>-profile.json`.

While adding the page line, measuring the Hershey text widths found real
overflows (the longest header/caption lines were up to 175 mm on a 166 mm
content box). The header is now four short lines, the long strings are
shortened, and `build_sheet` computes the required text width from the font
metrics and raises a page-size hint with the actual minimum instead of
letting text run off the sheet.

## Reason

Owner: the calibration documentation "should be within github so you can
reference it later. i should only need to give you the scanned image." The
manifest is written next to the G-code, but the analysis must also work when
only the scan is provided, and the sheet must not silently overflow.

## Implementation

- `docs/testing/CMYK_CALIBRATION.md`: the complete handoff - what the image
  is, the header format, both analysis commands (saved manifest, or rebuild
  from page size / margin / screen), the `--corners` fallback, and how to
  read the profile output (`inks`, `validation`, `blocks`, `paper_rgb`).
- `docs/README.md`: task-map row for the handoff; `software/README.md`
  links it from the CMYK section.
- `software/generator_tabs/cmyk_sheet.py`: four-line header (title, page +
  margin, screen token `lines`/`dots`/`crosshatch` with its values, GCR /
  gamma / weights); `marks=False` manifest-only builds; computed text-width
  guard with a minimum-page message.
- `tools/cmyk_calibrate.py`: `--layout PAGE_WxPAGE_H`, `--margin`,
  `--screen` rebuild the manifest through `cmyk_sheet.build_sheet(marks=
  False)`; `--manifest` is now optional; the report names its layout source.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 368
  tests (1 skipped: the pre-existing headless shader compile).
- New tests: the manifest-only build matches the marked sheet's rectangles,
  labels, and fiducials while returning empty layers; the CLI rebuilds the
  layout with no manifest and recovers the known ink numbers from a
  synthetic scan; and a layout source is required.
- Rendered the line and crosshatch sheets (200 x 200 mm) and confirmed all
  ink stays within the page (max extent 193.5 mm, the fiducial arms) with
  the new header readable.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- The first header attempt put page and margin on the title line and ran to
  216 mm on a 200 mm page. Measuring every string exposed the same problem
  in existing captions, so the header was split and the guard now derives
  the minimum page from the actual font metrics.
- Duplicating the layout inside the tool was rejected; the tool imports
  `cmyk_sheet` and rebuilds through the same code path, keeping one source
  of truth.

## Risks and follow-up

- The scan-only path relies on the printed header being legible; a deep
  crop also needs `--corners` for the fiducials.
- Wiring the measured profile into the multiply print-simulation preview
  remains the follow-up; the handoff doc states that contract.

## Files

- `docs/testing/CMYK_CALIBRATION.md`: AI handoff for a calibration scan.
- `docs/README.md`, `software/README.md`: links to the handoff.
- `software/generator_tabs/cmyk_sheet.py`: header, manifest-only builds,
  text-width guard.
- `tools/cmyk_calibrate.py`: manifest-free rebuild path.
- `software/tests/test_cmyk_sheet.py`: rebuild and guard coverage.
