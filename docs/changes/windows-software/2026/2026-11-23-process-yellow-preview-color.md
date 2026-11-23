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
  - process-yellow
  - preview
  - ink-simulation
related:
  - WSW-20261123-011
  - WSW-20261007-007
---

# Use pure process yellow in the CMYK preview

## Summary

The operator uses Tombow Process Yellow, Process Blue, Magenta, and Black
markers. The generic process-yellow ink is now `#ffff00` instead of
`#f0c400`, so uncalibrated CMYK multiply previews remove blue as process
yellow should without also darkening red and green into a brown cast.

## Reason

The previous yellow had `R=240` and `G=196`. In the multiply simulation that
made yellow darken red and green substantially, so warm skin, wood, and
background highlights looked brown before any physical ink calibration was
applied. Tombow Process Yellow should be much closer to `#ffff00`.

## Implementation

- `CHANNEL_COLORS["y"]` is now `#ffff00`.
- The same constant drives per-ink SVG stroke colour, the OpenGL CMYK preview,
  and the generic ink model used by Auto colour analysis.
- A regression pins the process-yellow value so it cannot silently regress to
  a warm display approximation.
- A measured ink profile still replaces these generic process colours in the
  multiply preview.

## Verification

- The CMYK tab suite passes `134` tests.
- Complete converter discovery passes `657` tests with one expected
  OpenGL-context skip.
- A software render of the active portrait confirms the yellow reads as a
  lemon process tone rather than brown/orange.
- Physical pen colour remains dependent on the measured ink profile.

## Struggles and rejected approaches

Keeping the warm approximation was rejected: it changes the apparent ink
mixture even when the CMYK separation is correct. Using a measured profile is
preferred when one exists, but the generic fallback must still behave like
process yellow rather than a brown display colour.

## Risks and follow-up

`#ffff00` is an ideal process-yellow display model, not a claim about the
measured yellow pen. Print and scan the CMYK calibration sheet to determine
the actual pen transmittance for production colour matching.

## Files

- `software/converter_core/cmyk.py`: pure process-yellow definition.
- `software/tests/test_cmyk_tab.py`: colour regression.
- `software/README.md`: current preview behaviour.
