---
id: RPSW-20260922-018
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h
  - integrated CS1238 moving-average force hold
tags:
  - cs1238
  - force-target
  - hard-force-limit
  - supervised-bench
related:
  - docs/report/lab-notes/2026-09-22-e-09c-cap-free-repeat.md
  - docs/project/ENGINEERING_LOG.md
---

# Set integrated force target to 35 g and limit to 60 g

## Summary

Changed the supervised integrated Pro Micro toolhead's force target to the
calibrated 35 g equivalent and lowered its hard-force trip to the 60 g
equivalent.

## Reason

The operator selected a lower drawing-force target and requested a lower
over-force cutoff for the current non-precision plotter.

## Implementation

- Retained the E-09C fit of 5,038.77 raw/g; set the target to 176,357 raw and
  hard-force limit to 302,326 raw.
- The existing ±5 g target-ready tolerance now represents approximately
  30–40 g around the 35 g target.
- Kept the fresh boot tare, 16-sample moving average, 250 ms force-correction
  cadence, 100 ms mechanical preload, and GP2 maximum-UP behavior unchanged.
- Changed only the integrated toolhead config. The standalone E-09F diagnostic
  continues to use its separate 70 g profile.

## Verification

- `arduino-cli compile --build-path <temporary-directory> --fqbn
  rp2040:rp2040:sparkfun_promicrorp2350
  firmware\pen_pressure\pro_micro_rp2350_toolhead` passed (79,512 bytes
  program storage; 16,160 bytes global memory).
- `python tools\docs_index.py --write` and `--check` passed for 188 change
  notes. Hardware behavior with the revised target has not yet been tested.

## Struggles and rejected approaches

None. This is a direct operating-point selection using the existing linear
fit; no new calibration fit was made.

## Risks and follow-up

The target and hard limit are raw-count equivalents derived from the bench fit,
not precision gram measurements under every installed-pen geometry. The
100 ms downward preload remains timed and does not stop at 35 g; force-feedback
correction follows it. Keep the physical cutoff reachable during the
supervised test and verify that telemetry settles near the intended load
without approaching the hard limit before using the controller in a plot.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: updated
  integrated raw target and cutoff.
- `firmware/pen_pressure/README.md`: updated current settings and scope.
- `docs/project/ENGINEERING_LOG.md`: records the decision and next test.
