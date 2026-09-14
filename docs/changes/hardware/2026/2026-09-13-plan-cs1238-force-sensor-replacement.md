---
id: HW-20260913-013
date: 2026-09-13
category: hardware
affected_categories:
  - rp23cnc-software
status: planned
components:
  - hardware/toolhead
  - firmware/pen_pressure
tags:
  - toolhead
  - cs1238
  - hx711
  - load-cell
  - force-control
  - testing
related:
  - HW-20260913-012
  - RPSW-20260913-005
---

# Plan CS1238 force-sensor replacement

## Summary

The selected CS1238 load-cell ADC breakout will replace the installed HX711.
The intended common breakout retains the HX711 module's two mounting holes,
four-wire load-cell terminals, and `VCC/GND/DT/SCK` header. The previously
purchased NAU7802 is retained as a spare and is not the active design.

## Reason

Three clear-start external-scale traces proved the N20 can repeat a bounded
clear-to-contact-to-clear cycle, but the HX711 did not classify physical force:
its no-contact response overlapped initial contact and its reported load lagged
release. The CS1238 can use the existing two-wire data/clock harness while
offering selectable higher data rates. It must still earn force authority
through its own test gates.

## Implementation

No wiring, firmware, or production behavior changed. Preparation adds:

- receipt inspection for the exact breakout's 3.3 V requirements, header and
  bridge-terminal labels, and two-hole fit;
- E-07C motor-inert CS1238 bring-up with the DRV8833 asleep;
- E-08C measured 40/640/1280 SPS rate/noise characterization; and
- E-09C three short clear-start scale/video traces, limited initially to six
  10 ms down and six up pulses, with RMS-band separation as the acceptance
  criterion.

## Verification

Documentation review passed. No hardware verification is claimed: the exact
breakout revision and its safe wiring remain unverified until receipt.

## Struggles and rejected approaches

The prior 12-down/12-up trace reached 59.3 g, 70.7 g, and 71.0 g in three
otherwise clear-start runs. Reusing that aggressive envelope as the first
replacement test was rejected. A new ADC is also not being treated as a
pen-up safety signal; mechanical timed lift and clearance remain separate.

## Risks and follow-up

The CS1238 can offer a faster sampling cadence but cannot solve a bypassed or
side-loaded mechanical force path by itself. Do not select a target force, raw
threshold, or loop cadence until E-07C/E-08C/E-09C pass. The actual pen and
its production clamp are required for final T-01J qualification.

## Files

- `docs/hardware/BOM.md`: records the CS1238 selection and NAU7802 spare.
- `docs/testing/TEST_PLAN.md`: adds E-07C/E-08C/E-09C acceptance gates.
- `firmware/pen_pressure/README.md`: records the planned pin/firmware change
  and preserves the disabled force-control boundary.
- `docs/report/lab-notes/2026-09-13-e-14c-drv8833-label-mapping-correction.md`:
  records the repeated-trace evidence and decision.
