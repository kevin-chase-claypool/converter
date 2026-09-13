---
id: RPSW-20260913-005
date: 2026-09-13
category: rp23cnc-software
affected_categories:
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e07b_hx711_actuator_steps
tags:
  - toolhead
  - e07b
  - hx711
  - force-calibration
  - testing
related:
  - docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md
---

# Add E-07B fast force trace

## Summary

Added the `r` service command to run one bounded 12-down/12-up actuator trace
with timestamped HX711 records, avoiding a manual host round trip after every
short pulse.

## Reason

The scale shut off during the manual one-pulse/review cycle. The scale must be
observed continuously while the controller preserves each force-sensor sample.

## Implementation

`r` requires an explicit `t` tare after physical pen clearance. It uses fixed
10 ms pulses, a 500 ms interruptible settle, and a three-sample HX711 record
after every pulse. It stops and sleeps on fault, failed sensing, or `x` abort.
The external scale remains the force authority; the command does not derive
force from pulse duration.

## Verification

`arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350
firmware\pen_pressure\e07b_hx711_actuator_steps` passed.

Hardware method validation passed in the first 26-second scale recording:
the bounded run completed a continuous approximately 0--75--0 g excursion
before the scale auto-off timer. This validates trace timing and sleep-between-
pulse behavior only; the matching serial `TRACE` records remain required for
HX711-to-grams calibration.

## Struggles and rejected approaches

Per-point user/agent review was rejected because it exceeded the scale's
auto-off interval and made a complete unload trace impractical.

## Risks and follow-up

Start only from a physically clear, tared pen; record the scale display on
video and keep `x` available. This remains a bench test, not production force
control. Repeat with complete retained serial trace lines to establish the
transfer and hysteresis evidence.

## Files

- `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`: bounded trace command.
- `firmware/README.md`: service-test capability.
- `firmware/pen_pressure/README.md`: command safety/use description.
- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`: test-method evidence.
