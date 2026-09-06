---
id: WSW-20260905-004
date: 2026-09-05
category: windows-software
affected_categories:
  - windows-software
  - rp23cnc-software
  - hardware
status: implemented
components:
  - software/converter_core/settings.py
  - software/converter_core/gcode.py
  - software/tests/test_theta_feed.py
  - software/README.md
  - docs/integration/INTERFACES.md
tags:
  - iosender
  - grblhal
  - gcode
  - m3
  - m5
  - z-axis
related:
  - WSW-20260905-003
  - F-02
  - F-05
  - M-06
---

# Make converter programs self-contained for ioSender

## Summary

Changed the Windows converter's production default from Z pen moves to the
machine's M3/M5 pen contract, and added an explicit modal preamble to every
generated program.

## Reason

The installed controller exposes an unwired Z slot only to make A available.
The prior default could therefore stream unintended Z words through ioSender.
The prior program header also relied on feed and work-coordinate modes that a
previous command or macro might have established.

## Implementation

`Settings.include_z` and the Qt checkbox now default to false. Default files
begin with `G21`, `G90`, `G94`, `G17`, and `G54`, then issue M5 and its
configured pen-up dwell before travel. The optional Z mode remains available
for deliberate non-production experiments, but is not the machine default.

## Verification

- Added a regression test that checks the complete default preamble, M3/M5
  presence, and the absence of Z words.
- Ran the converter unit suite and documentation index write/check commands.

## Struggles and rejected approaches

Leaving the UI default enabled and relying on the operator to clear it for each
conversion was rejected because ioSender streams the resulting Z words without
converting them into M3/M5.

## Risks and follow-up

F-02 must still stream a newly generated default file on the installed
controller. P100 commissioning, M3/M5 electrical and clearance verification,
X-axis validation, and M-06 coordinated-motion verification remain required
before direct P100-to-print operation is authorized.

## Files

- `software/converter_core/settings.py`: M3/M5 default.
- `software/converter_core/gcode.py`: self-contained modal preamble.
- `software/tests/test_theta_feed.py`: default-output regression coverage.
- `software/README.md`: converter behavior and Z-use guidance.
- `docs/integration/INTERFACES.md`: authoritative host/controller contract.
- `docs/integration/IOSENDER_CONVERTER_COMPATIBILITY_REVIEW.md`: resolved
  software discrepancies and remaining gates.
