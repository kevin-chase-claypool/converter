---
id: WSW-20261123-012
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - color-management
  - tombow
  - process-blue
  - process-magenta
  - process-yellow
  - preview
  - ink-simulation
related:
  - WSW-20261123-011
  - WSW-20261007-007
---

# Use the Tombow process palette in the CMYK preview

## Summary

The operator uses Tombow Process Yellow, Process Blue, Magenta, and Black
markers. All four generic fallback colours now match that process-marker set
instead of mixing a corrected yellow with older unrelated approximations.

## Reason

The previous yellow had `R=240` and `G=196`. In the multiply simulation that
made yellow darken red and green substantially, so warm skin, wood, and
background highlights looked brown before any physical ink calibration was
applied. Tombow Process Yellow should be much closer to `#ffff00`. The other
channels were also generic approximations rather than one coherent marker set.

## Implementation

- `TOMBOW_PROCESS_COLORS` now defines blue `#00aeef`, magenta `#ec008c`,
  process yellow `#ffff00`, and black `#231f20`; `CHANNEL_COLORS` uses that
  palette.
- The same constant drives per-ink SVG stroke colour, the OpenGL CMYK preview,
  and the generic ink model used by Auto colour analysis.
- A regression pins all four values so they cannot silently regress to mixed
  display approximations.
- A measured ink profile still replaces these generic process colours in the
  multiply preview.

## Verification

- The CMYK tab suite passes `134` tests.
- Complete converter discovery passes `657` tests with one expected
  OpenGL-context skip.
- A software render of the active portrait confirms yellow reads as a lemon
  process tone rather than brown/orange.
- Physical pen colour remains dependent on the measured ink profile.

## Struggles and rejected approaches

Keeping the warm approximation was rejected: it changes the apparent ink
mixture even when the CMYK separation is correct. Using a measured profile is
preferred when one exists, but the generic fallback must still behave like
process yellow rather than a brown display colour.

## Risks and follow-up

These are display approximations, not claims about measured Tombow ink
transmittance. Print and scan the CMYK calibration sheet to determine the
actual pen values for production colour matching.

## Files

- `software/converter_core/cmyk.py`: explicit Tombow process palette.
- `software/tests/test_cmyk_tab.py`: colour regression.
- `software/README.md`: current preview behaviour.
