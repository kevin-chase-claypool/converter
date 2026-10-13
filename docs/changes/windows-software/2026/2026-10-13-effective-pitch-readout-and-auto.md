---
id: WSW-20261013-007
date: 2026-10-13
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - pitch
  - pen-width
  - controls
related:
  - WSW-20261013-006
---

# Effective pitch readout, and Auto stops overwriting Dot pitch

## Summary

Two CMYK Screen-group changes:

1. The Dot pitch row now shows the **on-paper pitch live** - "= 1.40 mm on
   paper (touching)" - recomputed from Dot pitch x Artwork scale and annotated
   against the pen width (touching / slight gap / separated rows / wide gaps).
2. **Auto (photo) no longer sets Dot pitch.** The operator's spacing choice
   stands; the status line reports it plus what Match pen would suggest.

## Reason

Operator report (2026-10-13): "the pitch that gets recommended doesnt seem
right based on whichever pen width i choose". At the 280 % default artwork
scale, Match pen solves `field x 2.8 = pen`, so a 1.4 mm pen produced a 0.50
field - arithmetically right, visually baffling, and Auto silently repeated
the same overwrite after any manual spacing choice. The readout makes the
field-vs-paper relationship visible; Auto's restraint keeps a chosen gap.

## Implementation

- `cmyk_tab.py`: `effective_pitch_label` in the Dot pitch row; private
  `_update_effective_pitch` wired to pitch, artwork scale and pen-width
  changes; Auto's `pitch.setValue(self.pen_pitch_mm())` removed and its status
  message reworded.
- `test_cmyk_tab.py`: `test_auto_button_applies_photo_settings` now asserts
  the pitch is unchanged and the suggestion text is present.

## Verification

- `py_compile` clean; 88 tests pass (`test_cmyk_tab`, `test_generator_tabs`).
- Bench check: the readout should track Dot pitch x scale as either field is
  changed, and pressing Auto should leave the field where it was.

## Struggles and rejected approaches

Considered colour-coding the label when rows would overlap the pen;
deferred - the relation word already carries that information without another
visual language.

## Risks and follow-up

- The label is advisory; nothing blocks a pitch below the pen width (some
  tones genuinely want overlap).

## Files

- `software/generator_tabs/cmyk_tab.py`: readout, Auto change.
- `software/tests/test_cmyk_tab.py`: updated Auto expectation.
- `docs/project/ENGINEERING_LOG.md`: session entry.
