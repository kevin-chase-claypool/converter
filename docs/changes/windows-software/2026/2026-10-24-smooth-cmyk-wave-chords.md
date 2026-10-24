---
id: WSW-20261024-007
date: 2026-10-24
category: windows-software
affected_categories:
  - windows-software
  - hardware
status: implemented
components:
  - software/converter_core/cmyk.py
  - software/generator_tabs/cmyk_tab.py
  - software/tests/test_cmyk_tab.py
tags:
  - cmyk
  - wave-screen
  - waveform
  - faceting
  - path-tolerance
related:
  - WSW-20261024-006
  - 2026-10-23-m-13-cmyk-yellow-feed-sensitivity
---

# Smooth CMYK wave-screen chords within the path budget

## Summary

CMYK Wave-screen sine rows now receive enough source points to keep each
piecewise-linear chord within the configured Path tolerance after artwork
scaling. The rows remain parallel, but the visible peaks and crossings are
smoother instead of turning into angular facets.

## Reason

The shared-wave change removed the large overlap and wide-gap pattern. The
first physical print from that implementation started cleanly, but the
operator reported that the individual yellow waves were still visibly angular.
A rendered source inspection found the same facets on paper: a typical full
wave contained only about eight straight segments.

At the current effective pitch of about `3.36 mm`, each chord sampled about
every `0.84 mm`. Near full amplitude that leaves roughly `0.13 mm` between the
straight chord and the intended sine, despite the selected `0.05 mm` Path
tolerance. The tolerance previously affected polar planner subdivision but
not Wave-screen source sampling.

## Implementation

- `_wave_rows` derives its horizontal sample step from Path tolerance and the
  sine's maximum curvature.
- `screen_channel` exposes `path_tolerance_mm`, defaulting to `0.05 mm`.
- The CMYK tab passes its Path tolerance divided by Artwork scale, so scaling
  the screened result cannot multiply chord error above the requested limit.
- The change only increases the point density along each sine; it does not
  change row pitch, amplitude, image masking, bed compensation, or the planner.

## Verification

- A new regression failed before the change at `0.0979 mm` maximum chord
  error for a `4 mm` pitch and now passes below `0.05 mm`.
- A CMYK integration regression confirms the tab converts its `0.05 mm`
  paper-space budget to the correct source-space value at `280 %` scale.
- At the print's `1.2 mm` source pitch and `280 %` scale, the new paper-space
  sample step is `0.5219 mm`, about `12.9` segments per full wave. The measured
  maximum chord error is `0.0498 mm`, down from approximately `0.13 mm`.
- The existing all-angle spacing, parallel-row, and blank-region regressions
  continue to pass.
- Full converter discovery passes `505` tests with one OpenGL-context skip.

## Struggles and rejected approaches

- Keeping the old `spacing * 0.25` sample cap preserved visible corners.
- Hard-coding a denser step would ignore the operator's Path tolerance and
  artwork scale.
- Smoothing the plotted G-code after generation was rejected because the next
  save would recreate the same faceted source.

## Risks and follow-up

- Lower Path-tolerance values now increase wave point count and G-code length.
  Regenerate all four CMYK files after updating.
- A fresh full yellow print is required to confirm that the paper follows the
  smoother source. Bed compensation remains enabled and unchanged.

## Files

- `software/converter_core/cmyk.py`: tolerance-aware wave sampling.
- `software/generator_tabs/cmyk_tab.py`: paper-space tolerance handoff.
- `software/tests/test_cmyk_tab.py`: chord-error and scale regressions.
- `software/README.md`: current Wave-screen behavior.
- `docs/report/lab-notes/2026-10-23-m-13-cmyk-yellow-feed-sensitivity.md`:
  physical result and next print.
- `docs/testing/TEST_PLAN.md`, `docs/project/ROADMAP.md`, and
  `docs/project/ENGINEERING_LOG.md`: current M-13 status.
