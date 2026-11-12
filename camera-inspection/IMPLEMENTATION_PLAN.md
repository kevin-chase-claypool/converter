# Inspection software — initial implementation plan

Status: **proposed / not yet implemented**. This plan complements [calibration.md](calibration.md), not a claim of working closed-loop inspection.

## Objective and scope

Build a camera-inspection subsystem for the XY–theta pen plotter, using a separately driven CoreXY camera gantry (sometimes called CoreZB), with a Raspberry Pi 4 supervisory/HMI host and a camera endpoint whose final interface is still to be verified. The camera is approximately 300 mm above the paper; exact camera, lens, transport, and achievable accuracy remain subject to bench validation.

Primary goals:
1. Quantify and correct **systematic machine geometry errors** before drawing, particularly magnetic-origin offset, theta rotation-center error, ratio drift, backlash, and spatial distortion.
2. Inspect a **completed** drawing against the expected SVG without requiring the camera to have been physically centered over its carriage.
3. Improve **future prints** by proposing and validating new calibration/compensation profiles from accumulated post-print evidence. Real-time inspection and correction are **out of scope**.
4. Preserve traceable evidence (raw images, poses, calibration versions, deviation maps and uncertainty), distinguishing observed errors from hypothesized causes.

## Existing architecture to preserve

- Physical X/Y homing followed by TMAG5273 center-magnet raster/centroid registration as G54 X0/Y0; perimeter index establishes G54 A0 via controller-owned P100 macro (see ADR-003).
- The center magnet is a **nominal registration reference, not proof of the mechanical rotation axis**. The pen/sensor offset and P100 corrections are separate from actual rotary-center estimation.
- Converter has theta drive-ratio settings and calibration plots, rotation-center test routines, and a bed-error compensation pipeline. **Do not apply a second untracked correction** on top of an active profile.
- Existing fiducials and generated calibration marks can help localize images, but printed marks can inherit the very machine error being measured.
- The promoted 2026-10-29 centered dense-v3 compensation profile was owner-selected despite failing formal max-error/improvement gates. Revalidate profiles after any center/kinematic change.

## Decision: staged architecture

**Phase 1 — Offline calibration and post-process inspection (MVP).**
- Home and register machine, park pen, and stabilize bed at a known theta pose.
- Calibrate camera/lens and CoreXY geometry with an **independent dimensionally known target**.
- Characterize rotary center, angular behavior and direction dependence with independent optical references; preserve commanded vs observed poses.
- After drawing, park pen, place theta at a known stable angle, scan the completed drawing in overlapping tiles, and compare to SVG in a common paper frame.
- Report missing/extra strokes, line-center deviation, spatial trends, and uncertainty; **no automatic redrawing**.

**Phase 2 — Print-to-print learning and compensation.**
- After each completed print, estimate measured residuals in a stable paper coordinate frame, distinguishing systematic patterns from measurement noise and one-off artifacts.
- Aggregate repeatable errors across multiple prints, positions, angles, and drawing directions; retain raw evidence and confidence intervals.
- Fit a **candidate** update to the existing converter compensation model, with separate parameters for XY origin, theta ratio/phase, and spatial error where identifiable.
- Run an independent validation print (or reserved held-out geometry) and compare against the current profile before promotion; reject changes that worsen worst-case error or are not repeatable.
- Version and retain every accepted profile, provide one-click rollback, and never change machine/controller homing constants implicitly.

**Phase 3 — Optional automated calibration management.**
- Automate the candidate/validation/report/approval workflow, not real-time correction. Do not move the pen to repair the just-finished artwork.
- Prefer explicit approval until multiple cycles demonstrate that profile promotion is reliable.

## Coordinate frames and measurement model

Define and version transforms among:
- **SVG/paper frame** `P`: expected immutable design geometry.
- **Machine frame** `M`: physical XY axes and calibrated mechanical rotation center.
- **Rotating bed frame** `B`: actual theta orientation and paper-to-bed placement.
- **Camera gantry frame** `C`: CoreXY carriage coordinates.
- **Image frame** `I`: pixels after camera intrinsics/distortion correction.

Nominal planar mapping: `p_M = c_M + R(theta_actual) * p_P` (with paper-to-bed placement applied separately). Camera pixels map to the paper through calibrated camera intrinsics, extrinsics, gantry pose, bed pose, and paper-plane geometry.

**Camera optical center need not coincide with the carriage center.** Calibrate its fixed XY offset, in-plane yaw, scale, lens distortion and any camera tilt. A rigid off-center mount is acceptable; flex, play, drift and uncalibrated perspective are not.

