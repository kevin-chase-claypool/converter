---
id: WSW-20261008-005
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
  - defaults
  - gamma
  - tone
related:
  - WSW-20261008-004
  - WSW-20261008-003
---

# Set the CMYK defaults to the owner's gamma-led tuning

## Summary

The CMYK tab now ships the values the owner tuned to fix the dark,
muddy night-photo plot: **contrast 285 %** (inside the new 300 % soft-curve
range), **brightness 170 %**, **ink gamma 1.40**, **black (GCR) 95 %**,
weights **100/100/100/100 %**. Saturation 115 %, rectilinear fill at
0.10 mm pitch, artwork scale 280 %, resolution 10000 px, auto levels on,
hatch levels 8, and 40000 marks/ink are unchanged.

Ink gamma was the biggest lever: values above 1.0 raise each channel's tone
to a power (`tone ** gamma`), so 1.4 lays roughly a third less ink in the
mid tones - exactly what counters the four-ink overprint's natural
darkening. Brightness 170 lifts the image's shadows, and contrast 285
restores punch through the soft S-curve.

## Reason

Owner: "these changes improved things quite a bit especially gamma," with
the settings panel showing the values above and a clearly recognizable
portrait in the ink simulation.

## Implementation

- `software/generator_tabs/cmyk_tab.py`: contrast 200 -> 285, brightness
  130 -> 170, ink gamma 1.0 -> 1.40, GCR 65 -> 95, K weight 105 -> 100.
- `software/README.md`: shipped-defaults sentence and recommended row.

## Verification

- `python -m unittest discover -s software\tests -p "test_*.py"` passes 390
  tests (1 skipped: the pre-existing headless shader compile); the
  shipped-defaults test now asserts contrast 285, brightness 170, gamma
  1.40, GCR 95, and K weight 100.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Encoding the lift in brightness alone was rejected by the owner's own
  tuning: gamma changes ink coverage itself, so it lightens the print
  without washing out the image's structure.

## Risks and follow-up

- Gamma 1.40 is tuned for a dark scene; a well-exposed photo may want
  1.0-1.2. The measured calibration profile remains the final colour step.

## Files

- `software/generator_tabs/cmyk_tab.py`: the tuned defaults.
- `software/tests/test_cmyk_tab.py`: shipped-defaults assertions.
- `software/README.md`: current-state defaults.
