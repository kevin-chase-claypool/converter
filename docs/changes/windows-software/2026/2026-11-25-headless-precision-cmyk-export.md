---
id: WSW-20261125-013
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - tools/export_cmyk_headless.py
  - software/tests/test_cmyk_headless.py
  - samples/gcode/fam-precision-2026-11-25/
  - software/README.md
  - docs/integration/INTERFACES.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - process-color
  - headless
  - deterministic
  - transactional-export
  - verification
  - facial-detail
  - physical-validation-pending
related:
  - WSW-20261125-012
  - WSW-20261125-009
  - ADR-010
---

# Export and verify a precision CMYK set headlessly

## Summary

Added a headless application driver that selects the real **CMYK Photo** tab,
applies a complete workflow recipe, runs the normal four-program planner and
save path, and publishes through the transactional program-set API. The
driver verifies the resulting set, repeats the export for byte determinism,
and creates one compressed comparison preview from the tab's actual C/M/Y/K
layers.

The candidate Golden Sunset set uses the stabilized precision process screen at
the accepted `250 mm` page, `0.90 mm` pen, `0.35 mm` requested pitch,
`0.05 mm` tolerance, seed `7`, and `800000` marks-per-ink cap. It contains
four registered Y/M/C/K programs and a version-8 manifest.

## Reason

The renderer and transactional exporter were independently tested, but there
was no repeatable end-to-end driver proving that a real source image produces
a complete registered set through the application path. A visible Qt attempt
was blocked at an approval gate. An ad-hoc SVG or G-code path would not prove
the tab recipe, shared frame, planner, preflight, manifest, or transaction.

The prior coherent-flow Golden Sunset set also demonstrated the product
decision: its long blue streamlines obscured faces and teeth. The precision
process screen needed a bounded digital comparison before any paper run.

## Implementation

- The now-removed `tools/export_cmyk_headless.py` loaded the real application
  module in an offscreen Qt session, selected **CMYK Photo**, applied the named
  workflow preset, called `build_svg()` and `save_all()`, and used
  `MainWindow.export_program_set` for publication.
- The verifier checks all four expected files and the manifest, source and
  program hashes, Y/M/C/K print order, `G21/G90/G94/G17/G54`, `M2` and final
  pen-up state, common frame/theta/feed/reach/compensation headers, per-ink
  motion preflight, mark counts, artwork-page bounds, machine-reach bounds,
  registration, and common set identity.
- A default second full run is compared against the first. Program bytes must
  match exactly; the manifest must match after excluding only its creation
  timestamp.
- The evidence preview multiplies the actual generated ink layers in Y/M/C/K
  order using the converter's `process-ink-multiply-v1` transmittance model.
  The comparison re-applies the complete precision recipe and changes only
  the screen style, so the coherent and process panels share one page,
  placement, registration, pen order, seed, scale, pen width, and image-control
  contract. It is saved as a compressed JPEG and rejected above `750000` bytes.
- The generated set and evidence are in
  [`samples/gcode/fam-precision-2026-11-25/`](../../../../samples/gcode/fam-precision-2026-11-25/).

## Verification

- Full app-path export passed twice. All four program hashes matched between
  runs, and the manifests matched except for `created`.
- Manifest version is `8`; print order is `01-yellow`, `02-magenta`,
  `03-cyan`, `04-black`; all four programs report transactional whole-set
  publication, complete channels, common set identity, and motion preflight
  success.
- Mark counts are Yellow `23923`, Magenta `23024`, Cyan `16271`, and Black
  `1683` (`64901` total), below the `800000` per-ink cap.
- Every requested page bound is inside `250 x 250 mm`: all four layer extents
  are `0.400 .. 249.600 mm`. The largest final G54 XY radius is
  `174.383 mm` against the `180 mm` reach guard.
- There are zero over-tolerance moves at `0.05 mm`. The largest bed rotation
  in one drawing move is `2.06 deg`; the largest A rate is
  `269 motor deg/s` against the `500` preflight limit; there are no bare `G0`
  rotations.
