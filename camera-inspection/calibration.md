# Optical calibration, rotary characterization and compensation

## Permanent coded fiducial ring — selected concept
- Bed: 18-inch diameter (457.2 mm); central printable area: 14-inch diameter (355.6 mm); available outer annulus: 2 inches (50.8 mm) radially. Keep all permanent bed markers outside the printable area and sufficiently close to the bed rim to leave room for painter's tape securing the paper.
- Provisional layout: **20 unique AprilTag-family IDs** distributed approximately evenly around the rim (nominally 18° apart), approximately **12 mm square** with centers near **218 mm radius**. Exact dimensions, border/quiet zone, edge clearance, travel and detectability must be verified using the real camera, optics, lighting and mounting method before manufacture. IDs are unique; no custom hand-designed codes.
- The **historical Theta index location is directly east (+X) of bed center**, but a Hall-effect index/center sensor must **not** be assumed available to the camera inspection subsystem. Use the calibrated CoreZB camera and outer fiducials to establish optical center and angular zero. Define B00 aligned to the east optical station as θ=0° after calibration; distinguish this optical datum from any controller magnetic home or encoder reference that actually exists.
- **Precision placement is not required**: markers need only be fixed, individually recognizable, visible, and approximately spaced for coverage. Commissioning measures and records each marker's actual bed-frame coordinates and orientation **relative to the optically established Theta-zero reference**; never treat nominal 18° spacing as measured ground truth.
- The registered map is a repeatable relative baseline, **not an independently calibrated absolute angular standard**. Avoid claiming it can uniquely separate Theta angle error from commissioning motion error, camera pose, or fiducial geometry. Inspect actual artwork as outcome evidence; dedicated paper fiducials are optional, not mandatory. Without independent paper references, global displacement and paper movement can be ambiguous. Validate candidate corrections before promotion.
- Keep bed tags mechanically stable and out of tape/pen contact. Paper fiducials are a separate reference frame; never use the bed ring as a substitute for paper registration.

## Commissioning and rolling routine — optical, drawing remains installed
1. Home CoreZB and establish camera-to-machine geometry; no center or Theta Hall sensor is presumed available for this inspection workflow.
2. **Find bed center first**: rotate Theta while observing one or more outer-ring tags at known camera poses; fit the observed orbits to estimate the physical rotation center in the calibrated camera/gantry frame. Use a coarse center estimate for safe scanning, refine with multi-angle observations, and report uncertainty.
3. **Establish Theta zero second**: search for unique B00, rotate it to its calibrated east-side optical datum, and set/register optical θ=0°. This is a repeatable optical datum, not proof of absolute angle accuracy. Coordinate controller offsets carefully so G-code angle conventions remain consistent.
4. Index through the approximately 20 unique tags and register their **actual** positions and orientations; exact mounting angles are unnecessary. Check repeated approaches, clockwise/counterclockwise hysteresis, camera-station repeatability and multiple revolutions.
5. After every completed print and confirmed pen park, repeat center verification then optical θ=0° registration and selected tag checks. **Leave the completed drawing and painter's tape in place**: all required bed tags are outside the 14-inch printable region, in the uncovered outer annulus.
6. Scan the completed artwork with recorded Theta and CoreZB poses. **Paper fiducials are optional**, not required; match identifiable ink geometry to the executed stroke manifest in bed-referenced coordinates. Do not freely align away global translation/rotation errors; flag ambiguous paper shifts.
7. Windows fits and independently validates any candidate correction. Pi commits the approved outcome, preserves the three-generation retention rule, and releases the next-submission gate. Do not promote from ring offsets alone.

**Visibility prerequisite:** Tape, paper, clamps and other fixtures must not obscure the outer fiducial ring. CoreZB must reach the east inspection station and see enough tags at the chosen working distance. If the ring is obscured, fail safely rather than infer center or zero.

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

**Optional paper fiducials (P):** Dedicated paper markers may help independently estimate sheet pose `T_BP`, but are **not mandatory** for routine rolling calibration. Without them, sheet pose may be inferred only where artwork correspondence is sufficiently distinctive; some global offsets or shifts remain unidentifiable.

**Required scan:** After printing, optically register bed center and Theta zero, check B, then scan artwork in overlapping tiles. Scan P only if optional paper markers are present. Pre-print scans are optional diagnostics only. Without a pre-print reference, post-print images cannot establish whether paper shifted during the job. A changed paper pose is not automatically a machine correction.

**Transform (when paper pose is known):** `p_M = T_MB(theta) * T_BP * p_P`. Camera-to-machine mapping, lens distortion, exposure pose and uncertainty must also be calibrated. Multiple non-collinear references or equivalent constrained geometry are needed to determine the desired 2D transform; marker geometry and visibility are validation gates.

**Versioning:** Persist bed/rotary model versions separately from per-job paper registration records, with raw measurements, confidence, time, camera calibration and machine configuration. Windows generates compensation candidates from matched ink/G-code residuals; Pi stores approved profiles and historical records. Candidate updates must be validated on independent patterns before promotion.

**Identifiability:** Fiducials remove global registration ambiguity, but do not necessarily identify which of two coincident strokes deposited ink or uniquely separate angular error from other physical effects. Preserve ambiguous observations rather than training on invented correspondences.

## Interpretation of bed versus paper references

The **purpose of bed fiducials** is to anchor the mechanical bed frame independently of the artwork. The **purpose of paper fiducials** is to register the sheet against that anchored bed frame. When available, together they allow observed ink to be compared in a consistent physical coordinate system with expected executed strokes. This separates global bed registration from paper placement in the model; it does **not** guarantee that every residual has a uniquely identifiable mechanical cause or establish when any sheet movement occurred. Do not require a routine pre-print scan merely to use these references.

## Automatic rolling retention policy (required)

Keep only **three approved calibration generations** on the Pi: current `N`, previous `N-1`, and two back `N-2`. Each generation retains its approved correction profile, associated compact extracted geometry, validation metrics, provenance, and hashes. A drawing that produces no approved model change does **not** advance the generation counter. A failed or canceled candidate is not an approved generation.

After a newly approved generation and its records have been durably committed, atomically update the active-profile pointer, verify the retained three-generation set, then garbage-collect `N-3` and older generations **only when unreferenced by active/unresolved jobs**. Never delete the last known-good rollback target during a partially committed promotion. Recovery after reboot must be idempotent.

Original JPEGs are **temporary**: retain them while scanning, synchronizing, analyzing, validating, or awaiting a final Pi-side commit acknowledgment. After Windows returns verified geometric measurements and the Pi commits the resolved calibration outcome, automatically delete the JPEGs for successful jobs. On failures, retain required recovery images until retry succeeds or an explicit Cancel Sync & Revert resolves the transaction; after cancellation, clean up temporary images automatically once the cancellation is durably acknowledged. Preserve the small outcome/error record, not indefinite image archives. No routine manual cleanup is required.
