---
id: WSW-20261123-005
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - edge-flow
  - auto-exposure
  - tone-density
  - portrait
related:
  - WSW-20261123-003
  - WSW-20261123-004
  - docs/proposals/flow-field-cmyk.md
---

# Make Edge-flow Auto preserve portrait density

## Summary

The CMYK **Auto (photo)** action now adjusts only image processing for
Edge-flow. It no longer changes the saved Dot pitch or artwork scale. Its
Edge-flow curve now keeps enough midtone ink for the path-local tone segments
to show the yellow-to-magenta portrait gradient instead of producing a sparse
sketch.

## Reason

After the previous continuous-tone change, the owner pressed Auto on
`IMG_0514.JPG` and the portrait became noticeably lighter and more fragmented.
The saved recipe had `0.31 mm` source pitch at `260 %` scale, `4.0 mm` Flow
smoothing, and five Flow layers. Auto changed that pitch to `0.45 mm` and
selected brightness 115 %, contrast 140 %, saturation 115 %, GCR 75 %, and
gamma 1.10.

A software comparison at the saved artwork scale showed that the pitch change
was not the main loss. The old Auto curve reduced mean channel coverage from
about `52 %` to `32 %`; leaving the pitch fixed but retaining the same curve
still produced the same sparse portrait. The lifted brightness and ink gamma
removed the midtone strokes that distinguish yellow from magenta in the face.

## Implementation

- Edge-flow Auto returns image controls only. Dot pitch is operator-owned
  persisted layout and remains unchanged.
- The Edge-flow curve now holds normal brightness for the current portrait,
  strengthens midtone contrast, and lowers ink gamma enough to retain local
  color density after path-local gating. For this source it selects brightness
  100 %, contrast 235 %, saturation 120 %, GCR 85 %, and gamma 0.70.
- The tab passes its configured resolution into Auto analysis instead of
  evaluating the source at the API's smaller default.
- Wave Auto and all other screen styles keep their existing behavior.

## Verification

- The mixed-density regression checks both the selected curve and the mean
  per-channel tone coverage after `prepare_image_tones`.
- A tab regression verifies Edge-flow Auto leaves a `0.31 mm` pitch unchanged
  at `260 %` artwork scale.
- A software render of `IMG_0514.JPG` using the new Auto values and the saved
  five-layer, `4.0 mm`-smoothing recipe restores separate yellow, magenta,
  cyan, and black density through the face. The old Auto render remains
  visibly sparse in the same comparison.
- The new tone-coverage and preserved-pitch regressions pass. Complete
  converter discovery passes `638` tests with one expected OpenGL-context
  skip.

## Struggles and rejected approaches

The first diagnosis was that opening the effective pitch caused the sparse
result. A side-by-side render disproved that as the primary cause: exposure-only
Auto still looked nearly identical to the pitch-changing output. Keeping the
pitch is still required because it preserves the operator's saved geometry,
but the image curve needed the substantive correction.

The prior neutral-exposure Edge-flow recipe was selected on a smaller,
three-layer render. It did not hold the portrait's midtone density with the
current five-layer screen and larger artwork scale.

## Risks and follow-up

The new curve is a software-selected starting point, not a physical print
optimum. Pen spread, ink opacity, and paper still require a four-pass sheet.
The mouth remains a separate compact-edge problem noted in
`WSW-20261123-003`.

## Files

- `software/converter_core/cmyk.py`: non-destructive Edge-flow pitch behavior
  and denser Auto curve.
- `software/generator_tabs/cmyk_tab.py`: Auto uses the tab resolution.
- `software/tests/test_cmyk_tab.py`: density and preserved-pitch regressions.
- `software/README.md`: current Auto behavior and portrait recipe.
- `docs/proposals/flow-field-cmyk.md`: current controls and change link.
- `docs/project/ENGINEERING_LOG.md`: verification and diagnosis record.
