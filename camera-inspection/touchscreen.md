# Raspberry Pi Touch Display 2 — local HMI specification

## Physical canvas
- Official Raspberry Pi Touch Display 2 connected directly to the Raspberry Pi 4 (2 GB); **not** a networked standalone display. The previous 1280 × 720 landscape design was a concept for different hardware and is superseded.
- Design the UI for the Touch Display 2's native 720 × 1280 panel with software rotation as needed. Final portrait/landscape orientation and touch calibration must be verified on the mounted display. Maintain camera aspect ratio without stretching.
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
- Pi-hosted sender validates commands and machine state. HMI is a client of the single motion-authority sender; a second process must not independently stream G-code to grblHAL.
- Physical E-stop remains independent of software.

## Camera and inspection workload

- Display a camera preview or selected still image delivered over Ethernet from ESP32-P4-ETH, with optional fiducial and error overlays generated on the Pi.
- The Pi, not the ESP32-P4, performs final expected-versus-observed stroke comparison and reports error measurements.
- Use low-rate preview and individual full-resolution stills for post-print inspection; continuous real-time video analysis is not required.
- Prioritize responsive Run/Hold/Stop controls while image processing runs; isolate long-running analysis from the HMI event loop and monitor memory on the 2 GB Pi.
