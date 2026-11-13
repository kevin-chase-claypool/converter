# Optical calibration, rotary characterization and compensation

## Permanent coded fiducial ring — selected concept
- Bed: 18-inch diameter (457.2 mm); central printable area: 14-inch diameter (355.6 mm); available outer annulus: 2 inches (50.8 mm) radially. Keep all permanent bed markers outside the printable area and sufficiently close to the bed rim to leave room for painter's tape securing the paper.
- Provisional layout: **20 unique AprilTag-family IDs** distributed approximately evenly around the rim (nominally 18° apart), approximately **12 mm square** with centers near **218 mm radius**. Exact dimensions, border/quiet zone, edge clearance, travel and detectability must be verified using the real camera, optics, lighting and mounting method before manufacture. IDs are unique; no custom hand-designed codes.
- The magnetic **Theta index sensor is directly east (+X) of bed center**. Homing the index defines nominal θ=0°; the east-side optical station is a CoreZB camera pose above the marker ring. A designated reference tag B00 may be registered at this station at θ=0°, but do not assume its alignment from the sensor's location alone.
- **Precision placement is not required**: markers need only be fixed, individually recognizable, visible, and approximately spaced for coverage. Commissioning measures and records each marker's actual bed-frame coordinates and orientation **relative to the homed Theta index**; never treat nominal 18° spacing as measured ground truth.
- The registered map is a repeatable relative baseline, **not an independently calibrated absolute angular standard**. Avoid claiming it can uniquely separate Theta angle error from commissioning motion error, camera pose, or fiducial geometry. Inspect actual artwork as independent outcome evidence, with separate paper registration, and validate candidate corrections before promotion.
- Keep bed tags mechanically stable and out of tape/pen contact. Paper fiducials are a separate reference frame; never use the bed ring as a substitute for paper registration.

## Commissioning and rolling routine
1. Home Theta at the east-side magnetic index (nominal θ=0°); home XY and CoreZB. Check home and camera-station repeatability.
2. Calibrate camera intrinsics, image scale, distortion, and camera-to-machine pose with appropriate known geometry.
3. Move CoreZB to the fixed **east optical station** above the outer ring. Observe the reference tag at θ=0° and establish its ID and measured pose.
4. Index Theta to bring each of the ~20 uniquely coded tags beneath the stationary camera; capture each tag ID and observed pose. The commanded steps are nominal guides, not assumed marker coordinates. Register the **actual** relative fiducial map, using additional camera poses/multi-angle observations where needed to constrain geometry.
5. Repeat selected observations after homing, across multiple revolutions and from both directions to characterize return-to-index repeatability, eccentricity, backlash/hysteresis and uncertainty. Do not interpret a single marker offset as proof of angular error.
6. During each post-print cycle, after confirmed pen park, home/index Theta and inspect a suitable subset of ring markers using Theta motion at the east station; increase coverage when repeatability or confidence is poor. This is a **post-print** check, not a mandatory pre-print scan.
7. Register paper fiducials and scan the completed artwork with recorded Theta/camera poses; Windows matches observed ink against executed stroke trajectories.
8. Windows fits and independently validates a candidate compensation update. Pi approves/retains the existing profile per the sync gate and automatic three-generation retention policy. Never promote based solely on a ring residual.

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

## Interpretation of bed versus paper references

The **purpose of bed fiducials** is to anchor the mechanical bed frame independently of the artwork. The **purpose of paper fiducials** is to register the sheet against that anchored bed frame. Together, after printing, they allow observed ink to be compared in a consistent physical coordinate system with expected executed strokes. This separates global bed registration from paper placement in the model; it does **not** guarantee that every residual has a uniquely identifiable mechanical cause or establish when any sheet movement occurred. Do not require a routine pre-print scan merely to use these references.

## Automatic rolling retention policy (required)

Keep only **three approved calibration generations** on the Pi: current `N`, previous `N-1`, and two back `N-2`. Each generation retains its approved correction profile, associated compact extracted geometry, validation metrics, provenance, and hashes. A drawing that produces no approved model change does **not** advance the generation counter. A failed or canceled candidate is not an approved generation.

After a newly approved generation and its records have been durably committed, atomically update the active-profile pointer, verify the retained three-generation set, then garbage-collect `N-3` and older generations **only when unreferenced by active/unresolved jobs**. Never delete the last known-good rollback target during a partially committed promotion. Recovery after reboot must be idempotent.

Original JPEGs are **temporary**: retain them while scanning, synchronizing, analyzing, validating, or awaiting a final Pi-side commit acknowledgment. After Windows returns verified geometric measurements and the Pi commits the resolved calibration outcome, automatically delete the JPEGs for successful jobs. On failures, retain required recovery images until retry succeeds or an explicit Cancel Sync & Revert resolves the transaction; after cancellation, clean up temporary images automatically once the cancellation is durably acknowledged. Preserve the small outcome/error record, not indefinite image archives. No routine manual cleanup is required.
