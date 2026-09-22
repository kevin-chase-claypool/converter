---
id: RPSW-20260922-021
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - contact-seek
  - pulse-timing
  - cs1238
related:
  - RPSW-20260922-020
  - T-02
  - T-01J
---

# Revise Home Contact-Seek Pacing

## Summary

The supervised full-retract M3 seek now uses 25 ms DOWN pulses with 50 ms
sensor settling and an 80-pulse/8-second bound. It replaces the too-slow
5 ms/250 ms, 160-pulse/45-second candidate. Force thresholds and post-contact
moving-average control are unchanged.

## Reason

The first installed T-02 attempt safely exhausted its 160-pulse limit while
the pen remained about 4.5 mm above paper. Its CS1238 normalized force was
80,626 raw (about 16 g), below the 35 g contact target and 60 g hard limit.
The actual 800 ms of powered 5 ms pulses covered only about 7.5 mm of the
reported 12 mm full-retract gap, while 250 ms waits made the attempt take about
40 seconds.

## Implementation

- Use a dedicated `HOME_SEEK_SETTLE_MS` so the faster home search does not
  alter the established 250 ms force-hold correction cadence.
- Set home seek to 25 ms full-drive pulses, 50 ms sensor settling, 80 pulses,
  and 8 seconds. At the observed motion response this permits about 18.75 mm
  of bounded travel in about six seconds at the pulse cap.
- Retain the 35 g contact threshold, 60 g hard limit, 30-pulse GP2-release
  safeguard, motor sleep between pulses, and fault recovery behavior.

## Verification

- The installed 160 × 5 ms hardware trace reproduced the insufficient-travel
  failure safely and supplied the replacement timing evidence.
- Arduino RP2350 compile passed with
  `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350`.
- Documentation-index validation: pending after this edit.
- The revised 25 ms source has not yet been flashed or run on the toolhead.

## Struggles and rejected approaches

Increasing the 160-pulse limit alone was rejected: it would preserve roughly
40 seconds of no-contact stepping and still be unnecessarily slow. Changing
the shared force-hold correction period was rejected because the evidence only
supports changing initial home-seek pacing, not retuning post-contact control.

## Risks and follow-up

The 25 ms pulse can still overshoot the 35 g target if the final mechanical
response is abrupt; the 60 g hard limit remains the independent stop. Flash
only for a supervised T-02 run with cutoff reachable. Inspect the first
contact/hold transition and any fault before using M3/M5 for a drawing.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  revised home-seek-only timing and bounds.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  uses the dedicated home-seek settle interval.
- `firmware/README.md`, `firmware/pen_pressure/README.md`,
  `firmware/pen_pressure/CONTROL_STRATEGY.md`,
  `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`:
  current behavior and acceptance criteria.
- `docs/report/lab-notes/2026-09-22-t-02-home-contact-seek-setup.md`:
  captured first hardware result.
