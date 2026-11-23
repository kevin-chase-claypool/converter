---
id: WSW-20261123-009
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
  - toggle
  - user-interface
related:
  - WSW-20261123-006
  - WSW-20261123-008
  - docs/proposals/flow-field-cmyk.md
---

# Make Fine detail a reversible toggle

## Summary

**Fine detail** now toggles. The first click saves the current Edge-flow
layout and applies the pen-aware preset; the second click restores that saved
layout and clears the checkmark.

## Reason

The first state-indicator implementation made the checkmark truthful but kept
reapplying Fine detail whenever the active button was clicked. The owner
reasonably expected a checked button to turn off, but repeated clicks left it
checked every time.

## Implementation

- Activation snapshots screen style, calibration state, pitch, smoothing,
  layer count, Path tolerance, Black-keyline state, and sharpening controls
  before applying.
- A click while checked restores that snapshot. A click while unchecked saves
  the current controls and applies the preset.
- The snapshot is saved in the artwork recipe with
  `fine_detail_previous` and restored with the same image.
- Manual edits still clear the state indicator. The next activation records
  the newly edited layout as the new restore point.
- Older active recipes without a stored snapshot fall back to Edge-flow,
  unchanged pitch, smoothing `2.5 mm`, three layers, `0.15 mm` tolerance, and
  keylines off when toggled off.
- Applying Fine detail exits calibration-sheet mode before changing the
  artwork screen.

## Verification

- A regression applies Fine detail and verifies a second click restores the
  exact prior pitch, smoothing, layers, tolerance, keyline choice, style, and
  calibration state.
- A recipe round-trip regression proves the prior-layout snapshot survives
  sidecar save/restore and still toggles off afterward.
- Existing active/inactive indicator regressions continue to verify automatic
  clearing after manual edits.
- All `124` CMYK tab tests pass. Complete converter discovery passes `644`
  tests with one expected OpenGL-context skip.

## Struggles and rejected approaches

Making the indicator clear without changing controls would create a false
"off" state where the image still used Fine detail geometry. Restoring a
fallback alone would discard the operator's actual previous layout whenever a
snapshot was available.

## Risks and follow-up

The toggle confirms controls, not preview freshness. Press **Preview** after
either state change. Recipes saved before `WSW-20261123-009` cannot contain a
true previous layout and therefore use the documented fallback when toggled
off.

## Files

- `software/generator_tabs/cmyk_tab.py`: reversible toggle, snapshot restore,
  and recipe persistence.
- `software/tests/test_cmyk_tab.py`: toggle-off and snapshot round-trip
  regressions.
- `software/README.md`: current toggle behavior and legacy fallback.
- `docs/proposals/flow-field-cmyk.md`: current reversible preset behavior.
- `docs/project/ENGINEERING_LOG.md`: owner report and verification.
