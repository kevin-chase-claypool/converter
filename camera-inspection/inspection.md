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
3. Undistort image, correct paper-plane perspective, and register to machine/paper coordinates.
4. Segment dark ink against background; remove noise and optionally skeletonize/fit line centerlines.
5. Associate ink strokes with expected executed segments. Exclude future G-code from missing-line detection.
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
