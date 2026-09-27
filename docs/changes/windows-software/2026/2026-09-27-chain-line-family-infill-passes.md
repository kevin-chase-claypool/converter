---
id: WSW-20260927-005
date: 2026-09-27
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/gcode.py
tags:
  - converter
  - infill
  - hatch
  - pen-cycle
  - serpentine
  - print-time
related:
  - WSW-20260927-003
---

# Chain line-family infill passes instead of lifting between them

## Summary

`linear`, `crosshatch`, `diagonal`, `diagonal_crosshatch`, and `cubic` infill
can now keep the pen down between consecutive passes, the same way the lattice
patterns already could. A dense fill is drawn as one continuous zigzag instead
of lifting the pen once per row.

## Reason

`line_region_contours` already emits consecutive hatch rows head-to-tail - it
reverses every other row for exactly that reason - but `bridge_motion()` only
allowed the pen to stay down for `concentric`, `triangular`, `diamonds`, and
`hexagonal`. So every line-family pass paid its own `M5` / handshake / `G0` /
`M3` / handshake round trip.

Measured on a 40 x 40 mm filled square at 0.3 mm spacing: 183 passes, 184 pen
cycles, **0** bridges, and a 0.424 mm connector between consecutive passes -
narrower than the 0.3 mm pen tip it refused to draw. The drawn path length was
already optimal for the spacing (5,256 mm against an ideal `area / spacing` of
5,333 mm), so the loss was entirely pen cycles.

## Implementation

`software/converter_core/gcode.py`: the five line-family patterns were added to
`bridge_patterns`. Nothing else changed - the existing guards already decide
whether a connector is worth drawing:

```python
pattern_gap = spacing * (1.35 if pattern == "concentric" else 0.85)
max_gap = max(pattern_gap, pen_diameter * 6.0)
if xy_len <= 1e-9 or xy_len > max_gap:
    return None
```

That makes the change self-limiting. A line-family connector measures
`spacing / cos(angle)`, so at shading spacing it exceeds `max_gap` and is
rejected; at fill spacing it is a fraction of a millimetre and is drawn. The
same guard also stops crosshatch chaining across the gap between its two angle
families.

## Verification

Measured with `samples/svg/spirit-logo-purple-rgb.svg` at `Fill spacing 3`,
`crosshatch`, 0.3 mm pen:

| | before | after |
|---|---|---|
| planned jobs | 1,260 | 1,260 |
| pen cycles | 1,260 | **227** |
| bridged transitions | 0 | 1,033 |
| total draw length | 53,317 mm | 54,326 mm (+1.86%) |

The connectors total 1,009 mm with a median of 0.98 mm. At the measured
actuation of about 1.2 s to seek and 0.46 s to clear, removing 1,033 cycles
saves roughly **29 minutes** of pen actuation while adding about 1.4 minutes of
drawing. Net saving on that file is around 27 minutes.

Sparse fills are unchanged where the guard rejects the connector:

| pattern | spacing | passes | pen cycles | bridges |
|---|---|---|---|---|
| linear | 0.3 | 183 | 4 | 180 |
| linear | 1.0 | 55 | 4 | 52 |
| linear | 3.0 | 19 | 20 | **0** |
| diagonal | 3.0 | 13 | 14 | **0** |

- `python -m unittest discover -s software\tests -p "test_*.py"` passes, 41
  tests. The 4 new cases in `software/tests/test_infill_bridging.py` cover dense
  chaining, sparse non-chaining, the connector staying inside the gap guard, and
  non-serpentine patterns never bridging.
- `python -m py_compile software\qt_svg_to_gcode.pyw software\converter_core\gcode.py`
  passes.

## Struggles and rejected approaches

- The first pass at measuring this used "two-point contours" as the pass count
  and produced nonsense reductions such as -519%, because `planned_contours`
  consolidates contours and because the artwork's own outlines are also pen
  cycles. The correct identity is `pen cycles = planned jobs - bridges`, and
  every number above uses it.
- A first regression test asserted `pen cycles == pass count` for the sparse
  case and failed at 20 versus 19; the extra cycle is the rectangle's own
  outline contour, which a two-point-only count misses.
- Tightening `max_gap` for line families specifically, so that only
  sub-pen-width connectors qualify, was considered and rejected. The existing
  guard is the converter's single criterion for "is this connector short enough
  to draw", and applying a second criterion per pattern family would make the
  behaviour harder to predict.

## Risks and follow-up

- A bridged connector is drawn ink, so chained fills gain short perpendicular
  strokes at the end of each pass. The median is 0.98 mm on the sample above and
  the guard caps it at `max(spacing x 0.85, pen x 6)`, which is 1.8 mm for a
  0.3 mm pen. On a dense fill they are invisible; on sparse shading they are
  small serrations, and that is a visible change to existing hatch output.
- Crosshatch at shading spacing does bridge some passes, because short rows near
  the ends of a region have connectors inside the guard. That was not true of
  `linear` or `diagonal`, so the effect is geometry-dependent rather than
  uniform.
- Judging whether the serrations are acceptable is a plot-level decision. If
  they are not, the lever is the `pen x 6` floor in `max_gap`.

## Files

- `software/converter_core/gcode.py`: line families added to the bridge set.
- `software/tests/test_infill_bridging.py`: new behaviour coverage.
- `software/README.md`: documents which patterns chain.
