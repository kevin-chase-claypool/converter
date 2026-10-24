---
id: WSW-20261024-003
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/measure_bed_error_photo.py
  - software/tests/test_bed_photo_measurement.py
tags:
  - bed
  - calibration
  - photo
  - fiducial
  - orientation
  - matching
related:
  - WSW-20261024-001
  - WSW-20261023-004
---

# Make bed-calibration photo matching orientation-independent

## Summary

The full-field photo matcher now handles a rotated calibration sheet, a small
number of extra ink components, and the actual shared vertex of each V-shaped
fiducial. It no longer requires the photograph to match one fixed image
orientation or an exact 185-mark component count.

## Reason

The first eight-angle photo was rotated 90 degrees relative to the prior image
and contained 336 L-shaped components: the required 333 station marks plus
three specks. The old matcher rejected the component count. After allowing
extras, its fixed image-corner assumptions assigned the wrong ends of the
fiducial and station arms, producing 18-84 px station errors and unusable
coordinates.

## Implementation

- Evaluate all non-mirrored quarter-turn assignments of the four fiducials and
  select the one with the lowest station-lattice assignment score.
- Allow up to 12 extra medium-size components while still requiring all
  expected station marks and exactly four fiducials. Filter the larger
  fiducial group by both ink-pixel count and bounding-box dimension, and use
  the largest qualifying component in each quadrant so paper-edge fragments do
  not replace a fiducial.
- Assign components by centroid using a homography-aware expected centroid.
- Locate the station L corner in sheet coordinates by fitting the centres of
  its horizontal and vertical arms, independent of image rotation.
- Locate each V fiducial by selecting the three major convex-hull vertices and
  refining the vertex nearest the predicted pose.
- Raise the default assignment safety bound from 8 to 13 px for the denser
  333-mark sheet; the 10 mm lane spacing still provides a wide separation
  between candidate marks.
- Record fiducial order and orientation score in the photo diagnostic JSON.

## Verification

- The supplied `cal.jpg` now resolves four fiducials, 336 L candidates, and 109
  label fragments.
- All 333 station marks assign with `4.262 px` minimum, `7.565 px` median, and
  `12.365 px` maximum assignment error.
- The overlay places measured points on the shared L corners rather than the
  far ends of the arms.
- The measurement CSV contains all 333 station rows and passes the analyzer's
  completeness checks.
- `py -m unittest discover -s software\tests -p "test_bed_*.py" -q` passes all
  36 bed/photo tests.
- The compensated verification photo resolves four fiducials, 334 station-L
  candidates, and 74 label glyphs. All 333 station marks assign with
  `0.865 / 5.961 / 11.891 px` minimum / median / maximum error.
- Threshold/blur sweeps at `10/10`, `15/15`, and `20/18` all assign all 333
  stations and report the same failed compensated verification. Run-to-run
  extraction is not the reason the profile failed.
- The full converter suite passes 498 tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Rotating the source image externally was rejected because the matcher should
  accept the operator's original photograph.
- Raising the assignment threshold alone was rejected; the dominant errors
  came from fixed orientation and corner assumptions.
- Selecting mark endpoints by bounding-box position was rejected because image
  rotation changes which bbox corner is the shared vertex.
- Accepting every component wider than 40 px was rejected after the
  verification photo produced six large components, including multi-thousand
  pixel paper-edge fragments around the four real fiducials.

## Risks and follow-up

- A sheet that moves during the multi-pass print remains invalid even when all
  components are found.
- Review the generated overlay when assignment approaches the 13 px limit.
- The expanded calibration failed its independent compensated verification and
  is not the default. The matcher change only establishes that the failure is
  in the compensation field or machine repeatability, not marker assignment.

## Files

- `tools/measure_bed_error_photo.py`: orientation search, fiducial filtering,
  tolerant component assignment, and rotation-independent corner extraction.
- `software/tests/test_bed_photo_measurement.py`: V-vertex, L-vertex, mark-count,
  and homography regressions.
