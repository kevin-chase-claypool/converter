---
id: WSW-20261028-001
date: 2026-10-28
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
  - sharpening
  - unsharp-mask
  - image-processing
  - preview
  - manifest
related:
  - WSW-20261023-001
---

# Add luminance sharpening to CMYK photo preparation

## Summary

The CMYK tab now exposes an unsharp mask for photo detail. It is enabled by
default at 70 % with a 1.5 mm on-paper radius, and both amount and radius are
editable. Preview, per-ink layer generation, and saved-set provenance all use
the same sharpening recipe.

## Reason

Soft portrait features were disappearing into the CMYK screens. The owner's
photo comparison showed that increased mark density and stronger tone curves
alone produced heavier texture while leaving facial structure difficult to
read. An earlier partial implementation added a luminance unsharp mask in the
core module but never connected it to the tab, cache invalidation, tests, or
saved-set manifest.

## Implementation

`prepare_image_tones()` applies the mask after auto-level stretching and before
the saturation, contrast, brightness, and separation curves. It derives the
detail layer from luminance, adds that common detail to all three RGB
channels, and clips the result. This restores edge structure without selecting
one CMYK channel for sharpening and creating colour fringes.

The radius is entered in final on-paper millimetres and converted through the
fitted image's millimetres-per-pixel scale. Resolution therefore changes the
sampling cost but not the physical feature size emphasized by the mask. The
CMYK tab also divides the requested radius by **Artwork scale** before image
preparation, because the finished layers are scaled after screening. This
keeps the entered radius on-paper even when the shared CMYK frame is enlarged.
The tab disables the amount and radius controls while **Sharpen** is off,
includes all three values in its layer-cache key, and records them in the
version-3 `<name>-set.json`. The calibration sheet remains unprocessed so its
tone ladder stays geometrically reproducible.

## Verification

- `python -m unittest discover -s software\tests -p "test_cmyk_tab.py" -v`:
  all 92 tests pass.
- `python -m unittest discover -s software\tests -p "test_*.py" -v`: all
  `553` converter tests pass with the expected OpenGL-context skip.
- The new soft-edge regression confirms that sharpening increases the
  luminance edge gradient while keeping the image mean within 0.01.
- A visual comparison of the owner's portrait at 0 %, 70 %, and 140 % showed
  facial edges becoming readable at 70 %; 140 % introduced visible halos, so
  70 % is the shipped default.
- The saved-set regression verifies manifest version 3 and the exact
  sharpening recipe.

## Struggles and rejected approaches

The original backend patch used a hidden default of zero, so none of the
preview or output code reached it. Sharpening individual CMYK channels was
rejected because it can introduce coloured edge fringes. Raising mark density
and contrast alone made the portrait busier without recovering its fine
features. The unfinished implementation was preserved through several
unrelated milestones and completed here rather than silently changing its
owner-tuned defaults.

## Risks and follow-up

Sharpening is an artistic image transform, not a calibrated ink correction.
The default improves the representative portrait but can ring on an
already-sharp source; lowering the amount or disabling the mask is the first
adjustment. Existing CMYK recipes without a `sharpening` object remain valid
version-2 manifests. A physical print of the same portrait has not yet been
compared against the unsharpened files.

## Files

- `software/converter_core/cmyk.py`: luminance-only unsharp-mask helper and
  image-pipeline integration.
- `software/generator_tabs/cmyk_tab.py`: controls, cache invalidation, layer
  handoff, and version-3 provenance.
- `software/tests/test_cmyk_tab.py`: core, UI-wiring, cache, and manifest
  regressions.
- `software/README.md`: current CMYK controls, defaults, and manifest schema.
- `docs/project/ENGINEERING_LOG.md`: implementation and verification record.
