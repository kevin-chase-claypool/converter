---
id: WSW-20261123-011
date: 2026-11-23
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/converter_core/path_join.py
  - software/converter_core/structure_tensor.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
  - software/tests/test_path_join.py
tags:
  - cmyk
  - color-management
  - display-p3
  - icc
  - pen-down
  - path-chaining
  - toolpath-efficiency
  - continuous
related:
  - WSW-20261123-005
  - WSW-20261123-010
  - docs/proposals/flow-field-cmyk.md
---

# Color-manage CMYK sources and reduce adjacent pen lifts

## Summary

CMYK image inputs now honor their embedded ICC profile and EXIF orientation
before separation. The CMYK tab also has an explicit **Pen-down chain** control
and a **Continuous row screen (adjacent joins)** style for trading visible
connector ink against substantially fewer M3/M5 toolhead cycles.

## Reason

The current portrait source, `IMG_0514.JPG`, carries a Display P3 ICC profile.
The converter previously read its raw channel values as sRGB, shifting colour
before CMYK separation.

The saved Edge-flow recipe also produced about `23,500` separate marks across
the four inks. At the toolhead's multi-second engage/lift cycle, that path
fragmentation dominates elapsed time even when the drawing distance is
reasonable. The owner asked to keep pen lifts possible but minimize them,
especially between adjacent lines.

## Implementation

- `prepare_image_tones()` and Auto image analysis now share one loader that
  applies EXIF orientation, converts embedded ICC profiles to sRGB with
  perceptual rendering, and falls back to ordinary RGB conversion when a
  profile is malformed or unavailable.
- Edge-flow can retain up to `4 mm` of tone-off gap along the same traced
  streamline. This preserves the flow path while removing repeated lifts in
  dense passages.
- `chain_nearby_contours()` orders open marks by nearest endpoint and draws a
  bridge only within the configured gap. Closed contours and tagged Wave rows
  are preserved.
- The CMYK tab exposes **Pen-down chain / Keep pen down** with a default
  adjacent-connector gap of `5.0 mm`. Its state and results are stored with the
  artwork recipe and saved print-set manifest.
- **Continuous row screen (adjacent joins)** extends the existing rectilinear
  tone screen by joining nearest non-overlapping row runs into long chains.
  This is the speed-oriented option when straight screen directions are
  acceptable.

## Verification

- Regression tests verify ICC conversion invocation, EXIF orientation, the
  adjacent endpoint bridge, gap-limit behavior, preservation of closed and
  Wave rows, and the new UI round trip.
- A synthetic continuous-screen regression produces one chain instead of more
  than twenty separate rectilinear chains.
- The recipe used for the first measurement falls from `23,516` open marks to
  `10,596` with the `4 mm` local bridge and default `5 mm` endpoint chain.
- Raising only the endpoint bridge to `12 mm` measured `3,832` marks, showing
  the tunable tradeoff; that larger gap was not made the default because the
  owner asked to keep connectors adjacent.
- The later active Fine-detail recipe contains `120,676` raw marks. Default
  chaining reduces that to `13,533`; exact G-code planning emits `7,884` M3
  sequences across the four files (`1,441 / 1,665 / 3,209 / 1,569`).
- All four exact G-code files pass `tools/check_gcode_motion.py --strict` with
  no bare rotating `G0`, bed-step, or A-rate violation.
- The Continuous row style produces `530` marks for the earlier recipe and
  `482` for the active Fine-detail recipe before planner compaction.
- The focused CMYK and path-join suites pass `145` tests.
- Complete converter discovery passes `656` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

Large unconstrained chaining can collapse each ink to one stroke, but at
`30-50 mm` gaps it introduces conspicuous face-crossing diagonals and changes
the image. The default therefore remains local. A fully continuous rectilinear
screen is fast but loses the Edge-flow portrait texture, so it is a separate
operator-selected style rather than an automatic replacement.

ICC conversion corrects input-space mismatch; it does not calibrate the
physical pen transmittances, paper response, or four-pass registration.

## Risks and follow-up

Every connector is visible ink. Increasing the gap removes more toolhead
cycles while making the line screen and colour denser in the connector areas.
The Continuous row style should be judged on a physical four-pass sheet
alongside the Edge-flow result.

## Files

- `software/converter_core/cmyk.py`: sRGB/EXIF loading and continuous row
  screen.
- `software/converter_core/path_join.py`: constrained open-mark chaining.
- `software/converter_core/structure_tensor.py`: same-streamline tone bridge.
- `software/generator_tabs/cmyk_tab.py`: user controls, recipe persistence,
  SVG integration, and set-manifest evidence.
- `software/tests/test_cmyk_tab.py` and `software/tests/test_path_join.py`:
  profile, orientation, chaining, and style regressions.
- `software/README.md` and `docs/proposals/flow-field-cmyk.md`: current
  operator behavior and speed/colour tradeoff.
