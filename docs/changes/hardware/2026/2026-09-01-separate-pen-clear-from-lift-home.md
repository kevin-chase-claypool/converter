---
id: HW-20260901-001
date: 2026-09-01
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: planned
components:
  - toolhead-force-control
  - toolhead-lift-home-switch
  - firmware/pen_pressure
  - docs/decisions/ADR-004-separate-pen-clear-from-lift-home.md
tags:
  - toolhead
  - m3
  - m5
  - pen-clear
  - lift-home
  - load-cell
related:
  - HW-20260830-005
---

# Separate Normal Pen Clear from LIFT Home

## Summary

Defined two different pen-up outcomes. Normal high-cycle `M5` is `PEN_CLEAR`:
the Pro Micro retracts until the filtered load-cell reading returns to the
measured no-contact release band, then applies one bounded clearance pulse.
`LIFT_HOME` is the separate full-retract switch reference used only at boot,
recovery, or a service action.

## Reason

Plotting has many M3/M5 transitions. Requiring every M5 to travel to the
distant home switch would add unnecessary travel and switch cycles. The load
cell can rapidly establish pen release from paper, but its no-contact reading
does not uniquely identify absolute lift height.

## Implementation

- `M3`: seek using `F_contact_on`, then enter force hold.
- `M5`: use a lower hysteretic `F_release_off` plus debounce, issue a measured
  clearance pulse, and report `PEN_CLEAR`.
- `LIFT_HOME`: use the planned `GP2` normally-open switch input only for an
  absolute reference. It remains separate from the mechanical backstop.
- T-01H now characterizes release hysteresis, debounce, clearance-pulse bounds,
  pen-tip gap, and 30-cycle normal M3/M5 behavior.

## Verification

Documentation decision only. No switch wiring, firmware behavior, threshold,
or clearance-pulse value is verified. T-01G and T-01H remain commissioning
gates.

## Struggles and rejected approaches

Treating every M5 as a full `LIFT_HOME` motion was rejected: it does not match
the high-cycle plotting use case. Treating the no-contact load-cell value as an
absolute actuator position was also rejected because different clear positions
can have the same no-contact force.

## Risks and follow-up

The final mechanism must provide enough measured clearance after the pulse for
travel over paper variation. Calibrate signed force thresholds, debounce,
pulse duration/PWM, and the resulting gap under T-01H before enabling normal
M5 control. Keep startup/recovery on `LIFT_HOME` until T-01G verifies GP2.

## Files

- `firmware/pen_pressure/CONTROL_STRATEGY.md`: defines `PEN_CLEAR` and
  `LIFT_HOME` state behavior.
- `firmware/pen_pressure/README.md`: documents M3/M5 behavior and gates.
- `docs/integration/INTERFACES.md`: updates the G-code/toolhead contract.
- `docs/testing/TEST_PLAN.md`: adds T-01H.
- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: places T-01H in the gated path.
- `docs/hardware/WIRING_TABLE.md`: scopes GP2 to home/recovery rather than
  normal M5.
- `docs/decisions/ADR-004-separate-pen-clear-from-lift-home.md`: records the
  long-lived control-interface decision.
