# System architecture

## Hardware
- **Existing plotter:** XY Cartesian pen gantry plus θ rotating circular bed (~18-inch print area); RP23CNC/grblHAL and Windows ioSender V2.
- **Camera gantry:** Separate overhead CoreZB/CoreXY-style motion system, mechanically attached to the plotter frame, independently homed and controlled.
- **Vision node:** Waveshare ESP32-P4-ETH with MIPI-CSI camera (OV5647 proposed; camera-module pinout/driver support must be verified against the exact board and ESP-IDF version).
- **Host:** Windows PC running a fork of ioSender V2 plus supervisory inspection logic as needed.
- **Display:** Fixed 7-inch 1280×720 landscape touchscreen with an Ethernet-connected browser-capable controller, rather than a long moving MIPI-DSI cable.
- **Network:** Ethernet switch connects plotter, camera controller, host, and touchscreen. Switch input voltage, PoE requirements, bandwidth and port count require verification before purchasing. Existing fused 12 V power is preferred.

## Authority and data flow
1. ioSender owns the machine-control connection to RP23CNC/grblHAL.
2. A host-side API/WebSocket service (to be developed) exposes approved state and actions to the touchscreen.
3. Host supplies **executed** reference toolpath segments and synchronized pose information to the inspection pipeline.
4. ESP32-P4 captures frames and may perform local line detection, geometric comparison, and overlay generation subject to benchmarking.
5. Inspection results return to the host/display. No second independent grblHAL sender is permitted.
6. Physical emergency stop is independent of the browser UI.

## Coordinates
Use a common stationary machine frame M, a rotating bed/paper frame P, and a camera frame C. The camera's image transform must include:
- calibrated bed center, angular zero and actual θ pose;
- camera gantry X/Y pose and homing offsets;
- camera mounting extrinsics, scale, lens distortion and paper plane;
- timestamps/pose at **image exposure**, not merely latest network messages.

For bed point p in the machine XY frame at θ=0, nominal rotated position is:
`m = c + R(θ)(p - c)`.
Then project from machine coordinates to the camera using calibrated extrinsics/intrinsics.

## Synchronization strategy
Start with **stop-and-inspect**: pause or inspect only completed regions, settle camera and bed, capture frame, record both controller positions, then resume. Continuous inspection requires reliable exposure-time pose synchronization and performance measurements. Camera controller motor step count alone is not a measurement of physical carriage position.

## Boundaries
Pen-pressure/load-cell controller is separate from ioSender. Do not invent a pressure readout or control path. The inspection pipeline is not a replacement for the machine controller.
