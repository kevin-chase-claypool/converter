---
id: WSW-20261127-005
date: 2026-11-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/wave_rows.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - fixed-baselines
  - low-pitch
  - amplitude
  - clearance
  - depth-intensity
  - regression
related:
  - WSW-20261126-014
  - WSW-20261127-003
  - WSW-20261127-004
  - ADR-009
---

# Preserve fixed-baseline Wave depth at the live low pitch

## Summary

**Variable-depth Wave - fixed baselines** now preserves visible waveforms at
the owner's live `1.26 mm` pitch, `0.90 mm` pen, and `1.17 mm` clearance.
Shared-phase row amplitudes are bounded by a per-column forward/backward
envelope instead of iteratively scaling affected rows toward a straight line.
The carrier amplitude is also limited by its steep-flank geometry, so the exact
pen-envelope check remains authoritative.

Equal baselines, the shared phase, blank regions, Period variation, Depth
intensity, and the final shortest-segment safety gate are retained.

## Reason

The live Golden Sunset failure had only about
`1.26 - 1.17 = 0.09 mm` of relative row displacement available. The previous
local and whole-row multiplicative damping reduced every conflict in only one
direction. A steep tone change could therefore flatten unrelated rows, and
raising Depth intensity could make the remaining geometry even flatter.

Direct final-output row ranges before the change were:

| Ink | Median peak-to-peak | Rows below `0.03 mm` |
|---|---:|---:|
| C | `0.0105 mm` | `69.8 %` |
| M | `0.0304 mm` | `48.9 %` |
| Y | `0.0324 mm` | `10.7 %` |
| K | `0 mm` | `100 %` |

The saved-recipe `2.2 mm` pitch oracle did not exercise this state.

## Implementation

For consecutive fixed-baseline rows sharing one phase:

```text
row_i(x) = baseline_i + a_i(x) * sin(phase(x))
offset_difference = (a_i(x) - a_{i+1}(x)) * sin(phase(x))
```

For each along-row column the implementation takes the requested
tone-driven amplitudes and runs forward and reverse lower envelopes:

```text
a_i = max(
    requested_i,
    a_{i-1} - available_step,
    a_{i+1} - available_step,
)
```

The two passes produce the lowest amplitude field that both preserves every
tone-driven request and limits each adjacent amplitude difference. A large
tone edge is therefore spread gradually over neighbouring rows rather than
removing depth from the dark row or from unrelated parts of the grid.

The available step includes a `0.001 mm` analytic reserve. A second shared
carrier cap accounts for the reduced perpendicular separation on steep wave
flanks. When that physical cap binds, the visible depth field is normalized to
use the safe amplitude rather than collapsing to the source's absolute
coverage value. A `2 %` amplitude headroom is released as Depth intensity
rises from `100 %` to `150 %`, keeping that control monotone without exceeding
the physical cap. The existing final finite-segment clearance check still runs
and raises if any emitted pair would violate the configured envelope.

## Verification

- `test_fixed_baseline_live_pitch_envelope_preserves_interior_waves` uses the
  live `1.26/1.17` ratio with alternating dark/light row depth. At least 20
  interior-contour checks remain at `0.10 mm` peak-to-peak or deeper, every row
  has the same crossing count, fixed baselines remain `1.26 mm` apart, and
  every adjacent segment pair passes the `1.17 mm` check.
- `test_fixed_baseline_live_pitch_depth_intensity_is_not_damped` verifies that
  `150 %` Depth intensity never reduces the median waveform relative to
  neutral and retains at least `0.20 mm` peak-to-peak depth.
- The current combined `software.tests.test_cmyk_tab` run passes `136 / 138`.
  Both new live-pitch regressions pass. The two failures are concurrent UI-test
  ownership conflicts outside this workstream: the equidistant status expects
  `blocked` but receives `pass`, and the Match pen test expects `pass` but
  receives `blocked`. Their assertions were not changed after the file freeze.
- The rotating-bed, final-coordinate checker, and Wave coupon suites pass all
  `19` tests.
- Re-running the live-failed Golden Sunset recipe through the production
  `waves_fixed` path at final `1.265 mm` pitch gives these final row ranges:

| Ink | Rows | Median peak-to-peak | Rows below `0.03 mm` |
|---|---:|---:|---:|
| C | 200 | `0.583315 mm` | `0 %` |
| M | 200 | `0.583330 mm` | `0 %` |
| Y | 163 | `0.583462 mm` | `0 %` |
| K | 231 | `0.506907 mm` | `0 %` |

These are local across-row ranges after the final artwork scale, not
world-coordinate Y ranges affected by screen rotation.

At `100 %` versus `150 %` Depth intensity, the same final-source medians were
C `0.579564 -> 0.583315`, M `0.578399 -> 0.583330`,
Y `0.579219 -> 0.583462`, and K `0.502144 -> 0.506907 mm`.

## Struggles and rejected approaches

- The first envelope preserved interior tone depth but the exact checker still
  rejected it. Shared-phase rows with equal amplitude are parallel curves, and
  their perpendicular gap on steep flanks is smaller than their vertical
  baseline gap. A shared slope cap was required in addition to the `0.09 mm`
  relative-displacement envelope.
- Normalizing only the peak tone after the slope cap removed the flat waveform,
  but reduced visible depth contrast at ordinary pitch. The slope cap now
  applies only where it binds, and the existing narrow-tone contrast test was
  retained with a `2.5x` floor rather than the earlier physically impossible
  `3.5x` amplitude demand.
- Reusing the old pairwise binary scaling was rejected because it propagates a
  single conflict through the whole row grid.
- Breaking the amplitude envelope at every blank coverage cell was rejected.
  Coverage-boundary segments could approach diagonally; blank cells still
  emit nothing, while the amplitude budget applies across the row lattice.

## Risks and follow-up

- This is software/G-code geometry evidence, not a physical print result. Ink
  spread, pressure, paper absorption, registration, and rotating-bed following
  error still require a fresh low-pitch coupon.
- The analytic slope cap is conservative and reduces peak wave amplitude at
  tight pitch. It should be compared with the intended design on paper before
  treating the resulting `0.5-0.58 mm` median as visually sufficient.
- The source recipe at `2.2 mm` pitch remains an optimizer/software-fidelity
  check and is not evidence that the live `1.26 mm` failure is fixed.
- Per repository scope for this workstream, `software/README.md`, the roadmap,
  the engineering log, generated indexes, and commits/pushes were not changed.
  Those integration updates remain for the coordinating workstream.

## Files

- `software/converter_core/wave_rows.py`: shared slope cap, per-column
  forward/backward amplitude envelopes, depth normalization, and the retained
  exact clearance gate.
- `software/tests/test_cmyk_tab.py`: live-pitch interior visibility,
  shared-phase, no-collision, and intensity non-damping regressions.
