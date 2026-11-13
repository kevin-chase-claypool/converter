# Optical calibration, rotary characterization and compensation

## Proposed physical references
The bed already has an embedded center magnet and a perimeter index magnet. Proposed process: use those locations to make **visible black circular targets** on a rigid rotating calibration surface, then remove any temporary placement magnets. The optical circles should be mechanically stable and their centers detected by circle fitting.

**Caution:** The center magnet's location is a nominal reference, not proof of the true mechanical rotation axis. Likewise, the perimeter index gives an angular reference but does not by itself prove angular accuracy.

## Calibration routine
1. Home plotter XYθ and camera CoreZB; record repeatability over multiple homing cycles.
2. Calibrate camera intrinsics/lens distortion and camera-to-gantry mounting offset with a known physical scale.
3. Observe the nominal center target; establish camera-to-machine alignment.
4. Observe the perimeter target at many commanded θ angles over 360°, with stationary exposures.
5. Fit the perimeter target trajectory to estimate actual center of rotation and orbit radius.
6. Repeat clockwise and counterclockwise; compare directional repeatability/hysteresis.
7. Repeat across multiple revolutions, approach speeds and temperature conditions.
8. Measure and validate corrections on **held-out** angles and separate calibration artwork.

## Errors to characterize
- XY offset between nominal origin and fitted rotary center.
- Repeatable radial/angular deviation, gear/belt periodicity, and backlash.
- Nonrepeatable motion from belt slip, flex, loose fasteners or paper movement.
- Camera gantry scale, skew, repeatability and lens/perspective errors.
- Bed tilt/wobble (a planar single-camera observation can confound tilt with apparent XY displacement).

## Identifiability limits
A single perimeter point's trajectory provides excellent center/orbit information, but **cannot uniquely isolate true angular positioning error** from camera calibration, target eccentricity, pose errors or changing tilt without additional references/constraints. For absolute angular accuracy, use an independently calibrated angular reference or additional targets/methods. Use multiple radii/targets where needed.

## Compensation strategy
- First repair nonrepeatable mechanical faults.
- Apply verified XY center offset and camera calibration.
- Build a direction-aware θ correction lookup only if angular error is independently measurable and repeatable.
- Keep correction models versioned, with raw observations, uncertainty and test results.
- Select exactly one compensation layer (converter, supervisory planner, or controller) to avoid double correction.
- Always compare corrected vs uncorrected results on independent validation data.

## Illustrative scale
At radius 200 mm, 0.15° angular error corresponds to approximately 0.524 mm tangential displacement (`r * Δθ_rad`). This is an example, **not** a measured plotter error.

## Required dual fiducial frames (post-print inspection)

**Bed fiducials (B):** Permanent, mechanically stable markers referenced to the rotating bed. They define bed registration relative to the stationary machine frame M and support multi-angle rotary-center and repeatability characterization. The embedded center/index magnets are initial references, **not** proof of physical center or angular accuracy.

**Paper fiducials (P):** Separate marks physically associated with each sheet, defining paper-to-bed placement `T_BP`. Their location must be known relative to the artwork and they must remain visible and undisturbed. Do not infer paper alignment from bed markers alone.

**Required scan:** After printing, register B then P before any stroke comparison; hold theta and scan artwork in overlapping tiles. Pre-print scans are optional diagnostics only. Without a pre-print reference, post-print images cannot establish whether paper shifted during the job. A changed paper pose is not automatically a machine correction.

**Transform:** `p_M = T_MB(theta) * T_BP * p_P`. Camera-to-machine mapping, lens distortion, exposure pose and uncertainty must also be calibrated. Multiple non-collinear references or equivalent constrained geometry are needed to determine the desired 2D transform; marker geometry and visibility are validation gates.

**Versioning:** Persist bed/rotary model versions separately from per-job paper registration records, with raw measurements, confidence, time, camera calibration and machine configuration. Windows generates compensation candidates from matched ink/G-code residuals; Pi stores approved profiles and historical records. Candidate updates must be validated on independent patterns before promotion.

**Identifiability:** Fiducials remove global registration ambiguity, but do not necessarily identify which of two coincident strokes deposited ink or uniquely separate angular error from other physical effects. Preserve ambiguous observations rather than training on invented correspondences.
