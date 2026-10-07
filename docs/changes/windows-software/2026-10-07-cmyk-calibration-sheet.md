---
id: WSW-20261007-007
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
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - calibration
  - test-print
  - color-separation
  - tools
related:
  - WSW-20261007-001
  - WSW-20261007-003
  - WSW-20261007-005
---

# Add a labeled CMYK calibration sheet and scan tool

## Summary

The CMYK tab gains a **Test sheet** mode. With it checked, Preview and Save
build a labeled calibration page instead of the artwork: per-ink coverage
ladders (10-100 %), dot-size ladders (20-140 % at 50 % tone), overdraw
ladders (1x/2x/3x), a GCR ramp on 50 % gray (0/25/50/75/100 %), full-tone
pair mixes (C+M, C+Y, M+Y, C+M+Y), dense single-ink spots, a blank paper
patch, and four dense corner fiducials with all-ink cross arms. Every cell
is labeled with its parameter value. Saving writes
`<name>-calibration-<ink>.gcode` plus `<name>-calibration.json`; the new
`tools/cmyk_calibrate.py` maps a flat scan or photo of the plotted sheet onto
that manifest, samples every patch, and reports the paper-relative ink
transmittances plus a measured-vs-predicted check of the multiply model on
the mix patches.

## Reason

The preview still draws each ink opaquely, so screen inspection cannot show
how translucent inks will actually overprint. The only ground truth is a
printed sheet with known, labeled patch values read back numerically - the
same idea as a desktop printer's numbered calibration page. The sheet also
gives the print-side knobs (dot size, overdraw, GCR, gamma) values the
owner can pick from the paper, and gives the preview-side ink model real
transmittance numbers instead of guessed display colours.

## Implementation

- `software/generator_tabs/cmyk_sheet.py`: sheet layout, per-cell screening
  through `converter_core.cmyk.screen_channel` at the tab's current pitch,
  dot size, pen width, and overdraw, Hershey stroke labels drawn by the
  black pen, corner fiducials, and the JSON-ready manifest. The sheet always
  uses the halftone dot screen with solid spiral dots; ladder cells print
  raw tone (weights are not applied) so dot size and dot gain can be judged;
  the GCR ramp runs the real separation with the page's weights and gamma.
  Cell height is computed from the remaining page space, and pages below
  roughly 110 x 180 mm are refused with a hint.
- `software/generator_tabs/cmyk_tab.py`: the **Test sheet** checkbox in a
  new Calibration group; the layer cache key includes the mode; sheet mode
  needs no artwork; Save uses the `-calibration` base name and writes the
  manifest next to the G-code files.
- `tools/cmyk_calibrate.py`: corner-fiducial detection (dark neutral blobs
  with aspect/fill filters), least-squares homography from page millimetres
  to pixels, trimmed-mean patch sampling, transmittances from the dense
  spots, multiply validation on the mixes, a `--corners` manual override,
  and a profile JSON (`cmyk-ink-profile`).

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 361
  tests (1 skipped: the pre-existing headless shader compile).
- New `software/tests/test_cmyk_sheet.py` (7 tests): block census and
  fiducials, patch rectangles inside the content box, GCR channel split at
  the 0 % and 100 % ends, small-page rejection, determinism, recovery of
  known ink transmittances from a synthetic rotated scan (within 0.06), and
  the CLI profile write.
- New tab tests: sheet mode builds all four layers and writes the manifest
  next to the saved files, works without artwork, changes the layer cache
  key, and reports small pages.
- The default sheet was rendered to PNG and visually inspected: labels,
  ladders, GCR ramp, mixes, and fiducials all fit the 200 x 200 mm page.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Fitting four captions, ten ladder rows, and header/footer text into the
  default 200 x 200 mm page needed a computed cell height; a fixed cell
  height either overflowed or wasted space. Smaller pages now raise a clear
  error instead of silently clipping.
- Corner-fiducial detection initially risked matching dark K dot fields or
  text glyphs; the detector now requires dark neutral blobs with square-ish
  aspect and high fill and picks the largest per corner window, with
  `--corners` as a manual fallback.
- Applying per-ink weights to the ladder cells was rejected: it would mix
  two effects, and the ladders must show raw tone. Only the GCR ramp runs
  the full separation, and the sheet header prints the active weights.

## Risks and follow-up

- The sheet has not been plotted on paper yet; the next action is a real
  four-pass print and scan, which is exactly what the sheet is for.
- The multiply check may legitimately report that a pen set deviates from
  the ideal model; the profile keeps both measurements and errors so the
  preview work can decide between pure multiply and a corrected model.
- The preview still draws opaque per-ink colours; wiring the measured
  profile into a multiply print-simulation preview is a follow-up
  milestone.

## Files

- `software/generator_tabs/cmyk_sheet.py`: sheet layout, screening, manifest.
- `software/generator_tabs/cmyk_tab.py`: Test sheet mode, save naming, and
  manifest output.
- `tools/cmyk_calibrate.py`: scan sampling and ink-profile report.
- `software/tests/test_cmyk_sheet.py`, `software/tests/test_cmyk_tab.py`:
  coverage for the sheet, the tool, and the tab mode.
- `software/README.md`: CMYK section documents the sheet and the tool.
