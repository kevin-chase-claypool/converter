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

# Accept fiducials in compact calibration photos

## Summary

The bed-photo extractor now accepts the smaller fiducial components produced
by a 1684 x 2236 overhead photo. Previously, its fixed 40 px lower dimension
and 100-pixel area floor rejected every fiducial in that capture even though
the printed V marks were present and usable.

## Reason

The supplied v3 sheet photo is about half the linear size of the prior
3072 x 4080 calibration images. Its F1 fiducial footprint is approximately
27 x 37 px with 103 ink pixels. The old filter required at least 40 px in one
dimension and 100 pixels, so seeded fiducial selection stopped before any
station geometry could be evaluated.

## Implementation

The common fiducial component predicate now accepts:

- 80 to 1,200 ink pixels;
- 32 to 120 px maximum dimension.

Seeded fiducial lookup uses the same predicate as the full-sheet path, avoiding
two different definitions of a plausible fiducial. The quadrant and
largest-component safeguards remain unchanged.

## Verification

- A new red-first regression used a 27 x 37 px, 103-pixel fiducial. It was
  rejected before the change and accepted afterward.
- The existing paper-edge and station-mark rejection test still passes.
- The synthetic v3 extraction test passes at 1750 x 1750 with 4 fiducials and
  all 819 station marks.
- The supplied 1684 x 2236 photo now resolves four fiducials and enters dense
  station matching.
- All `64` focused bed tests pass.
- The full converter suite passes all `571` tests with one expected
  OpenGL-context skip.

## Struggles and rejected approaches

- Upscaling the whole image was rejected because it adds runtime and does not
  create missing detail; the fiducials are large enough to identify at native
  resolution.
- Lowering only the dimension floor was insufficient because the same compact
  image reduces fiducial area below the previous 100-pixel floor.
- Removing the size filter entirely would admit station groups and label
  components as fiducial candidates.

## Risks and follow-up

Compact photos leave fewer pixels across each 3 mm station arm and are more
sensitive to JPEG blur, threshold changes, and merged pen-up drag marks. A
successful fiducial match does not by itself validate station extraction or
produce an accepted profile.

The first compact v3 sheet remains invalid for profile fitting because its
pen-up travel contains visible drag traces; see the 2026-10-29 M-12/T-01H lab
note.

## Files

- `tools/measure_bed_error_photo.py`: compact fiducial bounds and shared
  predicate.
- `software/tests/test_bed_photo_measurement.py`: compact-component regression.
- `software/README.md`: documented compact-photo behavior.
