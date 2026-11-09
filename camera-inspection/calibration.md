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
