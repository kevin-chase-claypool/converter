---
id: HW-20260901-002
date: 2026-09-01
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - toolhead-force-control
  - hx711
  - firmware/pen_pressure
tags:
  - toolhead
  - load-cell
  - calibration
  - force-profile
  - startup-baseline
  - nonvolatile-storage
related:
  - HW-20260901-001
---

# Persist Toolhead Force Profile Separately from Boot Baseline

## Summary

Added T-01I to validate a scale-derived force-control profile saved in
nonvolatile storage and a separate no-contact baseline captured in RAM after
each `LIFT_HOME`.

## Reason

The toolhead needs usable calibrated force values during normal operation, but
sensor drift at startup must not silently alter those accepted values. The
separate scale fixture creates the persistent force profile; a boot baseline
only compensates the current unloaded residual.

## Implementation

- An explicit local service action commits one versioned, checksummed profile.
- The profile includes force conversion/direction, contact/release thresholds,
  target and hard-limit force, debounce, correction-pulse bounds, and clearance
  pulse bounds.
- Normal M3/M5 cycles and boot never write the profile.
- Each boot verifies the profile, takes a RAM-only no-contact baseline after
  `LIFT_HOME`, and rejects force control for invalid profile or baseline data.

## Verification

Documentation and test-plan addition only. T-01I requires five power cycles,
profile identity/checksum checks, RAM-baseline checks, and low/nominal scale
force checks before persistent calibration is accepted.

## Struggles and rejected approaches

Automatic re-calibration from an unloaded reading was rejected. It could mask a
bad sensor, changed mechanism, or paper condition while destroying the known
scale-derived force mapping.

## Risks and follow-up

The firmware storage format, checksum method, profile version, baseline/noise
limits, and force tolerances remain TBD until E-07/T-01E/T-01H establish their
measured inputs. Do not enable persistent profile use beforehand.

## Files

- `firmware/pen_pressure/CONTROL_STRATEGY.md`: specifies profile and baseline
  ownership.
- `firmware/pen_pressure/README.md`: adds the commissioning gate.
- `docs/testing/TEST_PLAN.md`: adds T-01I acceptance criteria.
- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: gates contact seek on T-01I.
- `docs/decisions/ADR-004-separate-pen-clear-from-lift-home.md`: records the
  persistent-versus-RAM-only separation.
