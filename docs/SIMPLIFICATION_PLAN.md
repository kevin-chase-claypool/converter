# Code Simplification Plan

## Before / after footprint

Measured on 2026-06-04, excluding `__pycache__` and `software/qt_debug.log`.

| Area | Before | After |
|---|---:|---:|
| Host application source | 3,279 lines in 2 Python files | 2,746 lines in 7 Python files |
| Generated/sample G-code | 8,715 lines | 8,715 lines |
| Legacy Tk UI | Present inside `svg_to_gcode.pyw` | Removed |
| Qt settings definitions | Repeated in UI constructor and parser | Centralized in `converter_core/settings.py` |

Net host-source reduction: 533 lines, about 16%.

The code footprint that matters for development is now:

| Source file | Role | Lines |
|---|---|---:|
| `software/qt_svg_to_gcode.pyw` | Primary PySide6/OpenGL UI | 1,171 |
| `software/converter_core/kinematics.py` | Bed/tool transforms, theta planning, contour ordering | 677 |
| `software/converter_core/geometry.py` | SVG parsing, transforms, hatching, clipping helpers | 565 |
| `software/converter_core/gcode.py` | G-code output and preview move records | 208 |
| `software/converter_core/settings.py` | `Settings` dataclass and UI field metadata | 106 |
| `software/svg_to_gcode.pyw` | Compatibility shim | 14 |
| `software/converter_core/__init__.py` | Public engine exports | 5 |
| Total host source |  | 2,746 |

## Same-feature target

The project can be simplified while keeping the same useful feature set:

- SVG vector parsing for paths, shapes, transforms, strokes, fills, and `<use>`.
- Fill hatching, tone hatching, and raster shading.
- Bed clipping, pen-width compensation, scaling, Y flip, and machine constants.
- XY plus rotating-bed theta planning with r-theta default and DP/greedy comparison modes.
- G-code output with `X/Y/A`, optional `Z`, `M3/M5`, dwell, feed rates, and final park.
- Qt desktop UI, OpenGL preview, playback, command list, estimate, colors, and conversion.
- Report-friendly docs that explain software, firmware, integration, tests, and tradeoffs.

The removed feature is the legacy Tk UI inside `svg_to_gcode.pyw`. It was not part of the primary
workflow and duplicated app logic now handled by the Qt UI.

## Implemented module split

| File | Purpose |
|---|---|
| `software/converter_core/settings.py` | Machine settings, checkbox/text field metadata, and parser helpers |
| `software/converter_core/geometry.py` | SVG loading, transforms, shape flattening, vector hatching, stroke/fill helpers, bed clipping |
| `software/converter_core/kinematics.py` | Bed/tool transforms, r-theta/DP/greedy theta planning, contour ordering, 2-opt |
| `software/converter_core/gcode.py` | Command formatting, dwell handling, conversion, preview move records |
| `software/converter_core/__init__.py` | Public API consumed by the UI and compatibility shim |
| `software/svg_to_gcode.pyw` | Backward-compatible shim for old imports and simple CLI conversion |

The Qt app intentionally remains in one file for this pass because splitting widgets and playback would
not reduce behavior risk as much as separating the conversion engine did.

## Reduction strategy

1. Delete the legacy Tk UI from `svg_to_gcode.pyw`.
   - Status: done.

2. Move settings metadata into the `Settings` dataclass.
   - Status: done via `TEXT_FIELD_GROUPS`, `CHECKBOX_FIELDS`, and `settings_from_values`.

3. Unify G-code generation and preview move generation.
   - Today the app needs both saved G-code text and a move list for preview.
   - Make one planner emit typed `Move` records, then render those records as G-code or preview data.
   - Expected reduction: 180-300 lines.
   - Benefit: fewer mismatches between actual output and preview.

4. Split conversion stages into pipeline modules.
   - Status: done for settings, geometry, kinematics/planning, and G-code.
   - `load_svg -> normalize_geometry -> shade -> clip -> plan -> emit`.
   - Expected line count does not drop by itself, but it makes code easier to test and easier to document.

5. Replace custom SVG path/transform parsing if dependencies are acceptable.
   - Expected reduction: 250-450 lines.
   - Risk: medium, because the current parser behavior must be regression-tested against existing samples.

6. Keep the OpenGL preview, but move math/cache code into small helpers.
   - Expected reduction: 100-180 lines.
   - Benefit: the preview file becomes mostly rendering, not planner math.

7. Move generated G-code samples out of the main report-facing footprint.
   - Keep one short sample in `samples/gcode/`.
   - Put large generated outputs in `artifacts/` or regenerate them from scripts.
   - Expected visible repository reduction: up to 8,000+ lines.
   - This does not change code, but it makes the project easier to review.

## Recommended report framing

Use the refactor as a system-integration argument:

- The host software is the integration layer between artwork, machine kinematics, firmware G-code,
  and the pen-pressure subsystem.
- The simplified architecture mirrors the real system boundaries: geometry, kinematics, planning,
  G-code protocol, preview, and UI.
- The most important correctness rule is that preview and output use the same planned moves.
- The firmware-facing contract is intentionally small: `G0/G1`, `X/Y/A`, optional `Z`, `M3/M5`,
  `G4`, and `M2`.

## Remaining reduction options

The implemented pass preserves behavior and keeps the current custom SVG parser. The remaining ways to
shrink the code further are:

- Unify saved G-code generation and preview move generation through one typed move pipeline.
- Move generated `.gcode` artifacts out of the main review footprint or regenerate them from scripts.
- Replace the custom SVG parser with a proven SVG geometry dependency after regression tests exist.
- Split the Qt preview and main-window code if future UI work becomes difficult.
