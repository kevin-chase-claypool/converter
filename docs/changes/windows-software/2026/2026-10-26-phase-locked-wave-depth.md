---
id: WSW-20261026-001
date: 2026-10-26
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_cmyk_wave_coupon.py
  - tools/make_cmyk_wave_coupon.py
  - samples/gcode/cmyk-wave-coupon.gcode
  - samples/gcode/cmyk-wave-pitch-coupon.gcode
  - samples/gcode/cmyk-wave-letter-test.gcode
tags:
  - cmyk
  - wave-screen
  - depth
  - amplitude
  - phase
  - clearance
  - test-paper
related:
  - WSW-20261025-003
  - WSW-20261024-013
  - 2026-10-24-wave-row-zero-points-and-clearance
---

# Restore wave depth with a shared phase

## Summary

Changed **Wave screen - phase-locked depth** so every row shares one sine
phase while scene tone controls that row's amplitude independently. The exact
segment-to-segment pen-envelope check remains. The extra 75%-of-pitch
same-column gap and independent row phase accumulator are removed.

Added a 16-patch portrait 8.5 x 11 paper test covering every CMYK screen angle
at `2.80`, `3.36`, and `4.20 mm` pitch, plus an equidistant control row.

## Reason

The zero-anchored mode had accumulated phase independently for every row.
Rows with different frequency could approach one another, causing the safety
pass to shift rows and reduce amplitude. The result was visibly shallower than
the original phase-aligned wave screen.

Direct comparison on the Ben1 source image predicted a median visible wave
range of about `2.75 mm` for the original algorithm, `0.95 mm` for the
independent-phase build, and `1.93 mm` after this change. The historical
pre-independent G-code and current G-code showed the same direction of change.

## Implementation

- `waves_zero` remains the stored style value for saved-recipe compatibility.
- The displayed name is now **Wave screen - phase-locked depth**.
- Every row uses the original common carrier:
  `sin(2 * pi * x / (2 * pitch))`.
- Smoothed scene depth still scales each row's amplitude.
- The fixed same-column 75% pitch floor is gone.
- Collision safety is now based on the actual shortest distance between
  adjacent visible segments, including the configured pen width and paper
  edge gap.
- If the exact check fails, a bounded search reduces wave amplitude until it
  passes or the flat-row geometry is proven impossible.
- New set manifests record `wave_phase_mode: shared_zero_anchored` instead of
  obsolete frequency-gain and 75%-band fields.

## Verification

- New regression: uniform full tone retains at least `95 %` of the available
  half-pitch amplitude (`> 3.8 mm` peak-to-peak on a `4 mm` pitch).
- New regression: all rows place their first crest at the same horizontal
  position while their vertical ranges differ by more than `1.8x`.
- Multi-pitch regression: `2.80`, `3.36`, and `4.20 mm` change amplitude while
  preserving the same number of wave crossings.
- Exact-clearance regression: rows may approach inside 75% of pitch when the
  actual `1.05 mm` pen envelope remains clear; steep segments closer than that
  still fail.
- The saved 6.5-inch-style coupon and multi-pitch coupon were regenerated and
  pass strict motion checks.
- Coupon SHA-256 values:
  `cmyk-wave-coupon.gcode` =
  `B63A6226F00BBDDC1A31CD2A895DFBED7EF809285B9B0046FBBB5B80E37F7D19`;
  `cmyk-wave-pitch-coupon.gcode` =
  `17D82A7A934325554EE89C4471B056E78B53E5D47FD9B0C4687C51A77118FE7B`.
- The new 8.5 x 11 test has 22,769 drawing moves, 287 travel moves, one program
  end, no pauses, and no bed rotation. Strict motion preflight passes.
- The letter test SHA-256 is
  `2DDCCEA3CD46E05B098D10971D586639E5B437B4684B13834B9147644E85325F`.
- Full converter discovery passes `546` tests with one expected OpenGL-context
  skip.

## Struggles and rejected approaches

- Independent phase was introduced to reproduce the low/high-frequency
  SquiggleDraw effect, but it consumed the amplitude budget needed for visible
  depth.
- The 75% same-column floor was much stricter than the physical pen envelope;
  at a `3.36 mm` pitch it required `2.52 mm` between centers for a `1.05 mm`
  envelope.
- Shifting rows after independent phase generated extra white space and made
  the result look flatter.
- Retaining independent phase behind the same style would not correct an
  existing saved recipe when loaded.

## Risks and follow-up

- The new physical 8.5 x 11 sheet has not been printed yet.
- The shared carrier intentionally gives up tone-driven winding-rate changes.
  Tone now changes depth through amplitude only.
- A clean paper result requires no row contact, visible amplitude variation,
  and matched crest/trough alignment across the phase-locked rows.
- Restart the Qt converter before regenerating artwork so the new module is
  loaded.

## Files

- `software/converter_core/cmyk.py`: shared phase, per-row amplitude, exact
  clearance search.
- `software/generator_tabs/cmyk_tab.py`: phase-locked label/tooltip and manifest.
- `software/tests/test_cmyk_tab.py`: amplitude, phase, multi-pitch, and clearance
  regressions.
- `software/tests/test_cmyk_wave_coupon.py`: regenerated coupon and 8.5 x 11
  test coverage.
- `tools/make_cmyk_wave_coupon.py`: `--letter` generator and revised tone
  fixture.
- `samples/gcode/cmyk-wave-coupon.gcode`: regenerated all-angle/motion coupon.
- `samples/gcode/cmyk-wave-pitch-coupon.gcode`: regenerated pitch ladder.
- `samples/gcode/cmyk-wave-letter-test.gcode`: portrait 8.5 x 11 verification.
