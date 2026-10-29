---
id: WSW-20261028-002
date: 2026-10-28
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: superseded
components:
  - software/converter_core/bed_calibration.py
  - tools/make_bed_error_calibration.py
  - tools/measure_bed_error_photo.py
  - tools/analyze_bed_error_calibration.py
  - software/tests/test_bed_compensation.py
  - software/tests/test_bed_photo_measurement.py
  - samples/gcode/bed-error-map-dense-91.gcode
  - samples/gcode/bed-error-map-dense-91.csv
tags:
  - bed-calibration
  - bed-compensation
  - dense-mesh
  - photo-measurement
  - station-layout
  - residual-error
related:
  - WSW-20261026-003
---

# Add a 91-station dense bed-calibration mesh

> Superseded by `WSW-20261029-001`: the first physical print showed 13 pass
> lanes crossing their own station-number glyphs. Use `dense-91-v2`.

## Summary

The bed calibration now supports a second station layout with 91 spatial
measurements compared with the existing 37. It uses smaller L marks, tighter
pass lanes, smaller labels, and repositioned outer fiducials to double the
spatial sampling density while keeping the original nine-angle protocol and
13-inch test field.

The existing `bed-error-map.gcode`, 37-station CSV, accepted
`4bad792e35ad` profile, and default command remain unchanged.

## Reason

The accepted 37-station map has gaps of roughly 45-65 mm between radial rings
and 22.5-45 degrees between stations. Its independent compensated verification
still has a `0.591 mm` maximum residual. That residual is larger than the
approximately `0.104 mm` minimum margin between the commanded Ben2 wave rows
and their pen-clearance envelope, so sparse interpolation can plausibly
contribute to repeatable row convergence even though the saved G-code itself
does not contain a crossing.

Additional stations previously required more sheet area because each station
used 4 mm arms and 10 mm lanes. Smaller stations make a denser field possible
without increasing the paper or changing the measurement protocol.

## Implementation

`CalibrationLayout` now owns all layout-dependent values: ring positions and
station counts, mark size, lane offset, label placement and size, test radius,
and fiducial geometry. The original values remain the `standard-37` layout.

The new `dense-91` layout contains:

| Radius | Stations |
|---:|---:|
| 0 mm | 1 |
| 30 mm | 6 |
| 60 mm | 12 |
| 90 mm | 18 |
| 120 mm | 22 |
| 148.5 mm | 32 |

It uses 3 mm L arms, 7 mm lane offsets, 1.8 mm labels, and smaller fiducials
at 160 mm radius. The outer station ring phase and fiducial orientation keep
the nearest fiducial-to-station-ink separation above 5 mm. The full layout
reaches 164.0 mm from the registered centre, inside the 165.1 mm test radius.

Measurement CSVs now include `layout_id`. The analyzer detects that value
automatically and rejects a known layout passed with a conflicting CSV. Older
37-station CSVs without the column continue to resolve to `standard-37`.

## Verification

- `python -m unittest discover -s software\tests -p "test_bed_*.py" -v`:
  all 55 bed-calibration and compensation tests pass.
- `python -m unittest discover -s software\tests -p "test_*.py"`: all `562`
  converter tests pass with one expected OpenGL-context skip.
- The dense generator produced 91 stations, 819 station marks, four fiducials,
  and 823 measurement rows.
- Minimum station-centre spacing is `28.713 mm`; minimum label-to-foreign-mark
  separation was reviewed at `6.927 mm`; the fiducial-to-station regression
  requires more than 5 mm and passes.
- `python tools\check_macros.py samples\gcode\bed-error-map-dense-91.gcode`
  passes.
- `python tools\check_gcode_motion.py
  samples\gcode\bed-error-map-dense-91.gcode --strict` passes with 2,336
  drawing moves, 1,069 travel moves, no pen-up rotation except the intended fed
  registration moves, and no bare rotating `G0`.
- Dense G-code SHA-256 is
  `5CC54A108A303FE70CFEBC120EEBDC3B114198FDDE949998DA04AB0BD65E7D77`;
  its 823-row CSV SHA-256 is
  `9C77AFEA0F7675E3553601B27F27CDDADB63FBB27413E1D994DCFFF754990BF7`.
- A synthetic dense field produces a 91-sample profile with the existing
  validation gates.

## Struggles and rejected approaches

- The first outer-ring phase placed a station on the fiducial diagonal, and
  the original inward fiducial arm intersected the station lane. Changing only
  the station count would have looked valid in an aggregate count while
  breaking component recognition.
- A 30-point outer ring could not keep all four quarter-turn fiducials halfway
  between station angles. Redistributing to 22 middle-ring and 32 outer-ring
  stations kept the total at 91 and removed the collision.
- Shrinking only the L marks was insufficient. Lanes, labels, and fiducials
  also had to shrink or move to preserve readable separation.

## Risks and follow-up

No 91-station sheet has been printed or measured yet. Its smaller components
require a sharp, straight-down, high-resolution photograph; the photo tool
starts the dense classification floor at 14 px and may need tuning from the
generated overlay.

The dense field is a calibration candidate, not a new active compensation
profile. Acceptance still requires a repeat sheet for noise, the normal M-12
fit gates, an independently compensated verification print, and improvement
in the worst residual without regressions at any angle stage.

## Files

- `software/converter_core/bed_calibration.py`: layout model, geometry,
  layout-aware CSV parsing, and profile analysis.
- `tools/make_bed_error_calibration.py`: `--layout dense-91` generation.
- `tools/measure_bed_error_photo.py`: dense defaults and layout metadata.
- `tools/analyze_bed_error_calibration.py`: layout detection and comparison.
- `software/tests/test_bed_compensation.py`: dense geometry, program, CSV, and
  analysis regressions.
- `software/tests/test_bed_photo_measurement.py`: 819-mark dense CSV coverage.
- `samples/gcode/bed-error-map-dense-91.gcode`: dense one-pen calibration.
- `samples/gcode/bed-error-map-dense-91.csv`: 823-row measurement template.
- `software/README.md`, `docs/testing/TEST_PLAN.md`, and
  `docs/project/ROADMAP.md`: current workflow, bench procedure, and candidate
  status.
