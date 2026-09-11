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
The measured `223.675804` mm +X radius would exceed the X `-10` mm home
pull-off bound, so P112 moves along that same +X line only to G53 X `-10.5` mm,
approximately 2.2 mm inboard. It uses the established active-low Aux0/GP28
handshake, captures two `G38.3`/
`G38.5` A footprints, validates their `4320 +/- 15` motor-degree spacing, and
trims backward from the second exit to its second-pass center. Both searches
run at `10000` motor-degrees/min (2.31 bed RPM); their combined 9,000-degree
search allowance takes no more than 54 seconds. It releases Aux0 and makes no
`G10` work-offset write. Probe captures are converted from G54 to G53 A before
the final G53 trim.

## Verification

- `G1 A10 F120`, followed by `G1 A-10 F120`, returned controller MPos A to
  `0.000`; the physical bed reference mark also returned exactly.
- `python tools/validate_homing_macro.py` passed the P100/P111/P112 static
  safety contract.
- Installed P112 evidence: the first complete two-footprint observation was
  `11234.037..11340.462` then `15566.192..15671.942` A motor degrees. Its
  footprint centers were 4331.818 motor degrees apart; widths were 106.425 and
  105.750 degrees. The original +/-10 gate rejected it by 1.818 degrees.
  The bounded +/-15 gate accepts that measured result; a successful installed
  completion then parked at pass-two center
  `MPos:-10.500,-218.363,A8610.084` after the observed second footprint
  `A8557.209..8662.959`. It printed the completion message, released PRB, and
  made no G54 write. The operator visually confirmed the index magnet centered
  beneath TMAG at that stop. Registration remains disabled.

## Struggles and rejected approaches

Enabling P100 Q4 would also make its eventual G54 A write reachable, which is
not appropriate for the first real-index observation. The first P112 version
would have approached a target one full revolution beyond the second observation
at the old 120 motor-degree/min registration feed; it was corrected before SD
installation. P112 keeps M-09 evidence separate from registration.

## Risks and follow-up

The outer point is 0.5 mm inside the positive-X home pull-off boundary, so P112
must be started only from the observed Q5 TMAG centroid and with the XY path
clear. The two
searches can total up to 9,000 motor degrees (2.083 bed revolutions) because
the first index entry begins at an unknown A phase; the final trim reverses
only across half of the observed index footprint. Do not run Q4 or production
Q0 yet.

## Files

- `firmware/grblhal/macros/P112.macro`: bounded, non-registering index survey.
- `tools/validate_homing_macro.py`: static P112 motion and no-G54-write checks.
- `firmware/README.md`: current staged registration state.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: P112 commissioning contract.
- `firmware/grblhal/macros/README.md`: operator procedure.
- `docs/integration/INTERFACES.md`: staged command contract.
