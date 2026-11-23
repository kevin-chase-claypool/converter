---
id: WSW-20261123-007
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
  - keylines
  - portrait
  - color-balance
related:
  - WSW-20261123-003
  - WSW-20261123-005
  - WSW-20261123-006
  - WSW-20261123-008
  - docs/proposals/flow-field-cmyk.md
---

# Preserve Black portrait keylines and refine Edge-flow Auto color

## Summary

Edge-flow can now keep the strongest coherent image boundaries continuous in
the Black plate while leaving Cyan, Magenta, and Yellow tone-gated. **Fine
detail** enables this automatically. Edge-flow Auto also reduces the
red-orange cast by moderating saturation and GCR while slightly lifting
brightness and ink gamma.

## Reason

The owner compared the portrait render with the source. Hair, eye sockets,
nose plane, ear, wood grain, and collar were recognizable, but the mouth and
teeth merged into a dark knot, small eye highlights disappeared, and the
shirt seams were under-described. The face was also substantially more orange
and dark than the source's pale skin, while the blurred green background
received too much high-contrast black and yellow texture.

The existing path-local tone gate correctly expressed light and dark areas,
but it broke compact high-contrast boundaries into the same short segments as
ordinary facial shading.

## Implementation

- The structure-tensor field now exposes its normalized gradient-strength and
  coherence confidence.
- **Continuous Black keylines** raises Black coverage only where that
  confidence is high. The same edge-tangent streamline direction is retained,
  so the result follows the eye, nostril, lip, tooth, collar, and wood
  boundaries rather than drawing a blanket outline.
- C/M/Y remain tone-gated. The checkbox defaults off for compatibility.
  **Fine detail** turns it on and saves it in the artwork recipe.
- Auto now targets a less saturated portrait balance. For `IMG_0514.JPG` it
  selects brightness 105 %, contrast 220 %, saturation 110 %, GCR 80 %, and
  gamma 0.75 instead of the previous 100/235/120/85/0.70.

## Verification

- A synthetic low-tone vertical edge increases continuous Black ink length by
  more than `1.4x` with keylines while following the same coherent direction.
- The Edge-flow recipe round-trip test covers the new persisted keyline flag.
- The Fine-detail preset regression verifies that the preset enables Black
  keylines.
- A `600 px` software render compares the saved five-layer screen, Fine detail
  without keylines, the revised Auto color, and the final keylined result.
  Continuous Black detail improves the eyes, nostrils, lip line, collar, and
  wood; the revised Auto reduces the orange cast while retaining facial
  density.
- All `120` CMYK tab tests pass. Complete converter discovery passes `640`
  tests with one expected OpenGL-context skip.

## Struggles and rejected approaches

Applying keylines to all four ink plates increased color fringing and made the
face busier. Continuous outlines across every shadow also buried the source
form. Restricting the boost to high-confidence Black paths preserves detail
without changing the broad color screen.

Returning to neutral or very bright Auto exposure restored the source's
luminance but made the screen sparse again. The selected values are a middle
point: enough midtone coverage for the face, with less chroma than the prior
Auto curve.

## Risks and follow-up

The keyline strength and confidence gate are software-selected from this
portrait and a synthetic edge. They have not been tested on a physical
four-pass sheet. Pen spread may thicken the Black boundary differently from
the measured monitor render.

The source background is intentionally out of focus; reducing its texture
would require a separate subject/background mask and is not part of this
change. The measured CMYK ink profile remains required for accurate physical
color matching.

## Files

- `software/converter_core/structure_tensor.py`: edge-confidence field and
  keyline coverage.
- `software/converter_core/cmyk.py`: keyline plumbing and revised Edge-flow
  Auto values.
- `software/generator_tabs/cmyk_tab.py`: Continuous Black keylines control,
  recipe persistence, manifest evidence, and Fine-detail activation.
- `software/tests/test_cmyk_tab.py`: keyline, preset, and round-trip
  regressions.
- `software/README.md`: current controls, recipe, and color behavior.
- `docs/proposals/flow-field-cmyk.md`: current keyline and Auto parameters.
- `docs/project/ENGINEERING_LOG.md`: comparison and verification evidence.
