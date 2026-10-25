---
id: WSW-20261024-013
date: 2026-10-24
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
tags:
  - cmyk
  - wave-screen
  - zero-point
  - frequency
  - clearance
related:
  - WSW-20261024-011
  - WSW-20261024-010
  - 2026-10-24-wave-row-zero-points-and-clearance
---

# Add zero-anchored CMYK wave depth

## Summary

Added **Wave screen - zero-anchored depth**. Every row starts at the same
zero-displacement baseline, while scene tone controls both wave amplitude and
winding rate. A sampled-band and true segment-distance clearance search reduces
only unsafe row-specific variation instead of forcing every row into one
completely uniform waveform.

## Reason

The open-source SquiggleDraw family resets phase to zero at each row baseline
and lets image brightness drive amplitude and phase increment. The project's
earlier modes either removed that depth by sharing one waveform, or permitted
unbounded row-to-row movement.

The primary-source review is in
`docs/research/2026-10-24-wave-row-zero-points-and-clearance.md`.

## Implementation

- Added stored style value `waves_zero`, displayed as **Wave screen -
  zero-anchored depth**.
- Every row begins at phase zero on its exact baseline; there is no
  row-to-row phase offset.
- Tone controls per-row amplitude and increases phase rate by up to `75 %`.
- A seven-row smoothing pass retains broad luminance depth without
  row-frequency noise.
- The zero-anchored amplitude envelope cannot exceed half the pitch, so only
  consecutive row bands can approach one another.
- Visible row centerlines must remain at least `75 %` of pitch apart at every
  common sample column. The shortest finite segment-to-segment distance is
  also checked, rather than assuming matching sample columns capture the
  closest approach.
- Each emitted centerline pair must keep the configured pen width plus
  `0.25 mm` of nominal paper gap. The CMYK tab divides both limits by Artwork
  scale so they remain paper-space checks rather than shrinking source-space
  estimates.
- When the full-depth candidate fails either check, a seven-step search fades
  row-specific amplitude/frequency variation toward the shared waveform. If
  that common waveform is still too steep, a second search reduces its common
  amplitude; an impossible pitch/pen combination raises a planning error.
- The strict **Wave screen - equidistant rows** mode remains available as the
  fully parallel fallback. The original **Wave screen** remains unchanged for
  comparison.
- Wave sample density accounts for the higher maximum phase rate so the
  configured Path tolerance still bounds chord faceting.
- The black-pen coupon now compares zero-anchored depth against equidistant
  rows on the same gradient, rather than comparing the superseded original
  mode.

## Verification

- A tone/reference regression fails with constant frequency and now confirms
  that dark tone produces at least 1.3x the zero crossings of light tone.
- A two-dimensional tone fixture confirms every sampled visible row centerline
  remains at least `75 %` of the configured pitch apart.
- A regression with three-millimetre column gaps and steep parallel segments
  confirms the final check catches their `1.026 mm` geometric distance even
  though every matching column passes the wider band floor.
- A uniform-tone regression confirms zero-anchored wave chords stay below the
  `0.05 mm` Path-tolerance target despite the faster dark-tone phase rate.
- Real Ben1 screening at `280 %` scale measured minimum same-column spacing of
  `2.543`, `2.537`, `2.764`, and `2.564 mm` for C/M/Y/K respectively, against
  the `2.520 mm` band floor. The stricter shortest-segment result was
  `2.102`, `2.224`, `1.925`, and `2.103 mm`, all above the required
  `1.050 mm` centerline envelope for the `0.8 mm` pen plus `0.25 mm` gap.
- The regenerated black-pen coupon has 20 wave runs and 886 source drawing
  points; `check_gcode_motion.py --strict` passes with the bed parked.
- A complete 49,719-line yellow validation program with 137,381 source drawing
  points and 976 contours passes the strict motion guard: largest drawing step
  `4.87 deg`, largest A rate `268 motor deg/s`, no pen-up rotation, and worst
  bounded path bow `0.080 mm` at the `30 mm` centre-hold boundary. Two moves
  exceed the configured `0.05 mm` tolerance because the bounded subdivision
  cap binds; the checker classifies the program as within its strict cap.
- All `81` CMYK-tab tests and `3` coupon tests pass (`84` combined). Full
  converter discovery passes `519` tests with one expected OpenGL-context skip.

## Struggles and rejected approaches

- The fully shared waveform guarantees spacing but loses the upstream
  low/high-frequency depth.
- Independent source-style phase accumulation without a safety pass can still
  converge.
- Clamping only the vertical amplitude does not address rows whose phase rates
  diverge.

## Risks and follow-up

- The `0.25 mm` segment gap is nominal source geometry. Bed compensation,
  registration, pen-tip shape, and machine following error can consume it;
  the wider `75 %` same-column band provides additional guard space.
- Regenerate and select **Wave screen - zero-anchored depth** explicitly.
  Physical yellow/magenta validation is still required.

## Files

- `software/converter_core/cmyk.py`: phase accumulation and clearance search.
- `software/generator_tabs/cmyk_tab.py`: new style option and guidance.
- `software/tests/test_cmyk_tab.py`: frequency, clearance, and chord tests.
- `tools/make_cmyk_wave_coupon.py` and
  `software/tests/test_cmyk_wave_coupon.py`: zero-anchored coupon.
- `samples/gcode/cmyk-wave-coupon.gcode`: regenerated comparison program.
- `software/README.md`: current Wave-screen behavior.
- `docs/research/2026-10-24-wave-row-zero-points-and-clearance.md`: upstream
  source review and rationale.
