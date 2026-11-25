---
id: WSW-20261125-008
date: 2026-11-25
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/_tab_common.py
  - software/generator_tabs/plotterfun_extended_tab.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_cmyk_photo_tab.py
  - software/tests/test_generator_tabs.py
  - software/README.md
tags:
  - cmyk
  - color-match
  - gcr
  - coherent-color-flow
  - guided-ui
  - fourteen-inch-bounds
  - x-theta
  - y-theta
related:
  - WSW-20261125-007
  - WSW-20261125-005
  - WSW-20261125-004
---

# Make native coherent CMYK the guided color workflow

## Summary

The converter's **CMYK Photo** tool now opens in a guided, image-led screen
with one primary action: **Create 4 G-code files**. It uses the native
coherent shared-geometry color renderer instead of Plotterfun Extended's
independent per-channel CMYK output. The full CMYK tuner remains one click
away under **Advanced settings**.

The guided page is 250 mm square, which places every corner inside the
355.6 mm (14 in) print circle. Public output is written in numbered physical
print order: `01-yellow`, `02-magenta`, `03-cyan`, `04-black`.

## Reason

The owner found the previous Plotterfun-based result visually incorrect: hue,
brightness, and contrast did not follow the source closely enough. This was an
algorithm mismatch. Plotterfun Extended runs its selected algorithm separately
for each CMYK channel, so the channels do not share coherent local color
geometry. The Reddit-style structure-tensor workflow instead belongs to the
native coherent CMYK renderer already implemented in `cmyk_tab.py` and
`structure_tensor.py`.

The previous interface also remained too empty and control-heavy. The owner
asked for a genuinely simple screen without removing color quality or the
machine's reach guards.

## Implementation

- `CmykPhotoTab` is now the production result of `cmyk_tab.create_tab()` and
  appears as **CMYK Photo**.
- Guided defaults select coherent color flow, three tone layers, 2.5 mm
  structure smoothing, pen-aware pitch, black keylines, and automatic image
  analysis. GCR remains active and contributes the K tone.
- The active converter ink profile is used when loaded; otherwise the native
  nominal process-ink model is used.
- The guided page is 250 x 250 mm. Its corner radius is `176.78 mm`, inside the
  `177.8 mm` radius of a 14-inch-diameter print area.
- **Create 4 G-code files** chooses the image and output folder when needed,
  applies the recommended photo recipe, builds the shared color preview, and
  then plans the exact Y/M/C/K programs with `analyze_program`.
- Public files use `*-01-yellow.gcode`, `*-02-magenta.gcode`,
  `*-03-cyan.gcode`, and `*-04-black.gcode`, plus `*-set.json`.
- The guided screen shows the source image in both the compact card and the
  large preview canvas. Generic Preview, playback, fit, and ink-profile chrome
  is hidden until **Advanced settings** is opened.
- Plotterfun Extended remains available as an explicit experimental
  independent-channel comparison; its description directs color work to
  **CMYK Photo**.

## Verification

- Guided UI tests verify source-image presentation, hidden advanced controls,
  advanced-mode restoration, 250 mm page bounds, and Y/M/C/K order.
- Focused CMYK, guided-workflow, and generator-shell modules pass `121` tests
  with one expected OpenGL-context skip.
- Complete converter discovery passes `719` tests in `151.103 s` with the one
  expected OpenGL-context skip.
- A live native run on the supplied colorful photo generated four nonempty
  programs with GCR at `80 %`. The largest actual XY radius was `174.817 mm`,
  below the 14-inch radius of `177.8 mm`.
- The same run passed strict motion preflight on every ink. Drawing counts were
  yellow `266,988`, magenta `136,910`, cyan `130,937`, and black `106,191`;
  all used Xθ/Yθ strategies and stayed below the A-rate and bed-step limits.
- The live preview visibly retained the source's green background, blue/gray
  clothing, skin hues, and black structure inside the displayed reach circle.

## Struggles and rejected approaches

Continuing to tune Plotterfun Extended's classic CMYK split was rejected
because its four independently traced channel networks cannot preserve the
shared local color planes described by the reference workflow.

Leaving the preview area blank until generation was rejected. The guided view
now displays the selected source image immediately and replaces it with the
planned CMYK preview when generation finishes.

Exposing a small subset of CMYK controls in guided mode was rejected as a
half-solution. The guided screen has one action; every specialized control is
preserved together under **Advanced settings**.

## Risks and follow-up

- The full-quality photo produces large G-code sets and took several minutes to
  preview and plan in the verification image. Progress and cancellation remain
  visible during that work.
- Hue and density still depend on the loaded ink profile, actual marker colors,
  paper, and registration. No physical four-pass comparison has been recorded
  for this image.
- The 250 mm page is a square inscribed around the same frame center. Changing
  physical stock, the A datum, or the registered bed center still requires the
  existing commissioning checks.

## Files

- `software/generator_tabs/cmyk_tab.py`: guided native CMYK workflow, image-led
  UI, 14-inch-safe page, Y/M/C/K output order, and advanced-mode toggle.
- `software/generator_tabs/_tab_common.py`: retains the guidance label so the
  guided mode can hide it cleanly.
- `software/generator_tabs/plotterfun_extended_tab.py`: labels Plotterfun as
  an experimental comparison.
- `software/qt_svg_to_gcode.pyw`: guided width, preview transport visibility,
  and settings-pane sizing.
- `software/tests/test_cmyk_photo_tab.py`: guided layout, defaults, workflow,
  bounds, and output-order regressions.
- `software/tests/test_generator_tabs.py`: production title, preview chrome,
  advanced toggle, and integration assertions.
- `software/README.md`: current guided workflow and tool guidance.
