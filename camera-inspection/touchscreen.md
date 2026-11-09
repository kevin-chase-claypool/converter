# 7-inch 720p touchscreen specification

## Physical canvas
- Native **1280 × 720**, landscape, 16:9. Design with fixed bounded regions and no vertical scrolling.
- Browser-based display on a frame-mounted controller; do not stretch camera images. Maintain aspect ratio and crop/letterbox as necessary.
- Industrial dark UI, legible DRO and practical touch targets.

## Always visible
1. Header: XYθ machine identity, machine state, work-coordinate system (e.g. G54).
2. **DRO row:** X (mm), Y (mm), θ (degrees), and **reported feed rate (mm/min)**.
3. Camera viewport with optional inspection overlays.
4. Job name, completion progress and ETA when calculable.
5. Main control tab selector.

## Tabs
- **RUN:** feed override (%) with ±10% and 100% reset; start/resume, feed hold, stop.
- **JOG:** X/Y jog, θ jog, step-size selection and homing as allowed by machine state.
- **TOOLS:** pen-change workflow, camera registration/calibration, work-zero and diagnostics, subject to verified host/controller support.
- Potential future **INSPECT** mode: expected G-code, detected ink, deviation heatmap, quantitative error metrics.

## Important distinctions
- Feed override percentage is a **commanded override**; feed DRO should show **reported actual feed** and must not be confused with the override.
- No pen-force readout: the pen-pressure/load-cell system is separate from ioSender and is not accessible over the planned control link.
- UI is a concept, not a live controller. Sample values and camera artwork are placeholders.
- Host validates commands and machine state. No browser directly streams G-code to grblHAL.
- Physical E-stop remains independent of software.
