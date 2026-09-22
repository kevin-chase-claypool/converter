---
id: RPSW-20260922-022
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
  - force-limit
related:
  - RPSW-20260922-021
  - T-02
  - T-01J
---

# Add Fine Home Contact Approach

## Summary

The supervised home-origin M3 seek now uses two pulse widths: 25 ms while the
load cell is below one-fifth of the 35 g contact threshold, then 5 ms for the
final approach. It keeps the 50 ms sensing interval, 100-pulse/8-second bound,
and existing calibrated force limits.

## Reason

The first faster 25 ms-only attempt made paper contact and entered force hold
at 177,470 raw, essentially the 35 g target. The next filtered sample reached
305,811 raw, only about 0.7 g beyond the 60 g hard limit, causing a correct
but unwanted hard-force fault. The large pulse is appropriate while the pen is
clear but not near contact.

## Implementation

- Select 25 ms pulses below `CONTACT_RAW_DELTA / 5`; select 5 ms pulses at or
  above that value.
- Store the width of an active pulse so changing force readings cannot shorten
  or lengthen a pulse in progress.
- Increase the candidate bound to 100 pulses while retaining its 8-second
  timeout. The maximum is based on the coarse pulse duration, so every
  permitted sequence fits within the timeout.
- Retain the 35 g contact threshold, 60 g hard limit, 30-pulse GP2-release
  check, driver sleep, and manual-M5 fault recovery.

## Verification

- Captured hardware trace reproduces the final-step hard-limit transient with
  the 25 ms-only candidate.
- Arduino RP2350 compilation/link produced the `.elf`, `.bin`, and `.uf2`
  artifacts for the updated sketch. The CLI process did not return after
  artifact generation and was stopped; no compiler error was reported.
- Documentation-index verification: pending after this edit.
- The two-stage source has not yet been flashed or tested on hardware.

## Struggles and rejected approaches

Raising the 60 g hard limit was rejected because it would weaken the user’s
selected safety limit to conceal an approach-control issue. Keeping every pulse
at 5 ms was rejected because the first trace showed it needs roughly 40 seconds
to cover the home-to-paper distance. The approach therefore changes speed only
after the sensor reports meaningful force.

## Risks and follow-up

The one-fifth switching threshold is a supervised candidate. Confirm the next
M3 run reaches `HOLD_FORCE` without a hard-limit fault and then perform a
representative M5 clear. Do not use M3/M5 for drawing until T-02/T-01J records
repeatable behavior.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`:
  coarse/fine pulse configuration.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.*`:
  pulse-width selection and active-pulse ownership.
- `firmware/README.md`, `firmware/pen_pressure/README.md`,
  `firmware/pen_pressure/CONTROL_STRATEGY.md`,
  `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`:
  current behavior and validation procedure.
- `docs/report/lab-notes/2026-09-22-t-02-home-contact-seek-setup.md`:
  hardware evidence for this adjustment.
