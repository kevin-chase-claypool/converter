---
id: WSW-20261127-008
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/wave_rows.py
  - software/tests/test_wave_rows_geometry.py
tags:
  - cmyk
  - wave-screen
  - fidelity
  - tone-density
  - ordered-dither
  - fragmentation
  - clearance
related:
  - WSW-20261127-006
  - ADR-009
---

# Add coarse 2-D tone cells to Wave fidelity

## Summary

`waves_fidelity` now makes deterministic tone-density decisions over coarse
along-row cells instead of using one threshold for a whole row. The cell field
is smoothed before normalization, and short hidden gaps are closed only when
they separate inked cells. The original fixed baseline lattice, shared phase,
amplitude envelope, and final exact clearance check remain in force.
`waves_fixed` geometry is unchanged.

## Reason

  One threshold per row cannot represent horizontal tone changes accurately.
  With the safe pen-plus-edge contract, it reduced the oracle from 16 to 11
  failures, but every ink still exceeded the full-image coverage-MAE limit and
  the portrait remained too light and colour-shifted. A local density field was
  needed to
make light cells sparse and dark cells continuous without introducing
per-raster-pixel breakup.

## Implementation

- Fidelity rows are divided into approximately `1.5` row-pitch cells, clamped
  to `1.5-3.0 mm`. At the live `1.15 mm` source pitch these are about
  `1.73 mm` before artwork scaling and `1.9 mm` in final paper space.
- Each `(row, along-cell)` pair receives a stable coordinate-mixed threshold.
  The threshold field is box-smoothed over eight neighbouring cells and
  normalized within the row before it is compared with smoothed ink coverage.
- A visible decision applies to the complete cell. A bounded one-cell hidden
  gap between two visible inked cells is closed so the threshold cannot turn
  into a coarse checkerboard of separate pen-down marks.
- Pixels below `INK_FLOOR` still remain paper, the fixed baselines remain
  integer multiples of pitch, and the existing shortest-segment clearance
  check still evaluates the emitted paths.
- Fidelity-only depth headroom was increased slightly so the existing
  `100% -> 150%` Depth intensity monotonicity regression remains true with
  the new visible-row set. The exact final clearance gate remains
  authoritative.
- Fidelity highlights retain 80% of the common carrier amplitude at the normal
  depth-intensity plateau, leaving 20% for local tonal variation while keeping
  Wave curvature visible across the whole image. Zero Depth intensity still
  collapses every emitted row to its baseline.

## Verification

- The required oracle command was run at `256 px` with the real Python 3.13
  interpreter:

  ```powershell
  tools\cmyk_wave_fidelity.py --recipe live-failed --style waves_fidelity --no-gcode --no-artifacts --render-pixels 256 --jobs 4
  ```

- Oracle failures fell from `11` to `7` under the safe pen-plus-edge
  contract. The remaining failures are worst-region colour delta-E, depth
  geometry delta (`0.0231 vs 0.05 mm`), median span in one crop, worst
  regional Wave amplitude (`0.2495 vs 0.50 mm`), and magenta/yellow/black
  coverage MAE. There is no relaxed-clearance failure in the current baseline.
- Full-image coverage MAE and correlation changed as follows:

  | Ink | MAE before | MAE after | Correlation before | Correlation after |
  |---|---:|---:|---:|---:|
  | C | `0.1922` | `0.1616` | `0.4937` | `0.6215` |
  | M | `0.2200` | `0.1882` | `0.5536` | `0.6538` |
  | Y | `0.2058` | `0.1964` | `0.6792` | `0.6919` |
  | K | `0.2170` | `0.1945` | `0.5041` | `0.5919` |

- Family-portrait RGB MAE is `0.1755`, lightness MAE `17.32`, structure
  correlation `0.8953`, luminance MAE `0.1751`, and edge correlation
  `0.4169`, all within their gates. Median global Wave peak-to-peak is
  `0.259/0.257/0.259/0.262 mm` for C/M/Y/K.
- Unscaled screening-path counts changed from C/M/Y/K
  `715/630/679/970` marks and `34202/54732/77771/40209` segments to
  `1152/941/390/1151` marks and
  `41725/71649/89611/48689` segments. Median mark spans are
  `5.39/9.17/41.38/5.39 mm`; the maximum marks in one row are
  `16/15/9/13`. This is bounded fragmentation rather than per-pixel output.
- `python -m unittest software.tests.test_wave_rows_geometry` passes all
  `14` tests, including deterministic cell variation, gap closing,
  minimum-run output, fixed-lattice, shared-phase, clearance, and live-pitch
  depth regressions.
- `python -m unittest software.tests.test_cmyk_tab` passes all `141` tests.

## Struggles and rejected approaches

- Independent full-range thresholds for every approximately `2 mm` cell
  improved the oracle from `11` to `8` failures, but increased C/M/Y/K marks
  to `3046/3531/1953/2906`; most C/M marks were under `2 mm`. That was
  rejected as unusable fragmentation.
- Increasing the cell to roughly `3 mm` reduced sub-`2 mm` marks to nearly
  zero, but recovered only `11 -> 10` failures and lost detail-edge margin.
- Closing only gaps whose coverage was at least half a nominal line width
  reduced over-inking, but marks returned to
  `1718/1799/692/1634`; it was rejected in favour of the smoothed field plus
  one-cell closing.
- Lowering the density scale to `0.82` worsened magenta regional bias beyond
  its gate. Smoothing over twelve cells instead of eight reduced coverage
  correlation and worsened colour delta-E.

## Risks and follow-up

- This is software geometry and composite-oracle evidence, not a physical
  print result. Ink spread, paper absorption, pressure, registration, and
  rotating-bed following error still require a low-pitch coupon.
- Magenta/yellow/black local coverage, worst-region Delta-E, one regional
  span/amplitude gate, and the material depth-change gate remain open. The
  changes are retained because every primary coverage and colour error
  improved and no safety or fragmentation gate regressed.
- Per coordination scope, current-state documentation, generated indexes,
  the engineering log, roadmap, commits, and pushes were not changed.

## Files

- `software/converter_core/wave_rows.py`: coarse 2-D ordered cell thresholds,
  deterministic threshold smoothing, bounded gap closing, and fidelity-only
  depth headroom.
- `software/tests/test_wave_rows_geometry.py`: cell determinism,
  gap-closing, minimum-run/fragmentation, and updated tone-density coverage.