- `tools/check_gcode_motion.py --strict` passed on all four programs.
- The controlled comparison report records matching process/coherent controls:
  `250 x 250 mm`, `5 mm` margin, `100 %` scale, `0.90 mm` pen, seed `7`,
  registration on, optimized bed motion, Y/M/C/K order, brightness `112 %`,
  saturation `92 %`, contrast `118 %`, GCR `28 %`, gamma `1.05`, sharpen
  `45 % / 0.80 mm`, and C/M/Y/K weights `100 / 95 / 90 / 30 %`.
- Compared with the earlier coherent-flow Golden Sunset manifest
  (`fam1`), total marks rise from `9147` to `64901`, while over-tolerance
  moves fall from `30` at `0.10 mm` to `0` at `0.05 mm`. The maximum
  per-move bed step falls from `9.434 deg` to `2.060 deg`.
- The single inspected `544895`-byte comparison image shows all three faces,
  eye and glasses structure, and hair in the precision process render. The
  coherent-flow panel remains dominated by dense blue contour flow and loses
  facial readability. Individual teeth are not yet distinguishable at this
  contact-sheet scale, so teeth visibility remains an explicit product
  decision rather than a claimed pass. The reference is a different subject
  and is used for screen/color behavior, not pixel matching.
- The requested `0.35 mm` process pitch is below the pen-safe centerline
  floor. With the `0.90 mm` pen and `5 mm` margin, the renderer resolves a
  `0.99 mm` spacing into `243` cells across `240 mm`, i.e. `0.98765 mm`
  actual axis pitch.
- Focused CMYK separation, image, screen, wave, contract, tab, and headless
  tests passed `173` tests. Complete converter discovery passed `750` tests in
  `220.256 s` with one expected OpenGL-context skip.
- No physical four-pass paper set was produced. Paper hue, ink density,
  overprint texture, pen registration, drag, and elapsed time remain
  unverified.

## Struggles and rejected approaches

The visible Qt workflow was unavailable behind an approval gate. Generating
SVG or G-code directly was rejected because it would bypass the tab recipe,
shared page identity, planner preflight, and transactional publication.

The first headless wait expected the tab's cached analysis key to remain
identical after the worker finished. The save itself completed successfully,
but that derived state changed during teardown. The driver now waits for the
tab's explicit "Saved 4 G-code files" result plus all five transaction
targets instead. A reduced `50 mm` export caught this before the full run.

Offscreen Qt reports unavailable OpenGL and WebEngine teardown warnings. They
do not affect the nonvisual export path; the single preview is rendered from
the tab's actual layer geometry and ink model rather than an unavailable GL
framebuffer.

## Risks and follow-up

The process manifest records the requested pitch rather than the resolved
pen-floor cell pitch. The verification report and this note record the
`0.98765 mm` actual axis pitch for the selected pen. Add the resolved pitch
and cell dimensions to a future manifest revision if operators need them
without inspecting the verification evidence.

The digital comparison establishes structure and reproducibility, not paper
calibration. Teeth detail is the visible product boundary: the candidate keeps
faces and features but does not yet demonstrate separated teeth at contact
sheet scale. Do not tune pitch, channel weights, or keyline density
speculatively. The next decision is whether to prioritize teeth/detail over
current color texture and density, then validate that choice with one HOME +
REGISTER followed by the four numbered files in order on one sheet.

## Files

- `tools/export_cmyk_headless.py`: real-tab headless export, verification,
  determinism repeat, and comparison preview.
- `software/tests/test_cmyk_headless.py`: application-path export and bounds
  regressions.
- `samples/gcode/fam-precision-2026-11-25/`: candidate four programs, version-8
  manifest, verification report, and compressed comparison.
- `software/README.md`: operator/tool documentation and current test count.
- `docs/integration/INTERFACES.md`: headless publication contract.
- `docs/project/ROADMAP.md`: completed digital milestone and remaining paper
  validation.
- `docs/project/ENGINEERING_LOG.md`: chronological evidence and failed
  headless-wait assumption.
