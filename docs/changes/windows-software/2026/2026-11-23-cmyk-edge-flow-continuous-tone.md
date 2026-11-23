---
id: WSW-20261123-003
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/structure_tensor.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - edge-flow
  - continuous-tone
  - tone-response
  - auto-exposure
  - highlight-gradient
  - portrait
related:
  - WSW-20261123-002
  - docs/proposals/flow-field-cmyk.md
---

# Preserve continuous color tone in edge-flow CMYK

## Summary

Edge-flow CMYK now varies the inked fraction along each streamline with local
channel tone instead of drawing every path above the ink floor at full
density. The CMYK **Auto (photo)** action also uses a separate exposure and
color recipe for edge flow, and opens an unrealistically fine pitch to at
least `1.5` pen widths. Bright warm highlights can therefore retain the
separate yellow-to-magenta transition visible in the reference print.

## Reason

The source `IMG_0514.JPG` had a substantial continuous yellow/magenta ramp in
the face: in the tested crop the 10th-to-90th percentile span of
`yellow - magenta` was `0.235`, and their channel correlation was `0.901`.
The old screen still rendered broad parts of the forehead as one dense
orange/red wash.

Two conversion behaviours caused that loss:

- The previous edge-flow layers activated at broad thresholds. Coverage below
  the next threshold produced the same full streamline density, creating wide
  tonal plateaus.
- The generic Auto search treated edge flow like a sparse rectilinear row
  screen. For the tested `0.8 mm` pen and `0.31 mm` effective pitch it chose
  `brightness 80 %`, `gamma 0.80`, and a pitch finer than the pen. The result
  had almost no paper left to express a light color ramp.

## Implementation

- Candidate streamline paths are traced through the existing strength-gated
  shared luminance field.
- Each CMYK plate evaluates its own processed tone along the path. A
  deterministic low-discrepancy threshold within `4-8 mm` paper cells keeps
  the local tone fraction of the path: highlights draw sparse segments, while
  shadows approach a continuous stroke.
- `Flow layers` remains the maximum number of offset networks. Additional
  layers activate in progressively darker tone bands, so they deepen shadows
  instead of making the lightest coverage binary.
- Edge-flow Auto preserves normal photo exposure, retains more CMY in warm
  midtones, and limits black extraction. At the tested portrait and pen/pitch
  settings it now selects `brightness 115 %`, `contrast 140 %`,
  `saturation 115 %`, `GCR 75 %`, and `gamma 1.10`.
- Auto raises an edge-flow effective pitch only when it is below `1.5` pen
  widths. The tested `0.31 mm` pitch becomes `1.2 mm` for a `0.8 mm` pen.
- The saved manifest records
  `strength_gated_shared_luminance_structure_tensor_continuous_tone`.

## Verification

- A new tone-ramp regression checks six brightness levels from `0.12` to
  `0.55`. Every step has strictly more streamline length; the brightest sample
  has over `3x` the length of the dimmest.
- A new Auto regression recreates a warm portrait ramp and verifies that edge
  flow keeps brightness at or above `100 %`, gamma at or above `0.90`, and
  opens an `effective pitch 0.31 mm` / `pen 0.8 mm` setup to at least
  `1.2 mm`.
- The focused CMYK tab suite passes all `116` tests.
- Complete converter discovery passes `636` tests with one expected
  OpenGL-context skip.
- An `800 px` software render of `IMG_0514.JPG` at `1.2 mm` effective pitch,
  three layers, and the new Auto recipe retains separate yellow, magenta,
  cyan, and black strokes through the face, clothing, wood, and background.
  The forehead now carries visible yellow/magenta density changes and white
  paper gaps instead of a solid red/orange field.
- No four-pen physical sheet has been printed and measured for this recipe.

## Struggles and rejected approaches

Changing only brightness and gamma made the source tone composite faithful but
did not restore the screen gradient; the full-density layer rule still
quantized it. Increasing the layer count also retained wide steps.

Using only seed-level acceptance produced longer paths but allowed one stream
to over-ink a tone change it crossed. Fine `1-2 mm` dither cells restored a
continuous ramp but fragmented the artwork into speckle. The selected
`4-8 mm` cells balance local color response with continuous pen strokes.

A lower GCR alone lightened the face but did not fix the missing ramp. A
brighter Auto pass alone restored exposure but still produced binary hatches.

## Risks and follow-up

The `4-8 mm` tone-cell range and the `1.5` pitch multiplier are software
heuristics selected from one portrait and synthetic tone ramps. Pen spread,
ink opacity, paper, and the final four-pass overlay can change the best
settings. A physical edge-flow sheet remains the next validation gate.

## Files

- `software/converter_core/structure_tensor.py`: continuous local tone
  response along streamlines and darker-band layer activation.
- `software/converter_core/cmyk.py`: edge-flow-specific Auto exposure,
  separation, and pitch guard.
- `software/generator_tabs/cmyk_tab.py`: current control guidance and manifest
  identifier.
- `software/tests/test_cmyk_tab.py`: continuous tone-ramp and Auto regressions.
- `software/README.md`: current edge-flow behavior, recipe, and pitch guidance.
- `docs/proposals/flow-field-cmyk.md`: implemented tone method and current
  starting pitch.
- `docs/project/ENGINEERING_LOG.md`: chronological evidence and rejected
  approaches.
