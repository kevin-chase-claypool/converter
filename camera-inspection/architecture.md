# System architecture

## Hardware
- **Existing plotter:** XY Cartesian pen gantry plus θ rotating circular bed (~18-inch print area); RP23CNC/grblHAL; Raspberry Pi 4 is the planned local sender/HMI host, replacing the laptop as the machine-side runtime.
- **Camera gantry:** Separate overhead CoreZB/CoreXY-style motion system, mechanically attached to the plotter frame, independently homed and controlled.
- **Vision node:** Waveshare ESP32-P4-ETH with MIPI-CSI camera (OV5647 proposed; camera-module pinout/driver support must be verified against the exact board and ESP-IDF version).
- **Host:** Raspberry Pi 4 (2 GB RAM) running the G-code sender/HMI and supervisory post-print inspection. Exact sender software and integration method remain to be validated; the Windows laptop remains a development workstation.
- **Display:** Official Raspberry Pi Touch Display 2, directly attached to the Pi 4 over its supported display/touch interfaces. This is not a separate Ethernet browser terminal. Native panel orientation and resolution must be verified in the deployed setup.
- **Network:** Ethernet switch connects RP23CNC, ESP32-P4-ETH, and Pi 4; the touchscreen is attached directly to the Pi. Switch input voltage, PoE requirements, bandwidth and port count require verification before purchasing. Existing fused 12 V power is preferred.

## Authority and data flow
1. One sender process on the Pi 4 owns the machine-control connection to RP23CNC/grblHAL; final software selection is pending.
2. Pi-local HMI presents approved sender actions, status, camera preview, and inspection results on the Touch Display 2.
3. Pi retains the **executed** reference toolpath and records camera gantry pose and bed angle for inspection registration.
4. ESP32-P4 captures MIPI-CSI images, uses hardware JPEG where supported, and can crop, grayscale, or threshold images in software after benchmarking. It sends JPEG/original-quality inspection images and optional derived data over Ethernet.
5. Pi 4 performs fiducial identification, camera/bed registration, image-to-reference alignment, geometric error measurement, and future-print calibration estimates. ESP32-P4 does not own final expected-versus-actual comparison. No second independent grblHAL sender is permitted.
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

## Synchronization strategy — post-print inspection (preferred)
Complete the entire drawing before scanning. Then hold the bed at a known angular position, home/locate CoreZB, raster-scan the completed artwork using overlapping stationary captures, and record the camera pose and bed angle for each tile. Stitch/register tiles into paper coordinates and compare against the final intended G-code geometry. There is **no need to synchronize exposures with moving pen strokes**. Calibration profiles derived from repeatable systematic errors can adjust **future** converter output, subject to independent validation. Continuous in-process inspection is a possible later feature, not the initial design. Camera motor step count alone is not proof of physical position; camera-to-bed calibration and paper stability remain necessary.

## Boundaries
Pen-pressure/load-cell controller is separate from ioSender. Do not invent a pressure readout or control path. The inspection pipeline is not a replacement for the machine controller.

## Distributed processing and performance plan (November 2026)

- **ESP32-P4:** Camera sensor configuration, stationary still capture, hardware-assisted JPEG where supported by the selected sensor/driver, optional ROI crop/grayscale/thresholding, Ethernet transfer, and capture metadata. Preserve access to the original full-resolution image; do not irreversibly discard information during preprocessing.
- **Pi 4 (2 GB):** Receive and archive tiles, associate each with bed angle and camera XY pose, detect fiducials, calibrate perspective and lens distortion, compare observed strokes with executed G-code, quantify errors in millimeters, and visualize findings on Touch Display 2.
- **Pipeline:** While the CoreZB moves to the next stationary inspection position, the Pi can analyze the preceding image. Motion/capture coordination must prevent blurred frames; timestamps alone are not a substitute for verified stationary exposure.
- **Memory budget:** Stream/process one tile or bounded batches at a time; avoid retaining full-resolution decoded images for the entire drawing in RAM. Cache compressed source images to storage for reanalysis.
- **Performance gates:** Benchmark acquisition time, JPEG size, Ethernet throughput, preprocessing CPU/PSRAM consumption, Pi RAM/CPU, registration accuracy, and total scan time before moving additional operations to the ESP32.
- **Responsibility boundary:** The Pi is the geometric authority. Optional ESP32 stroke extraction is a later experiment, not the initial implementation.
