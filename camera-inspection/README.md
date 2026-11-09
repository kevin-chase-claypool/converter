# XYθ Camera Inspection & Calibration Project

**Status:** Design and feasibility planning. No functionality in this folder is implemented or validated.

This project captures the architecture discussed for extending the existing XYθ pen plotter with an independent CoreZB camera gantry, an ESP32-P4-ETH vision controller, an ioSender V2 fork, a 7-inch control touchscreen, and metrology-based calibration and compensation.

## Documents
- [Architecture](architecture.md) — hardware, communication, coordinate ownership, synchronization
- [Inspection pipeline](inspection.md) — actual ink vs expected G-code, overlays, error metrics
- [Calibration and compensation](calibration.md) — optical center/index targets, rotary error, backlash, validation
- [Touchscreen interface](touchscreen.md) — 1280×720 layout and control requirements
- [Roadmap and open questions](roadmap.md) — milestones, risks, test criteria

## Established constraints
- The pen control/load-cell subsystem is separate from ioSender; **do not display pen force or pressure telemetry** as if available to ioSender.
- The existing ioSender host is the sole authority for grblHAL motion commands and job streaming. A browser client must not independently command the RP23CNC.
- Camera images, example coordinate values, and projected deviation results in UI concepts are illustrative, not live measurements.
- Do not claim that a browser API already exists in ioSender V2; the fork requires implementation and verification.
- No fiducials are required in every artwork image if repeatable calibrated machine coordinates suffice, but optical references remain useful for periodic verification.

## System intent
1. Move the camera independently of the pen using the CoreZB gantry.
2. Acquire inspection images and compare completed ink strokes to the intended toolpath.
3. Report and visualize line-position deviations in calibrated physical units.
4. Characterize the 3D-printed rotary bed and compensate **repeatable** errors after independent validation.
5. Expose live camera, DRO, motion controls and inspection results on a 7-inch landscape display.

## Engineering rule
Maintain a clear distinction between commanded motor coordinates, actual mechanical position, and camera measurement uncertainty. Do not apply the same correction in multiple control layers.
