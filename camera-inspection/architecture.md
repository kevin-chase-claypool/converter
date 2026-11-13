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
5. Pi 4 orchestrates fiducial-first scanning, stores pose-tagged images and registration evidence, and serves the touchscreen; Windows performs authoritative stroke matching, geometric error fitting, and new calibration candidate generation. ESP32-P4 does not own final expected-versus-actual comparison. No second independent grblHAL sender is permitted.
6. Physical emergency stop is independent of the browser UI.

## Coordinates
Use separate frames: stationary machine M, rotating bed B, paper P, and camera C. **Never merge bed and paper registration into one calibration.** The camera's image transform must include:
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
- **Pi 4 (2 GB):** Coordinate motion and fiducial-first capture, receive/archive pose-tagged tiles, offer camera preview and inspection status, publish approved calibration profiles, and transfer inspection datasets to Windows. Lightweight preview/registration checks may run locally, but not the authoritative model fitting.
- **Pipeline:** While the CoreZB moves to the next stationary inspection position, the Pi can analyze the preceding image. Motion/capture coordination must prevent blurred frames; timestamps alone are not a substitute for verified stationary exposure.
- **Memory budget:** Stream/process one tile or bounded batches at a time; avoid retaining full-resolution decoded images for the entire drawing in RAM. Cache compressed source images to storage for reanalysis.
- **Performance gates:** Benchmark acquisition time, JPEG size, Ethernet throughput, preprocessing CPU/PSRAM consumption, Pi RAM/CPU, registration accuracy, and total scan time before moving additional operations to the ESP32.
- **Responsibility boundary:** Windows converter/analysis is the geometric computation authority; Pi is the approved-profile and job-execution authority. Optional ESP32 stroke extraction is a later experiment, not the initial implementation.

## Post-print two-layer fiducial registration and calibration exchange

1. **After drawing, before artwork inspection**, scan bed fiducials first and paper fiducials second; estimate independent bed-to-machine and paper-to-bed transforms with confidence. Hold the bed at a known angle for the subsequent tiled artwork scan. No pre-print optical scan is required for normal jobs.
2. Optional pre-print fiducial captures are reserved for diagnostics or controlled experiments; without a baseline, post-print registration cannot prove whether paper moved during printing.
3. The transform chain is `p_M = T_MB(theta) * T_BP * p_P` (homogeneous coordinates); camera observations also require calibrated `T_CM`/camera intrinsics and exposure pose. Bed calibration and paper registration are separate, independently versioned records.
4. Pi retains raw imagery, fiducial measurements, capture pose, approved model history and job manifests. Windows receives datasets and performs stroke-to-G-code correspondence, residual analysis, candidate model fitting and validation. Identical overlapping strokes can remain unidentifiable despite good fiducial registration; label them ambiguous.
5. Windows checks the Pi's approved calibration profile ID, content hash and schema compatibility **before generating compensated G-code**. It applies the correction once using the converter's existing XYθ kinematics, submits the job with profile/hash and stroke-to-G-code manifest, and the Pi verifies the job before streaming to RP23CNC. The profile is pinned for the accepted job; new models affect future jobs only.
6. Pi stores inspection history and approves new model versions only after independent validation. The legacy bed compensation field can remain the numerical correction engine while camera observations replace the manual acquisition workflow. No automatic self-promotion of unvalidated profiles.
