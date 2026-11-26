---
id: WSW-20261126-007
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/settings.py
  - software/generator_tabs/cmyk_tab.py
  - software/qt_svg_to_gcode.pyw
  - software/tests/test_generator_tabs.py
  - software/README.md
  - software/generator_tabs/README.md
  - docs/project/ROADMAP.md
tags:
  - cmyk
  - artwork-scale
  - bed-fit
  - auto-center
  - placement
  - generator-tabs
  - regression
related:
  - WSW-20261126-006
  - WSW-20261007-017
  - WSW-20261020-001
---

# Keep CMYK artwork scale effective and centered

## Summary

CMYK **Artwork scale** now zooms the processed image inside a stable, centered
page frame instead of being cancelled by global bed fit. New artworks without
a saved layout start centered on the bed, while dragging and the placement
fields still provide later adjustments.

## Reason

Bed fit previously measured the already-scaled CMYK content bounds. Scaling
the artwork and then fitting those larger bounds mathematically restored the
same final footprint, so changing Artwork scale appeared to do nothing.

The fit also changed the global scale after the CMYK page-centre anchor had
been calculated. The scaled contours and their frame anchor therefore used
different coordinates, leaving the artwork off-center.

## Implementation

- Added an optional internal `fit_frame_mm` setting. Bed fit sizes this stable
  unscaled page frame when present, rather than remeasuring content bounds.
- CMYK sets its page rectangle as the fit frame and its page centre as the
  shared frame anchor. `fitted_settings()` now scales the frame anchor by the
  same ratio as the final bed-fit scale.
- Preview and Save use the frame fit without an unnecessary first content
  outline pass.
- The explicit fit buttons also use the frame for generator pages.
- Importing an artwork with no valid layout sidecar resets placement to
  `(0, 0)`. A saved sidecar still restores deliberate later placement changes.

## Verification

- Focused regressions confirm CMYK bed fit has the same page scale at 100 %
  and 280 % local Artwork scale, the frame center remains the true page center,
  fitted CMYK layer spans grow with local Artwork scale, and a new artwork
  without a sidecar clears a prior offset.
- Prior generator-fit and placement-reimport regressions remain in the
  focused run.
- The complete generator, CMYK, and placement modules pass `154` tests with
  one expected OpenGL-context skip. Complete converter discovery passes `628`
  tests with one expected OpenGL-context skip, and Python compilation passes.

## Struggles and rejected approaches

Disabling global bed fit was rejected because it would restore the clipping
problem that prompted the fit handoff fix. Letting local scale alter the fit
bounds was rejected because that recreates the cancellation and prevents a
stable print frame.

## Risks and follow-up

Artwork scale above the page-filling size is an intentional zoom/crop control;
content beyond the page or drawable circle can still be clipped. Reducing
Artwork scale restores more margin. The page fit remains bounded by the current
`180 mm` safe reach until the separate 14.5-inch geometry is physically
verified.

## Files

- `software/converter_core/settings.py`: internal stable fit-frame field and
  validation.
- `software/generator_tabs/cmyk_tab.py`: page frame, page center, and scale
  tooltip.
- `software/qt_svg_to_gcode.pyw`: frame-based fitting, synchronized center,
  explicit fit handling, and centered imports.
- `software/tests/test_generator_tabs.py`: scale, center, and import regressions.
- `software/README.md`: current zoom/crop and placement behavior.
- `software/generator_tabs/README.md`: fit-frame contract for generator tabs.
- `docs/project/ROADMAP.md`: restored CMYK scale and centering status.