Distinguish:
- Constant origin offset: causes angle-dependent **periodic** displacement (not unbounded growth).
- Incorrect theta ratio, missed steps or slip: can cause **accumulating** angular phase error.
- Backlash/hysteresis: depends on approach direction.
- Bed wobble/tilt and XY/CoreXY skew: may appear as spatially varying error.

Do not infer actual theta solely from commanded A, nor infer absolute angular accuracy from one perimeter marker orbit without independent constraints.

## Fiducial policy — avoid measuring away the defects

1. **Independent calibration references:** precisely spaced targets mounted on a stable calibration surface; use to calibrate camera optics, camera gantry and true rotary center.
2. **Artwork fiducials:** generated by converter; use to identify tiles, associate scanned regions with expected artwork, and assess relative alignment.
3. Registration must not freely warp every tile to fit expected strokes. That would conceal machine geometry errors. Keep a locked global transform for absolute error assessment, and report separately any local-registration residual.
4. Narrow field of view may show only one fiducial at a time: associate observations via calibrated camera-gantry pose, tile overlap and target IDs. Never assume three marks appear in one image.
5. For a final scan, the **history of theta angles during drawing is not needed for basic shape comparison**, but logged theta commands/actual-pose estimates are useful for attributing defects and designing corrections.

## Proposed code modules (names provisional)

- `camera_inspection/capture.py`: camera interface, timestamped images, focus/exposure controls and image metadata.
- `camera_inspection/frames.py`: explicit coordinate-frame transforms and versioned calibration parameters.
- `camera_inspection/optics.py`: intrinsic calibration, distortion and pixel-to-mm uncertainty.
- `camera_inspection/gantry.py`: camera CoreXY motion abstraction, home, positioning, settle, and limits.
- `camera_inspection/rotary.py`: theta characterization, orbit fit, direction/turn tests, confidence bounds.
- `camera_inspection/fiducials.py`: fiducial detection, identification and reference-class distinction.
- `camera_inspection/scan.py`: coverage planner, overlap, tile acquisition, global registration and mosaic.
- `camera_inspection/expected.py`: load SVG/plot plan, canonical expected centerlines, and completed-stroke manifest.
- `camera_inspection/compare.py`: observed stroke extraction, matched deviations, missing/extra ink, confidence.
- `camera_inspection/report.py`: overlays, numerical error maps, calibration provenance and export.
- `camera_inspection/supervisor.py`: state machine, interlocks, checkpoint execution and cancellation.

Module layout may be adapted to existing `software/` packaging after inspecting integration points.

## Data contracts

Persist a versioned run manifest with:
- Input SVG hash, G-code hash, converter/planner settings and active bed-compensation fingerprint.
- Machine homing/registration results, calibrated true center, theta index/ratio and measured direction effects.
- Camera model/lens/focus, intrinsic/extrinsic calibration version, camera gantry calibration and uncertainty.
- Each tile's commanded and observed/acknowledged camera pose, bed theta, timestamps, image filename and exposure.
- Fiducial detections and their classification (independent reference vs printed artwork).
- Expected stroke IDs and execution-completion status for checkpoint inspection.
- Global alignment, raw residuals, threshold policy and inspection decision; preserve original images.

Use **paper coordinates** as the canonical expected geometry; do not reconstruct expectations by treating machine-frame X/Y G-code as paper-frame coordinates.

## Milestones and acceptance gates

1. **Camera bench test:** stable imaging and focus at working height; calibrate optics and repeat capture on an independent scale target.
2. **Camera gantry test:** quantify XY scale, skew, backlash, repeatability and camera mounting offset across the full scan area; test return-to-target after long moves.
3. **Rotary characterization:** scan independently mounted target(s) over >=1 revolution, then multiple turns, both directions; separate periodic center effects from cumulative theta drift. Repeat from fresh homing cycles. Keep held-out angles.
4. **Static scan MVP:** scan a stationary known target in overlapping tiles; compare known distances without allowing per-tile fitting to erase errors.
5. **Completed-artwork MVP:** scan finished plot at a fixed known theta; compare to original SVG, generate deviation heatmap and missing/extra-stroke report.
6. **Validation:** compare measured offsets against independent physical measurements, repeated scans and held-out targets. Set acceptance thresholds only after measurement repeatability is established.
7. **Print-to-print learning:** aggregate residuals across prints, fit candidate compensation profiles, quantify repeatability and preserve uncertainty.
8. **Profile validation and promotion:** print independent validation geometry, compare corrected vs uncorrected accuracy, then approve or reject with rollback.

