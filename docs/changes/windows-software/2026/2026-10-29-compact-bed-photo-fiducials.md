---
id: WSW-20261029-004
date: 2026-10-29
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - tools/measure_bed_error_photo.py
  - software/tests/test_bed_photo_measurement.py
tags:
  - bed-calibration
  - photo-measurement
  - fiducial
  - image-scale
related:
  - WSW-20261029-002
  - WSW-20261029-003
---

# Recover dense measurements from compact calibration photos

## Summary

The bed-photo extractor now accepts the smaller fiducial components produced
by a 1684 x 2236 overhead photo. Previously, its fixed 40 px lower dimension
and 100-pixel area floor rejected every fiducial in that capture even though
the printed V marks were present and usable. Fiducial selection now scores the
physical V arm pattern, and dense station coordinates are refined directly
from each printed L template rather than from threshold-dependent connected
components.

## Reason

The supplied v3 sheet photo is about half the linear size of the prior
3072 x 4080 calibration images. Its F1 fiducial footprint is approximately
27 x 37 px with 103 ink pixels. The old filter required at least 40 px in one
dimension and 100 pixels, so seeded fiducial selection stopped before any
station geometry could be evaluated.

After relaxing the filter, proximity-only ranking selected a nearby station
mark instead of the bottom-left fiducial. That single wrong vertex distorted
the fitted sheet and produced apparent 10 mm station errors. Connected
component corners also changed with threshold, making nominally identical
marks move by millimetres.

## Implementation

The common fiducial component predicate now accepts:

- 80 to 1,200 ink pixels;
- 32 to 120 px maximum dimension.

Seeded fiducial lookup uses the same predicate as the full-sheet path, avoiding
two different definitions of a plausible fiducial. Candidate ranking combines
the observed triangle side lengths with the known 4 mm radial arm, 7 mm
tangent arm, and expected image scale. The quadrant and largest-component
safeguards remain unchanged.

After the four fiducials determine the projective sheet transform, each of the
819 station Ls is refined independently against its expected two-arm template
within `+/-5 px` of the common station shift. This retains A0/control and
per-angle differences while preventing a connected-component threshold from
changing the measured coordinate.

## Verification

- A new red-first regression used a 27 x 37 px, 103-pixel fiducial. It was
  rejected before the change and accepted afterward.
- The existing paper-edge and station-mark rejection test still passes.
- The synthetic v3 extraction test passes at 1750 x 1750 with 4 fiducials and
  all 819 station marks.
- A new shape-score regression distinguishes the long fiducial arm pair from
  a station-like L.
- The supplied 1684 x 2236 photo resolves the correct four shared vertices and
  all 819 station Ls.
- Thresholds 20, 55, 70, and 80 produce identical measured station coordinate
  files.
- The corrected analysis no longer exceeds the 5 mm correction bound, but it
  still fails the profile gates: A0 spatial is `0.594 mm` RMS / `1.705 mm`
  maximum, A0 control is `0.297 / 0.655 mm`, and leave-one-out is
  `0.676 / 3.689 mm` with `42.1 %` improvement.
- All `65` focused bed tests pass.
- The full converter suite passes all `575` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- Upscaling the whole image was rejected because it adds runtime and does not
  create missing detail; the fiducials are large enough to identify at native
  resolution.
- Lowering only the dimension floor was insufficient because the same compact
  image reduces fiducial area below the previous 100-pixel floor.
- Removing the size filter entirely would admit station groups and label
  components as fiducial candidates.
- Ranking only by seed distance selected the bottom-left station mark because
  it happened to be closer than the actual fiducial; arm-shape scoring fixed
  that specific misregistration.
- Component corners remained threshold-sensitive even after registration.
  Per-mark raw-image template matching removed that dependency.

## Risks and follow-up

Compact photos leave fewer pixels across each 3 mm station arm. Threshold
stability is now demonstrated, but the sheet still fails the calibration
accuracy gates. A successful fiducial match does not itself validate the
field or produce an accepted profile.

The first compact v3 sheet remains unaccepted because its A0 and
leave-one-out errors exceed the gates. It also contains one visible pen-up
drag; see the 2026-10-29 M-12/T-01H lab note.

## Files

- `tools/measure_bed_error_photo.py`: compact fiducial bounds and shared
  predicate, V-shape ranking, and per-mark dense template refinement.
- `software/tests/test_bed_photo_measurement.py`: compact-component,
  fiducial-shape, and repeatable dense extraction regressions.
- `software/README.md`: documented compact-photo behavior.
