# CMYK calibration: print, scan, analyze (AI handoff)

When the project owner provides a scan or photo of the CMYK calibration
sheet, this page is the complete instruction set. The image plus this
repository is enough; no extra context needs to be supplied.

The sheet is plotted from the CMYK tab's **Test sheet** mode
([`../../software/README.md`](../../software/README.md), CMYK section;
layout in [`../../software/generator_tabs/cmyk_sheet.py`](../../software/generator_tabs/cmyk_sheet.py)).

## The image

A quiet calibration sheet: the only printed text is a two-line identification
header. The marks are per-ink coverage ladders, per-ink step ladders with the
overdraw cells at the end of each row, a GCR ramp, dense mix patches (C+M,
C+Y, M+Y, C+M+Y, C+M+Y+K) printed at the same tight spacing as the dense
single-ink spots, a blank paper patch, and four dark square fiducials in the
corners with all-ink cross arms. Row order
from the top: C, M, Y, K coverage; C, M, Y, K steps plus overdraw; GCR
ramp; mixes, spots, paper.

The printed header is the minimum needed to match a scan to this layout:

1. `CMYK CALIBRATION - page <W>x<H> mm | margin <M> mm`
2. `screen lines | pitch <P> mm`, `screen dots | pitch <P> mm | dot <D>%`,
   or `screen crosshatch | pitch <P> mm | levels <L>`

## Analyze

1. Prefer a saved manifest - `<name>-calibration.json` (kind
   `cmyk-calibration-sheet`) is written next to the G-code at Save time:

   ```text
   python tools\cmyk_calibrate.py scan.png --manifest <name>-calibration.json
   ```

2. Scan only: read the page size, margin, and sheet screen from the header
   and rebuild the deterministic layout. `--pitch` and `--levels` are
   descriptive only; include them when the header shows them:

   ```text
   python tools\cmyk_calibrate.py scan.png --layout 216x279 --margin 6 --screen crosshatch --pitch 0.6 --levels 4
   ```

3. If fiducial detection fails (cropped or cluttered image), add
   `--corners x1,y1,...,x4,y4` with the fiducial centres in pixels, order
   top-left, top-right, bottom-left, bottom-right. The scan must show the
   whole sheet with all four fiducials, flat and evenly lit.

The tool writes `<scan stem>-profile.json`.

## Read the output

- `inks.c/m/y/k` - paper-relative ink transmittance at full coverage. These
  are the multipliers for the print-simulation preview:
  `result = paper x C x M x Y x K` in C, M, Y, K plot order.
- `validation` - measured vs predicted values for the mix patches. A small
  mean error (about 8/255 or less) means pure multiply matches this pen set;
  a large error means the printed mixes are the ground truth for that
  pen/paper and the preview needs a correction.
- `blocks` - coverage, step, overdraw, and GCR reflectance tables for
  recommending control changes (gamma, pitch, overdraw, GCR, weights).
- `paper_rgb` - the white reference sampled from the blank PAPER cell.

## Then

Report the ink numbers and the multiply verdict. These profile numbers are
the input for the CMYK multiply print-simulation preview (follow-up to
`WSW-20261007-007`); keep profiles named by pen set and paper, because a
pen, paper, or pressure change invalidates them.
