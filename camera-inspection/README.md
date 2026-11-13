# XYθ CoreZB Camera Inspection & Precision Calibration

**Project index** · [Hardware inventory](hardware-inventory.md) · [Roadmap](roadmap.md)

This subproject extends the existing XYθ pen plotter with an independent camera gantry, image-based stroke inspection, optical rotary calibration, and a Pi-hosted local sender/HMI on the Raspberry Pi Touch Display 2.

> **Project status:** Design and feasibility documentation. No inspection or compensation software is claimed implemented. Purchase status is not inferred from selections or shopping carts.

## Navigate the project

| Document | Contents |
|---|---|
| **[Hardware inventory](hardware-inventory.md)** | Existing machine hardware, new CoreZB selections, explicitly owned items, purchase checklist and compatibility risks |
| **[Architecture](architecture.md)** | Host/ESP32-P4/RP23CNC responsibilities, Ethernet, coordinate systems and synchronization |
| **[Inspection](inspection.md)** | Captured ink vs executed G-code, projection, segmentation, error metrics and overlays |
| **[Calibration](calibration.md)** | Mandatory independent bed and paper fiducials, pre/post registration, rotary characterization, profile versioning and validation |
| **[Touchscreen](touchscreen.md)** | Pi Touch Display 2 HMI, X/Y/θ/feed DRO, camera, Run/Jog/Tools |
| **[Roadmap](roadmap.md)** | Phases, milestones, verification tasks and unresolved decisions |

## Major subsystems

1. **Existing plotter:** RP23CNC/grblHAL, XY pen gantry, θ rotating 3D-printed bed, independent pen-force subsystem.
2. **CoreZB:** Independently homed overhead camera XY carriage on the same machine frame.
3. **Vision node:** Proposed Waveshare ESP32-P4 Ethernet board and MIPI-CSI camera; performance to benchmark.
4. **Supervisory host:** Raspberry Pi 4 (2 GB) is the planned local G-code sender, capture coordinator and approved-calibration store; sender software and integration remain to be validated. Only one sender may control RP23CNC.
5. **Touchscreen:** Official Raspberry Pi Touch Display 2 attached directly to the Pi 4, with native resolution/orientation support.
6. **Metrology:** Camera registration, rotary-bed center/index calibration, deviation measurement and validated compensation.

## Goals

- **Finish each drawing before inspection**; then scan bed fiducials, paper fiducials and the completed artwork with overlapping CoreZB camera images and known stationary bed/camera positions. Use measured, repeatable errors to calibrate **future** prints.
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
- **Screen fit:** Touch Display 2 native 720×1280 panel, rotate in software as required; no stretched camera image and always-visible X/Y/θ/feed DRO.
- **Safety:** Physical emergency stop independent of software.
- **Procurement honesty:** Selected/cart parts remain unconfirmed until receipts or user confirmation.

## Development order

**Inventory and compatibility → CoreZB motion → post-print image scanning → camera/bed calibration → complete-artwork inspection → systematic error modeling → converter compensation for future prints → independent verification → touchscreen integration.**

See [roadmap.md](roadmap.md) for actionable checklists. Keep measurements, calibration coefficients, firmware versions, and before/after tests together when implementation begins.

## November 2026 processing split

ESP32-P4-ETH handles MIPI-CSI still capture, supported JPEG encoding, optional lightweight image preprocessing and Ethernet delivery. Raspberry Pi 4 (2 GB) orchestrates post-print bed-then-paper fiducial scans, captures and archives images, manages approved profile versions, and drives Touch Display 2. Windows performs authoritative stroke-to-G-code registration, geometric error analysis, and rolling-calibration candidate fitting. Post-print tiled still-image inspection is the baseline; software remains to be implemented and benchmarked. See [architecture.md](architecture.md).

## Post-print registration and version synchronization

Every job requires **post-print bed-then-paper fiducial registration** before inspecting artwork; no routine pre-print optical registration is required. The bed frame describes rotary mechanics; the paper frame describes sheet placement and movement. Keep their models separately versioned. Windows must synchronize and verify the Pi-approved calibration profile before applying compensation through the existing converter engine, and the Pi must verify the pinned profile/hash when accepting G-code. See [architecture.md](architecture.md), [calibration.md](calibration.md), and [inspection.md](inspection.md).
