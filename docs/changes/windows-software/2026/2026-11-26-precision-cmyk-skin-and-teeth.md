---
id: WSW-20261126-002
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - tools/export_cmyk_headless.py
  - software/tests/test_cmyk_edge_flow.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_headless.py
  - samples/gcode/fam-precision-2026-11-25/
  - software/README.md
  - docs/integration/INTERFACES.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - process-color
  - precision-screen
  - color-rendering
  - skin
  - facial-detail
  - teeth
  - highlight-preservation
  - headless-export
  - deterministic
  - physical-validation-pending
related:
  - WSW-20261125-013
  - WSW-20261125-012
---

# Correct precision CMYK skin color and facial detail

## Summary

Rejected the 2026-11-25 Golden Sunset precision output after reproducing its
violet/gray skin, weak facial structure, and lost tooth bands. The headless
comparison had swapped C/M/Y/K transmittance identities onto the Y/M/C/K print
layers, the source panel did not share the generated page fit, and the
precision recipe used under-saturated image controls. The corrected precision
workflow now preserves image-aware skin color, broad highlights, eye and smile
structure, and digital tooth bands while retaining the existing page,
registration, Y/M/C/K order, transactional export, and bed compensation.

## Reason

The controlled set at
`samples/gcode/fam-precision-2026-11-25/` was not an acceptable color target.
The first numerical check separated renderer error from separation error:

- A representative skin patch changed from source `[207, 131, 104]` to process
  `[147, 127, 173]` in the contact sheet, an approximately `-60 Red / +69 Blue`
  shift consistent with yellow and cyan being rendered as each other.
- The headless renderer zipped the C/M/Y/K transmittance matrix to
  `PRINT_CHANNELS = Y/M/C/K`; the G-code and ink assignments were correct, but
  the evidence image was not.
- The source comparison panel filled its whole 570-pixel panel while the
  generated process image occupied the `240 mm` drawable area inside the
  `250 mm` page. That introduced a further scale/offset mismatch.
- Correcting only the transmittance identity restored a warm hue but retained
  about `9.9` mean RGB levels of error over five skin patches. The process
  cells also lacked a mechanism to preserve a bright tooth band after a cell's
  average tone had been diffused.

## Implementation

- `tools/export_cmyk_headless.py` now zips nominal or measured transmittances
  by `converter.CHANNELS` (C/M/Y/K) while keeping the physical print order
  Y/M/C/K. Its source panel is aspect-fitted into the same page and margin
  frame as the ink layers.
- The precision recipe is explicit: auto levels off, brightness `100 %`,
  saturation `106 %`, contrast `122 %`, gamma `1.00`, GCR `65 %`, a `60 %` /
  `1.50 mm` unsharp mask, and C/M/Y/K weights `100/100/100/100 %`.
- `screen_process_color_area_cmyk()` moves each selected mark toward that
  ink's local tone centroid within its cell. The Black centroid includes the
  keyline field, so structure remains aligned while average plate coverage is
  unchanged.
- Broad positive highlights can remain paper after diffusion. A cell is
  protected when at least `40 %` of its footprint has local detail `>= 0.16`
  and scene luma `>= 0.45`, using a `1.5 mm` background radius. This keeps
  eyes, glasses, and tooth bands from being filled by unrelated process cells.
- The set manifest records the highlight thresholds, detail alignment, and
  resolved `0.9876543209876543 mm` cell pitch separately from the requested
  `0.35 mm` layout control. The workflow validation evaluates the resolved
  pen-floor pitch, eliminating the previous false warning.

## Verification

- The focused CMYK edge-flow, tab, and headless paths passed `111` tests.
- A subsequent focused tab run passed `72` tests after making
  `auto_levels=false` explicit in the recipe.
- The complete focused CMYK suite passed `177` tests. Complete converter
  discovery passed `755` tests in `212.572 s` with one expected OpenGL-context
  skip. Python compilation passed for all changed Python modules.
- Two complete full-size application exports produced identical program bytes
  and identical manifests after excluding `created`.
- Final mark counts are Yellow `26250`, Magenta `23293`, Cyan `13079`, and
  Black `12414` (`75036` total). Final maximum XY radii are
  `174.272/174.204/174.364/174.236 mm`, all inside the `180 mm` reach guard.
- Every program contains `G21/G90/G94/G17/G54`, ends with `M2` after a pen
  clear, shares one frame/theta/feed/compensation identity, and reports a
  complete transactional set with zero over-tolerance moves at `0.05 mm`.
- `tools/check_gcode_motion.py --strict` passed all four programs. Largest
  per-move bed rotation is `2.05 deg`; largest A demand is
  `269 motor deg/s`; there are no bare `G0` rotations.
- Across five representative skin patches, mean modeled RGB error is `8.4`
  levels, down from approximately `9.9` under the corrected prior controls.
  Mean eye/mouth gradient correlation rises from approximately `0.097` to
  `0.140`. A `387175`-byte, three-face digital crop keeps eyes, glasses,
  smiles, and white tooth bands visible.
- The 2026-11-25 output is retained only as historical commit evidence and is
  no longer the current controlled sample. The regenerated seven-file set,
  manifest, verification report, and `536109`-byte comparison image supersede
  it in place.

## Struggles and rejected approaches

Increasing ink weights or lowering GCR alone did not address the dominant
violet shift because the transmittance identity was wrong. A blanket
max-brightness knockout was rejected after protecting `35-46 %` of cells and
removing facial structure. Joint 16-state color quantization stayed close in
mean RGB but reduced Cyan coverage from about `19 %` to `7 %` and shifted too
much density into Black. Coherent-flow and edge-streamline Black overlays
darkened skin and still did not recover the child's tooth separations. The
accepted path gates only broad positive highlights and moves selected marks
without changing their plate selection or long-run count.

## Risks and follow-up

This remains digital renderer evidence. Physical paper is unavailable for this
session, so paper hue, ink density, overprint texture, four-pass registration,
drag, elapsed time, and felt-tip spread remain unverified. In particular,
individual tooth gaps smaller than the `0.90 mm` pen may merge even though the
white tooth bands are visible in the digital face crop.

The next physical gate is one `G65 P113` HOME + REGISTER followed by the four
numbered programs back to back. Inspect skin hue, eye/glasses continuity,
smile and tooth-band readability, highlight cleanliness, black keyline
overdraw, registration, drag, and elapsed time before changing the recipe
again.

## Files

- `software/converter_core/cmyk.py`: highlight gate, cell tone-centroid
  alignment, shared process-grid helper, and deterministic recursion.
- `software/generator_tabs/cmyk_tab.py`: explicit precision controls, resolved
  pitch, manifest detail metadata, and corrected stage validation.
- `tools/export_cmyk_headless.py`: channel-correct comparison rendering,
  page-framed source panel, and effective-pitch reporting.
- `software/tests/test_cmyk_edge_flow.py`: highlight-preservation and
  sub-cell-centroid regressions.
- `software/tests/test_cmyk_tab.py`: recipe and renderer-forwarding coverage.
- `software/tests/test_cmyk_headless.py`: transmittance identity and source
  frame regressions.
- `samples/gcode/fam-precision-2026-11-25/`: replacement deterministic set and
  compressed comparison evidence.
- `software/README.md`: current recipe, detail behavior, and measured limits.
- `docs/integration/INTERFACES.md`: manifest and verification metadata.
- `docs/project/ROADMAP.md`: rejected candidate, replacement evidence, and
  remaining physical gate.
