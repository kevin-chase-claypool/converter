---
id: RPSW-20260923-007
date: 2026-09-23
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - cs1238
  - force-control
  - false-fault
  - observability
related:
  - RPSW-20260923-006
---

# Reject implausible CS1238 conversions

## Summary

An out-of-range CS1238 conversion is now dropped before it can reach the force
filter. Three consecutive implausible conversions raise a
`CS1238 reading implausible` fault instead, so a real sensor failure still
stops the machine. A `cs1238_rejects` counter is reported in telemetry.

## Reason

On 2026-09-23, with the toolhead idle in `LIFTED` and no motor command
outstanding, the controller faulted with `hard force limit exceeded`. The
fault record shows `cs1238_raw=-6292478` against `cs1238_filtered=-107985`: the
raw value is six million counts from the filtered value and far outside the
installed bridge's roughly -1.5e5 to +3.2e5 raw range. A single corrupt
conversion inside the 16-sample average produced a false over-force condition
and aborted a passing cycle set.

The same path explains the isolated -353,842 raw sample previously seen in the
E-09E kitchen-scale trace, so corrupt conversions are a recurring property of
this acquisition path rather than a one-off.

## Implementation

- `toolhead_config.h`: added `CS1238_SAMPLE_MIN_RAW` / `CS1238_SAMPLE_MAX_RAW`
  as the physical plausibility band, `CS1238_SAMPLE_MAX_DELTA_RAW` as twice the
  hard-force delta (about 120 g) relative to the live tare, and
  `CS1238_IMPLAUSIBLE_FAULT_STREAK` as 3.
- `pressure_controller.cpp`: `serviceCs1238()` rejects a conversion that is
  outside the plausibility band or further than the maximum delta from the live
  tare. Rejected samples never reach the moving average. The controller counts
  them and faults after three consecutive rejections.
- `pressure_controller.h`: added the rejection counter and implausible streak.
- `pro_micro_rp2350_toolhead.ino`: added `cs1238_rejects=<count>` to the shared
  telemetry record.

## Verification

- Compiled for `rp2040:rp2040:sparkfun_promicrorp2350` with `arduino-cli`
  1.5.1: passed, 82640 bytes program storage and 16244 bytes dynamic memory.
- `python tools\docs_index.py --write` and `--check` pass.
- Bench confirmation is required: a repeat cycle set should show
  `cs1238_rejects` either static or slowly growing, with no false hard-force
  fault.

## Struggles and rejected approaches

Raising the hard-force limit or requiring more averaging windows was rejected:
the guard was correct and the filtered value was genuinely over the limit — the
defect is a corrupt input, and widening the guard would blunt a real safety
check. Dropping implausible samples silently was also rejected; without a
persistence escape a genuinely failed ADC would leave the controller holding a
stale force value forever.

## Risks and follow-up

The plausibility band is generous, so it catches only gross corruption. A
moderate glitch that lands inside the band still enters the average; the
consequence is bounded because a single such sample shifts the 16-sample mean
by a few thousand counts, well under the force margins. If `cs1238_rejects`
grows quickly, the interface itself needs attention — supply decoupling, clock
and trace integrity, or a longer conversion settle in the driver.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: plausibility constants.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`: rejection and fault-streak logic.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`: rejection counters.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`: `cs1238_rejects` telemetry.
- `firmware/pen_pressure/README.md`, `docs/integration/INTERFACES.md`: document the rejection rule and the new field.
