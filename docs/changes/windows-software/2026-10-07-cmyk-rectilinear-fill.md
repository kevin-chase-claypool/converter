---
id: WSW-20261007-020
date: 2026-10-07
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/cmyk_sheet.py
  - tools/cmyk_calibrate.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_sheet.py
tags:
  - cmyk
  - screening
  - rectilinear
  - pen-cycles
related:
  - WSW-20261007-019
  - WSW-20261007-014
---

# Add a rectilinear fill screen that joins rows

## Summary

New CMYK screen style **Rectilinear fill (joined rows)**: parallel rows whose
pitch follows tone like the line screen, but consecutive overlapping runs are
stitched into serpentine chains joined over ink, so a connected region costs
one M3/M5 cycle instead of one per row. Row direction alternates at each
join; rows keep their ink's classic screen angle; the connector hop is only
drawn when its midpoint is over ink, so a chain never crosses blank paper.
Overdraw passes keep the same directional sub-pen offsets as other styles.

Two density fixes came with it: the **Dot pitch** floor drops from 0.6 mm to
0.1 mm (coverage is roughly pen width / pitch, so a 0.3 mm pen at 1.2 mm is
~25 % ink, at 0.6 mm ~50 %, and below ~0.3 mm the fill fuses solid), and the
calibration sheet's pitch ladder now sweeps 0.25-2.4 mm (sheet version 7)
with `rectilinear` available as a sheet screen and as a
`cmyk_calibrate.py --screen` choice.

## Reason

Owner: "if it would help to reduce the number of m3s and m5s maybe we should
have a rectilinear fill", then "i've tried to make it more dense, but this is
as dense as the rectilinear lines will go." The 0.6 mm pitch floor capped the
achievable ink coverage at pen width / pitch.

## Implementation

- `software/converter_core/cmyk.py`: `_line_runs(..., connect=True)` collects
  per-row runs in the local frame and `_stitch_runs` joins overlapping runs
  of consecutive rows into serpentine chains, choosing the nearest end so
  the stroke alternates direction; a join requires the connector midpoint to
  sample at or above the run threshold. New `rectilinear` style dispatch.
- `software/generator_tabs/cmyk_tab.py`: style entry and tooltip; pitch
  range 0.1-8 mm.
- `software/generator_tabs/cmyk_sheet.py`: `rectilinear` sheet screen with
  the pitch ladder; ladder sweep 0.25/0.4/0.6/0.9/1.2/1.8/2.4 mm.
- `tools/cmyk_calibrate.py`: `rectilinear` accepted by `--screen`.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 383
  tests (1 skipped: the pre-existing headless shader compile). New tests:
  a uniform field joins into exactly one chain with fewer polylines than the
  line screen, a blank band splits the chain, every style builds all four
  layers (rectilinear included), the sheet's rectilinear ladder values, and
  the 0.2 mm pitch floor.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Relying on the planner's keep-down bridges was rejected: bridging requires
  `FillTrail` geometry plus the Convert tab's keep-down setting, and it
  disables the per-ink preview colours. The screen pre-joins the rows
  instead, so the saving applies everywhere with no settings involved.

## Risks and follow-up

- At the 180-degree turns the pen never lifts; any lag or dwell there can
  leave a slightly heavier speck at the row ends.
- Very small pitches multiply rows (and ink load); paper wetness should be
  checked before using sub-0.3 mm pitches on large fills.

## Files

- `software/converter_core/cmyk.py`: serpentine run stitching.
- `software/generator_tabs/cmyk_tab.py`: style, pitch range.
- `software/generator_tabs/cmyk_sheet.py`: rectilinear sheet screen.
- `tools/cmyk_calibrate.py`: `--screen` choice.
- `software/tests/test_cmyk_tab.py`, `test_cmyk_sheet.py`: coverage.
