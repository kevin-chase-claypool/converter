---
id: RPSW-20260922-028
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - cs1238
  - contact-detection
  - moving-average
  - force-control
related:
  - RPSW-20260922-027
---

# Confirm Contact by Trend

## Summary

Initial paper contact is now accepted from a persistent force response to a
stopped fine pulse, and subsequent force targets are referenced to that touch.

## Reason

The toolhead reached the former absolute 30 g raw threshold while the pen was
still approximately 0.5 mm above paper. Released-mechanism preload and
friction can therefore mimic a contact-force value.

## Implementation

After a 5 ms surface-approach pulse reaches the candidate region, the driver
sleeps. The controller requires an approximately 10,000-raw increase from the
pre-pulse level in three 25 ms-separated moving-average windows. An isolated
spike or relaxed value does not transition state. The accepted response is the
dynamic contact reference for tune target and hard-force limit. At 640 SPS,
the confirmation costs roughly 75 ms, not a visible pen-motion delay.

The integrated sketch uses the installed CS123x 2.0.3 library's `read()` API,
replacing removed 1.1.0 `forceRead()` usage.

## Verification

- Arduino CLI compile passed for the SparkFun Pro Micro RP2350 target with
  CS123x 2.0.3.
- The rejected absolute-threshold trace is recorded in
  `docs/report/lab-notes/2026-09-22-t-02-home-contact-seek-setup.md`.

## Struggles and rejected approaches

Further tuning of the absolute 30 g state threshold was rejected because it
would only move the false transition caused by friction/preload. A single
large filtered sample was also rejected because sticktion can create one-time
spikes.

## Risks and follow-up

The 10,000-raw response and three-window confirmation are supervised bench
candidates. Flash and run stationary T-02 to establish whether actual paper
contact produces the expected persistent signature, then tune only from that
evidence.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  trend confirmation and contact-relative targets.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  confirmation values.
- `firmware/pen_pressure/CONTROL_STRATEGY.md`: contact-definition contract.
