# Actual ink vs projected G-code inspection

## Goal
Visually compare completed physical pen strokes against the expected toolpath and report discrepancies in **millimeters**, not only pixels.

## Proposed layers
- Camera image: unmodified image of ink on paper.
- Projected path: reference segments that have **already executed**.
- Detected ink: extracted stroke centerlines/masks.
- Deviation heatmap: signed/unsigned offsets, missing segments, excess marks and uncertain regions.
- Inspection status: metrics and confidence; avoid declaring PASS without validated thresholds.

Colors are UI conventions, not measurements. Suggested: green expected path, cyan detected line, red deviations, yellow unverified/incomplete regions.

## Candidate pipeline — completed-print scan
1. Finish the full print; preserve the G-code and expected pen-down geometry, θ transformations and calibration profile used for that job.
2. Hold the rotary bed at a known angle; traverse the completed artwork in overlapping CoreZB camera tiles. At each stationary capture, record camera pose, bed angle, exposure settings and image scale.
3. **Mandatory post-print first scans:** locate bed fiducials, then paper fiducials, and validate separate bed-to-machine and paper-to-bed transforms. Undistort images and register camera observations to both frames before artwork matching. Pre-print scanning is optional; paper movement during printing cannot be inferred from a post-print scan alone.
4. Segment dark ink against background; remove noise and optionally skeletonize/fit line centerlines.
5. On Windows, associate ink strokes with expected executed segments using the converter's stroke-to-G-code manifest and fiducial-registered expected geometry; label indistinguishable overlapping strokes ambiguous. Exclude future G-code from missing-line detection.
6. Compute nearest-centerline deviation, mean/RMS/max, coverage/missing length, and confidence.
7. Render projected/actual/difference layers and return results with frame timestamp and pose.

## Precision considerations
- Pixel size at paper plane and lens distortion establish a measurement floor.
- Pen stroke width, illumination, focus, blur, paper texture and shadows affect centerline estimates.
- Pose error, belt compliance, carriage skew and rotary bed errors can dominate pixel-level resolution.
- Inspecting regions near image edges may be less reliable than the center.
- Revisit a known reference periodically to detect drift.
- Store raw frames and uncorrected measurements for audit and algorithm regression.

## ESP32-P4 partition
Plausible on-device targets: acquisition, grayscale/threshold segmentation, ROI extraction, centerline fitting, simple geometry comparison, compact overlay/metrics. Full-resolution, high-frame-rate registration and complex CV may require the Windows host. **Benchmark before promising throughput, latency or accuracy.**

## Initial acceptance tests
- Repeated stationary captures of the same stroke.
- Known intentionally offset lines and missing segments.
- Different ink colors, widths, and lighting.
- Different camera locations and θ angles.
- Compare reported error against independent physical measurements.

## Stroke provenance and distributed workflow

The converter should emit a job manifest mapping stable stroke IDs to source SVG geometry, executed G-code block ranges, full commanded XYθ trajectories, expected paper-frame ink paths, converter version and pinned calibration profile/hash. The Pi stores it alongside nominal/corrected G-code and pose-tagged images. Windows performs authoritative correspondence and residual fitting after receiving the inspection dataset; the Pi manages acquisition, local preview and approved-profile synchronization.

After printing, bed fiducials must be scanned before paper fiducials; neither can substitute for the other. Routine pre-print fiducial scanning is not required. Registration quality gates must precede any automatic compensation proposal. A single stationary-theta scan can contain evidence from strokes drawn at many theta angles **if** their execution trajectories are retained, but does not by itself guarantee a uniquely identifiable theta-error model.

## Registration semantics

The bed-first post-print scan supplies the physical reference for the entire inspection. The subsequent paper scan measures sheet pose relative to that bed, and the artwork scan measures ink relative to the registered sheet. Use the two transforms separately when attributing errors: a global paper offset must not automatically become a permanent bed/rotary compensation update. The stroke manifest and executed XYθ trajectories provide correspondence candidates; ambiguous overlaps and unobservable timing remain flagged rather than forced into calibration.

## Temporary imagery and automatic cleanup

Full-resolution JPEG tiles are **intermediate data**, not permanent calibration history. Keep them on Pi microSD until Windows has synchronized and verified them, extracted fiducial/stroke geometry, completed calibration evaluation, and the Pi has durably committed the outcome and acknowledged completion. Then automatically delete JPEGs and retain compact geometric measurements, confidence, executed-trajectory correspondence, model/validation metadata and hashes. If the laptop is offline or transfer/analysis fails, preserve recoverable JPEGs and resume on reconnect; a user-confirmed Cancel Sync & Revert can close the pending transaction and trigger automatic cleanup after the Pi commits the cancellation. Do not erase files needed by an unresolved job. Approved calibration geometry is retained for current and two previous approved generations only; unchanged evaluations do not consume a generation.
