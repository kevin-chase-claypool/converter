---
id: RPSW-20260910-002
date: 2026-09-10
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: verified
components:
  - RP23U5XBB homing candidate
  - GP27/U3 PRB return
  - motor-inert P100 diagnostic
tags:
  - p100
  - f-08
  - probe
  - g38
  - magnetic-homing
  - safety
related:
  - RPSW-20260910-001
---

# Verify real-magnet PRB/G38 path

## Summary

The RP23U5XBB homing candidate passed direct and actual GP27/U3 probe-input
testing. The blue `A_HOME` return was moved from `LIMA SIG` to `PROBE SIG` only
after the direct PRB stage passed.

## Reason

The baseline firmware excluded probe support, and the prior LIMA check could
not show a controller-visible state. P100 requires a safe, motor-inert proof
that the installed magnetic output can stop a G38 probe cycle on the A axis.

## Implementation

The candidate firmware enables `PROBE_ENABLE`, NGC parameters, and expressions
without overwriting the baseline UF2. The installed PRB input uses `$6=1` for
the normally-open U3 low-side closure. The test used
`p100_handshake_test.ino`, which leaves all actuator-related pins untouched.

## Verification

- Candidate boot reported `SIGNALS:HSEP`, `EXPR`, PRB pin 7, and Aux P0 pin 36.
- Direct dry contact and the actual U3 path both changed ioSender P blank/red
  in the intended directions.
- In `SCAN_ACTIVE`, real TMAG detection changed `detected=0 -> 1 -> 0` in sync
  with P blank -> red -> blank.
- `G38.3 A30 F60` returned `[PRB:0.000,0.000,0.000,11.475:1]`.
- `G38.5 A30 F60` returned `[PRB:0.000,0.000,0.000,13.275:1]`.
- TB6600 branch fuses were removed; no physical axis moved. `$20=1` and `G90`
  were restored at completion.

## Struggles and rejected approaches

The first G38 attempt returned `:0` because the diagnostic's five-minute scan
timeout had expired. Disarming, reacquiring the baseline, and repeating inside
the timeout passed. No polarity workaround or actuator command was used.

## Risks and follow-up

F-08 remains incomplete: verify `#5064`, filesystem `G65 P100 Q1`, macro
abort/release behavior, and G53/G54/G10 semantics. Do not run Q3/Q4, enable
production P100, or reinstall TB6600 fuses as part of this milestone.

## Files

- `hardware/firmware-homing-candidate.uf2`: archived candidate artifact.
- `firmware/grblhal/config/build-record.md`: candidate provenance.
- `docs/hardware/WIRING_TABLE.md`: installed PRB endpoint.
- `docs/testing/TEST_PLAN.md`: F-08 partial result.
- `docs/report/lab-notes/2026-09-10-e-18-motor-inert-p100-handshake.md`: bench evidence.
