---
id: WSW-20261123-008
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - edge-flow
  - fine-detail
  - user-interface
related:
  - WSW-20261123-006
  - WSW-20261123-007
  - docs/proposals/flow-field-cmyk.md
---

# Show whether the Fine detail preset is active

## Summary

The CMYK **Fine detail** button now displays its current state. It is checked
and reads **Fine detail ✓** only while the Edge-flow controls still match the
pen-aware preset. Editing any preset-related control clears the indicator
immediately.

## Reason

Fine detail previously looked like a momentary action button. After clicking
it, there was no visible confirmation that the preset was active, and a later
manual edit could leave the screen in a partially modified state without any
indication.

## Implementation

- The button is checkable and uses both the checked state and the `✓` suffix.
- Active state requires Edge-flow, Black keylines, the calculated pitch,
  smoothing, layer count, and a Path tolerance at or below the preset target.
- Pen width, Artwork scale, screen style, calibration mode, pitch, smoothing,
  layers, tolerance, and keyline changes all refresh the indicator.
- Clicking Fine detail while active simply reapplies the current pen-aware
  targets. It is not a reversible on/off mode because the preset does not
  retain a separate copy of the previous operator layout.
- The tooltip explicitly states whether the preset is active or inactive.

## Verification

- A focused regression verifies the checked button and active tooltip after
  applying the preset.
- A second regression changes Flow smoothing and then Black keylines, proving
  that the indicator clears for each and can be restored by clicking again.
- All `121` CMYK tab tests pass. Complete converter discovery passes `641`
  tests with one expected OpenGL-context skip.

## Struggles and rejected approaches

Making the button behave as a true toggle with an "off" state would require
storing and restoring the entire previous screen recipe. It would also make
"off" ambiguous after the operator edits only one control. Deriving state from
the actual controls is more truthful.

## Risks and follow-up

The indicator confirms settings, not that the current Preview was rebuilt
after the click. The status text still instructs the operator to press
Preview.

## Files

- `software/generator_tabs/cmyk_tab.py`: checkable indicator and live state
  calculation.
- `software/tests/test_cmyk_tab.py`: active, cleared, and reapplied-state
  regressions.
- `software/README.md`: operator-facing indicator behavior.
- `docs/project/ENGINEERING_LOG.md`: implementation and verification record.
