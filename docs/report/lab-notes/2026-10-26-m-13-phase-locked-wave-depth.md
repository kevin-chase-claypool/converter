# M-13 phase-locked wave-depth comparison and paper test

**Date:** 2026-10-26

## Purpose

Compare the first wave-screen implementation with the independent-phase
zero-anchored revision, then provide a compact physical check on 8.5 x 11
paper.

## Algorithm comparison

The first wave screen used:

- One common phase for every row.
- A wavelength of twice the row pitch.
- Local ink tone to scale that row's amplitude.
- No independent per-row frequency.
- No fixed row-band clearance; physical collision checking was absent.

The superseded zero-anchored revision used:

- One phase accumulator per row.
- Tone-driven changes to both amplitude and phase rate.
- A 75%-of-pitch same-column row floor.
- Row shifting and slope budgets to satisfy that floor.
- A final exact segment-distance check.

The current phase-locked revision uses:

- One common phase for every row.
- The same wavelength relationship as the first implementation.
- Shared scene luminance to scale each row's amplitude.
- No independent frequency or fixed 75% row floor.
- The exact shortest-segment pen-envelope check retained.

## Measured comparison

With the Ben1 image and current 200 mm page settings, comparing visible wave
runs by vertical range produced:

| Version | Median visible range | Mean |
|---|---:|---:|
| Original wave | `2.75 mm` | `2.12 mm` |
| Independent zero-anchored | `0.95 mm` | `0.91 mm` |
| Phase-locked depth | `1.93 mm` | `1.81 mm` |

These values are geometry measurements, not physical ink measurements. The
phase-locked result recovers about twice the visible depth of the immediate
predecessor while retaining the exact pen-envelope guarantee.

## 8.5 x 11 verification program

File:

[`cmyk-wave-letter-test.gcode`](../../../samples/gcode/cmyk-wave-letter-test.gcode)

Generate with:

```powershell
python tools\make_cmyk_wave_coupon.py --letter
```

The portrait sheet contains sixteen `50 x 50 mm` patches in a `200 x 200 mm`
field:

- Columns left to right: C15, M75, Y0, K45 screen angles.
- Row 1: phase-locked depth at `2.80 mm` pitch.
- Row 2: phase-locked depth at `3.36 mm` pitch.
- Row 3: phase-locked depth at `4.20 mm` pitch.
- Row 4: equidistant rows at `3.36 mm` pitch as the fixed-depth control.

The toolhead remains at A0 for the entire program so bed rotation is not a
variable. Use one black 0.8 mm Pigma Micron.

## Procedure

1. Tape portrait 8.5 x 11 paper flat and centered.
2. Run `G65 P113` and verify center registration.
3. Confirm `$123=6000`, `$701=0`, and 100 percent feed override.
4. Run the file once; it has no pauses or manual stage changes.
5. Do not retape or move the sheet during the run.
6. Allow roughly 20-35 minutes and photograph the result straight down.

## Physical acceptance

- Within each phase-locked patch, crests and troughs should occupy the same
  horizontal positions across rows.
- Tone-driven amplitude variation must remain visibly stronger than in the
  earlier dense-ripple result.
- Rows must not touch, cross, or reverse order.
- The three pitch rows should preserve the same wave rhythm while changing
  absolute amplitude with pitch.
- The bottom equidistant row should have uniform row amplitudes and fixed
  repetition.
- All four screen angles must satisfy the same criteria.

## Static evidence

- G-code: about `24,800` lines; one `M2`, no `M0`.
- Motion: `22,769` drawing blocks and `287` travel blocks.
- SHA-256:
  `2DDCCEA3CD46E05B098D10971D586639E5B437B4684B13834B9147644E85325F`.
- Machine extent: about `X -100.12..100.41 mm`,
  `Y -100.67..100.50 mm`.
- Bed rotation: zero.
- Strict motion check: PASS.
- Screen tests: shared phase, full-tone amplitude, amplitude-vs-pitch,
  exact-clearance, and all-angle generation pass.

## Verification status

Implementation software: verified.

Physical visibility/clearance on the 8.5 x 11 sheet: pending.
