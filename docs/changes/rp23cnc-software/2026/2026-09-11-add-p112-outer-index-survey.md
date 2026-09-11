---
id: RPSW-20260911-012
date: 2026-09-11
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/grblhal/macros/P112.macro
  - tools/validate_homing_macro.py
tags:
  - P112
  - P100
  - A-axis
  - index-magnet
  - M-09
  - safety
related:
  - RPSW-20260911-011
---

# Add P112 Outer-Index Survey

## Summary

Added P112, a standalone bounded outer-index survey that makes two A-axis
magnetic observations and stops the TMAG on the second-pass index center.

## Reason

P100 Q5 now repeats the center-magnet result without hidden homing, and the
reinstalled A-axis fuse passed a low-speed `A10`/`A-10` return test. The next
safe evidence step is to observe the real index magnet without authorizing G54
A registration.

## Implementation

P112 requires a fresh P111 followed by Q5 with no intervening axis movement.
It moves the TMAG +X by the measured center-to-index radius `223.675804` mm,
uses the established active-low Aux0/GP28 handshake, captures two `G38.3`/
`G38.5` A footprints, validates their `4320 +/- 10` motor-degree spacing, and
approaches the equivalent second-pass center. It releases Aux0 and makes no
`G10` work-offset write. Probe captures are converted from G54 to G53 A before
the final G53 approach.

## Verification

- `G1 A10 F120`, followed by `G1 A-10 F120`, returned controller MPos A to
  `0.000`; the physical bed reference mark also returned exactly.
- `python tools/validate_homing_macro.py` passed the P100/P111/P112 static
  safety contract.
- Installed P112 survey: pending.

## Struggles and rejected approaches

Enabling P100 Q4 would also make its eventual G54 A write reachable, which is
not appropriate for the first real-index observation. P112 keeps M-09 evidence
separate from registration.

## Risks and follow-up

The outer point is near the positive-X machine edge, so P112 must be started
only from the observed Q5 TMAG centroid and with the XY path clear. It may
travel slightly more than two full bed revolutions because the first index
entry begins at an unknown A phase. Do not run Q4 or production Q0 yet.

## Files

- `firmware/grblhal/macros/P112.macro`: bounded, non-registering index survey.
- `tools/validate_homing_macro.py`: static P112 motion and no-G54-write checks.
- `firmware/README.md`: current staged registration state.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: P112 commissioning contract.
- `firmware/grblhal/macros/README.md`: operator procedure.
- `docs/integration/INTERFACES.md`: staged command contract.
