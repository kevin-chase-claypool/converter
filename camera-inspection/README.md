# XYθ CoreZB Camera Inspection & Precision Calibration

**Project index** · [Hardware inventory](hardware-inventory.md) · [Roadmap](roadmap.md)

This subproject extends the existing XYθ pen plotter with an independent camera gantry, image-based stroke inspection, optical rotary calibration, and a remote ioSender control display.

> **Project status:** Design and feasibility documentation. No inspection or compensation software is claimed implemented. Purchase status is not inferred from selections or shopping carts.

## Navigate the project

| Document | Contents |
|---|---|
| **[Hardware inventory](hardware-inventory.md)** | Existing machine hardware, new CoreZB selections, explicitly owned items, purchase checklist and compatibility risks |
| **[Architecture](architecture.md)** | Host/ESP32-P4/RP23CNC responsibilities, Ethernet, coordinate systems and synchronization |
| **[Inspection](inspection.md)** | Captured ink vs executed G-code, projection, segmentation, error metrics and overlays |
| **[Calibration](calibration.md)** | Center/index circles, fitted rotation center, eccentricity, angular error, backlash and correction validation |
| **[Touchscreen](touchscreen.md)** | 7-inch 1280×720 landscape UI, X/Y/θ/feed DRO, camera, Run/Jog/Tools |
| **[Roadmap](roadmap.md)** | Phases, milestones, verification tasks and unresolved decisions |

## Major subsystems

1. **Existing plotter:** RP23CNC/grblHAL, XY pen gantry, θ rotating 3D-printed bed, independent pen-force subsystem.
2. **CoreZB:** Independently homed overhead camera XY carriage on the same machine frame.
3. **Vision node:** Proposed Waveshare ESP32-P4 Ethernet board and MIPI-CSI camera; performance to benchmark.
4. **Supervisory host:** ioSender V2 fork on Windows remains sole authority for CNC commands and G-code streaming.
5. **Touchscreen:** Browser-driven 7-inch 720p landscape machine display.
6. **Metrology:** Camera registration, rotary-bed center/index calibration, deviation measurement and validated compensation.

## Goals

- Synchronize camera and plotter poses, initially with **stop-and-inspect** captures.
- Compare only **executed** reference strokes against actual ink, not future planned strokes.
- Show projected path, observed ink, and quantified deviations in calibrated millimeters.
- Use visible black circles at the embedded bed center and perimeter index positions for calibration.
- Fit multi-angle perimeter-target measurements to estimate the physical rotation center; characterize repeatable mechanical errors.
- Validate compensation on independent test patterns before integrating into a single control layer.

## Confirmed design constraints

- **No pen-force DRO:** The pen-pressure/load-cell controller is separate from ioSender.
- **Single motion authority:** Browser and ESP32-P4 must not independently stream commands to RP23CNC.
- **Real measurement vs commanded coordinates:** Step counts do not establish physical accuracy.
- **Optical reference limitations:** A center magnet may not coincide with the true rotation center; one perimeter marker does not uniquely establish all angular errors.
- **Screen fit:** 1280×720, no scrolling, no stretched camera image; always-visible X/Y/θ/feed DRO.
- **Safety:** Physical emergency stop independent of software.
- **Procurement honesty:** Selected/cart parts remain unconfirmed until receipts or user confirmation.

## Development order

**Inventory and compatibility → CoreZB motion → synchronized image capture → camera calibration → executed-toolpath inspection → rotary characterization → validated compensation → touchscreen integration.**

See [roadmap.md](roadmap.md) for actionable checklists. Keep measurements, calibration coefficients, firmware versions, and before/after tests together when implementation begins.
