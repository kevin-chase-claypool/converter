---
id: RPSW-20260922-007
date: 2026-09-22
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/e09e_cs1238_pen_scale_pulse
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - e-09e
  - n20
  - pen-clear
  - pulse-duration
  - safety
related:
  - RPSW-20260922-006
  - docs/report/lab-notes/2026-09-22-e-09e-installed-pen-scale-direction.md
---

# Refine E-09E pulses and stage pen-clear candidate

## Summary

E-09E now permits 5–100 ms supervised pulses in 5 ms increments. The disabled
production controller stages a 100 ms M5 extra-lift candidate instead of 500 ms.

## Reason

An observed fault-free 10 ms up pulse reduced kitchen-scale force from 35.5 g
to 2.2 g, making the prior minimum too coarse near the 40–60 g target. The
observed N20 speed also suggests 100 ms may provide adequate eventual air-gap
motion without the excessive 500 ms starting value.

## Implementation

- Changed only the temporary E-09E manual pulse bounds and step size.
- Updated the integrated controller's `PEN_CLEAR_EXTRA_LIFT_MS` candidate to
  100 ms.
- Preserved all commissioning gates as false. `PEN_CLEAR_VALID` remains false;
  100 ms is not a verified clearance setting.

## Verification

- Recompile both Pro Micro sketches after the edits.
- The E-09E lab note retains the raw/scale observations used for the decision.
- No automatic force control, M3/M5 driven motion, or 30-cycle clearance test
  is claimed.

## Struggles and rejected approaches

The preliminary 40.7/62.5 g readings were not monotonic, so no installed-pen
slope or force profile was fitted. Reducing the test pulse resolution is safer
than inferring a linear correction from those points.

## Risks and follow-up

Repeat a fresh-tare 5 ms-pulse series with complete raw lines and pulse counts.
Before enabling normal M5 behavior, T-01H must measure the pen-tip gap and
pass 30 full clear cycles using the staged 100 ms candidate.

## Files

- `firmware/pen_pressure/e09e_cs1238_pen_scale_pulse/e09e_cs1238_pen_scale_pulse.ino`: 5 ms supervised pulse resolution.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: 100 ms disabled M5 clearance candidate.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: candidate comment.
- `docs/report/lab-notes/2026-09-22-e-09e-installed-pen-scale-direction.md`: bench evidence.
