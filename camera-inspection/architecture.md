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

## Purpose of the two post-print fiducial layers

Bed fiducials are the **stable physical reference**: first register the rotating bed relative to the calibrated camera/machine frame, then register the sheet using its separate paper fiducials relative to that bed. Only after both checks pass should Windows project the job's executed stroke trajectories and measure ink residuals. This is why both fiducial types are necessary even though neither requires a routine pre-print scan. Bed fiducials anchor the physical rotary frame; paper fiducials identify the sheet pose; the resulting residuals characterize the printed geometry. Distinguish persistent bed/rotary model errors from per-job paper placement, and never treat a sheet offset as a permanent rotary correction. A post-print observation cannot by itself time-localize paper movement during the print.

## Offline inspection, synchronization gate and retention

The Pi starts post-print inspection **only after confirmed completion of the pen end-print park sequence**, even if Windows is offline. It captures bed fiducials, paper fiducials, and artwork tiles, committing a checksummed, job-ID-addressed inspection package on microSD. SQLite tracks durable job/transfer states. Windows resumes missing verified chunks on reconnect, performs stroke matching and rolling-calibration evaluation, and returns a signed/hashed result for Pi-side commit. Power loss, reconnect and repeated acknowledgments must be safe and idempotent.

**Submission gate:** The Pi rejects the next G-code submission until the previous inspection/calibration transaction is resolved and acknowledged. Windows also checks the Pi's approved profile ID/hash/schema before final compensated G-code generation and again at submission. If the profile changed, invalidate and regenerate the compensated G-code. Successful evaluation may leave calibration unchanged if evidence is insufficient. On failure, offer explicit **Retry** or **Cancel Sync & Revert**; cancellation preserves the last approved profile, records the exception, and releases the gate only after the Pi durably commits that decision. Rolling back an already activated profile is a distinct internal transaction.

**Automatic retention:** Keep exactly the latest three approved calibration generations (`N`, `N-1`, `N-2`), including compact geometry and validation records. Do not advance generations for unchanged/failed/canceled evaluations. After successful durable promotion, prune older unreferenced generations; protect any profile referenced by an unresolved job. JPEGs are temporary and are automatically removed after verified analysis/result commit or acknowledged cancellation. Pending jobs retain the files necessary for recovery. Enforce free-space reserve and fail safely rather than silently dropping data. No manual cleanup in normal operation.

## East-indexed coded bed fiducials (selected design)

Use approximately 20 uniquely identified, approximately evenly spaced AprilTags around the outer edge of the 18-inch rotating bed, outside the central 14-inch printable region. Reserve the majority of the 2-inch radial annulus for painter's tape. Provisional 12 mm tags at approximately 218 mm center radius require optical and physical clearance validation. The magnetic Theta index sensor is directly east (+X) of bed center; home establishes nominal θ=0°. The CoreZB camera uses an east-side optical station while Theta rotates tags into view. During commissioning, measure and store actual marker coordinates relative to the homed index: precise tag installation angles and ideal 18° spacing are **not** required. During post-print inspection, compare observed ring poses to this baseline, then separately register paper and artwork. The map measures relative repeatability and does not by itself establish absolute angular accuracy. See [calibration.md](calibration.md).

## Optical reference registration — supersedes magnetic-sensor assumptions

For the camera inspection workflow, do **not** assume a Hall-effect sensor is available to locate the bed center or establish Theta zero. The historical Theta index is east (+X), but the **operational inspection reference** is optical: home CoreZB; use multiple observations of permanent outer-ring coded tags while Theta rotates to estimate the physical bed center **first**; then bring designated tag B00 to the calibrated east optical station to establish θ=0°. Keep the completed artwork and painter's tape installed throughout; the ring is outside the printable area and must remain unobstructed. Actual tag locations are commissioned, not presumed perfectly spaced. Dedicated paper fiducials are optional; preserve uncertainty about paper movement and global registration when absent. Controller angular zero and optical zero must be reconciled explicitly before generating/executing compensated G-code. See [calibration.md](calibration.md).