**Go/no-go rules:** no claim of subpixel mechanical accuracy from pixel pitch alone; no compensation based on nonrepeatable residuals; no change to P100, theta ratio, or active compensation profile without separate validation and rollback.

## Integration questions to resolve before implementation

- Final camera connection: Raspberry Pi 4 CSI/USB vs ESP32-P4 Ethernet endpoint, and achievable full-resolution capture/transport rate.
- Lens and sensor mechanical compatibility, FOV, distortion, focus at ~300 mm, illumination and exposure stability.
- Camera gantry controller, axis mapping and how actual motion completion/position is acknowledged.
- Bed theta feedback availability: commanded A versus independent measured theta; when bed can be held stationary.
- Existing SVG-to-G-code stroke IDs, output metadata, fiducial definitions and how inspection manifests will be generated.
- Mechanical access to independently referenced calibration targets and whether artwork paper can slip relative to bed.
- Safety interlocks, camera/pen clearance and user interface for scan, calibration and review.

## First coding slice

Start with **offline, read-only inspection**: load expected SVG centerlines, camera calibration and a set of static sample images with known fiducials; compute a locked global image-to-paper transform and export a deviation overlay + CSV. Add synthetic unit tests for known translations, rotations, camera offset, center eccentricity, theta-ratio drift, missing strokes, and false-registration masking. Do not connect real-time correction or overwrite the current converter compensation pipeline in this slice. The next slice is a versioned print-to-print calibration learner with held-out validation.

Related: [Optical calibration plan](calibration.md), [magnetic registration](../docs/decisions/ADR-003-controller-owned-magnetic-registration.md), [theta drift diagnosis](../docs/changes/windows-software/2026/2026-09-30-theta-drift-diagnosis-and-calibration-plot.md), [dense rotation-center calibration](../docs/changes/windows-software/2026/2026-10-23-dense-rotation-center-calibration.md).

## Architectural decision (2026-11-12): post-print learning only

The intended operational loop is **draw → inspect finished print → compare with expected SVG → estimate systematic error → propose updated compensation → validate → use on subsequent prints**. This is not a real-time correction project. Each print supplies additional evidence; improvement is a measured goal, **not a guarantee of monotonic improvement**. Distinguish systematic errors from stochastic noise, paper slip, ink spread and scan-registration artifacts. Preserve the original SVG and every applied compensation profile for reproducibility. A final scan must not automatically move the pen or silently alter the current profile.

## Live camera streaming and Pi HMI (required)

The inspection system **must continuously deliver a camera preview to the Raspberry Pi 4**, which drives the **official Raspberry Pi Touch Display 2**. This requirement is independent of the decision to perform geometric analysis and compensation **after** each completed print.

Proposed data path: **CoreXY-mounted camera → camera endpoint (ESP32-P4 Ethernet if verified) → Ethernet/PoE switch → Raspberry Pi 4 → directly attached Touch Display 2**. The Touch Display 2 is not an Ethernet video endpoint; the Pi renders its UI locally. The Pi may receive power via a compatible PoE solution, subject to actual power budget and hardware verification. The camera endpoint's sensor/driver, streaming protocol, throughput and ESP32-P4 compatibility remain engineering validation items, not settled assumptions.

Functional requirements:
- Display a responsive **live camera preview** on the Pi's Touch Display 2 during plotting, camera positioning and post-print scanning; show connection/stream health and a recoverable error state.
- Provide a **full-resolution still-capture path** for metrology with associated timestamp, camera pose, bed angle, exposure and calibration metadata. Preview compression/resizing must never silently become the measurement source.
- Preserve HMI machine controls (play/pause/stop/feed override), scan start/cancel, scan progress, inspection overlay and before/after comparisons.
- Isolate streaming/display failures from the GRBL-HAL safety and motion-control path. A video disconnect must not silently command motion.
- Avoid blocking motion control or inspection acquisition with video rendering. Design separate bounded queues/consumers for preview and still capture; define dropped-frame behavior.
- Measure actual preview frame rate, latency, resolution, Pi CPU load, network bandwidth and full-resolution capture time on target hardware before committing to a streaming transport or UI framework.
- Keep camera-stream service, inspection engine and HMI as separable components so inspection may continue collecting evidence without an open preview screen.

This is a **live-view requirement, not a real-time drawing-correction requirement**. The system may show what the camera sees while printing, but only post-print scans update proposed compensation for later prints.
