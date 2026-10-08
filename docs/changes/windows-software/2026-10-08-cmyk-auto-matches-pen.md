---
id: WSW-20261008-012
date: 2026-10-08
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/README.md
tags:
  - cmyk
  - screening
  - automation
  - pitch
related:
  - WSW-20261008-010
  - WSW-20261008-009
---

# Auto (photo) also matches the pen pitch

## Summary

Pressing **Auto (photo)** now also sets Dot pitch to one pen width at the
current artwork scale - exactly what the **Match pen** button does. Auto
previously reported the effective pitch (`Dot pitch x Artwork scale` versus
pen width) as text advice and left the control alone, so a photo could be
auto-fitted and still screened at a density the pen cannot hold.

## Reason

Owner: "is dot pitch being adjusted during the auto button press?" - it was
not. The advice line could tell the operator the balance was off but did
nothing about it, and the effective pitch only reads correctly when it is
tied to the same artwork scale the Auto result is judged at.

## Implementation

- `software/generator_tabs/cmyk_tab.py`: `pen_pitch_mm()` returns
  `clamp(pen width / artwork scale, 0.1, 8.0)`; `match_pen_pitch()` uses it,
  and `apply_auto_settings` sets Dot pitch to it before reporting. The Auto
  status message states the pitch it chose (one pen width at the current
  scale) instead of the previous effective-pitch advisory.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"`: 398 tests
  pass, 1 skipped (the pre-existing headless shader compile).
- `test_auto_button_applies_photo_settings` presses Auto at 150 % artwork
  scale with the 0.30 mm pen and asserts Dot pitch lands on 0.20 mm and the
  status message names it.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Keeping the trend advisory text alongside the auto-set pitch was rejected:
  after Auto the effective pitch is one pen width by construction, so the
  advisory would always print the same "good balance" sentence.

## Risks and follow-up

- Auto now overwrites a manually chosen Dot pitch. Operators who want a
  deliberately coarser or denser screen should set Dot pitch after Auto, the
  same way Auto already overwrites the tone controls.

## Files

- `software/generator_tabs/cmyk_tab.py`: shared pen-pitch helper; Auto sets
  the pitch.
- `software/tests/test_cmyk_tab.py`: Auto pitch assertion.
- `software/README.md`: Auto description updated.
