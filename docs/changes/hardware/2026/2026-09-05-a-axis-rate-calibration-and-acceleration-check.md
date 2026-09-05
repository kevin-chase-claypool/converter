---
id: HW-20260905-003
date: 2026-09-05
category: hardware
affected_categories:
  - hardware
  - rp23cnc-software
status: verified
components:
  - RP23CNC/RP23U5XBB
  - A-axis TB6600 and 17HS15-1504S-X1 motor
  - A-axis calibration and rate tests
tags:
  - a-axis
  - calibration
  - acceleration
  - tb6600
  - commissioning
related:
  - M-02
  - M-04
  - docs/report/lab-notes/2026-09-05-m-02-a-axis-rate-ramp.md
---

# Correct A-axis calibration and characterize the F5000 ramp

## Summary

The A-axis steps-per-unit setting was corrected to `$103 = 4.44444`, matching
the motor-shaft-degree contract. A one-motor-revolution check passed, and
`A720` and `A1440` at `F5000` completed smoothly with the expected slow ramp.

## Reason

The initial rate-ramp screenshot showed `$103 = 250.000`, which did not match
the planned 8-microstep, 1,600-pulse motor calibration. The corrected setting
needed a physical check before interpreting commanded A travel or feed rates.

## Implementation

The operator set `$103` to `4.44444` in ioSender, first tested `$113=5000`,
then raised `$113` to `15000` for the high-rate check. `$123` was increased
from `10` through `25`, `50`, and finally `300`; the controller ramps rather
than applying the target feed instantly.

## Verification

- `G1 A360 F300` and `G1 A-360 F300` each completed smoothly and returned to the
  reference mark, passing M-04's one-motor-revolution check.
- `G1 A720 F5000` and `G1 A1440 F5000` completed smoothly. The operator observed
  slow ramp-up and ramp-down; at `F5000`, the target is `83.33 deg/sec` and
  each ramp takes about `8.3 s`.
- The same `A1440 F5000` forward/reverse check passed at `$123=25` and
  `$123=50`, with no reported stalls or return-position errors. Current and
  temperature were not recorded for those two steps.
- The operator then raised `$113` to `15000`, `$123` to `300`, and ran the
  corresponding `F15000` forward/reverse test. Motion was reported smooth in
  both directions. Assuming `A1440` travel, each ramp is about `0.83 s`;
  current, temperature, and exact travel were not recorded.
- The operator then raised `$113` to `40000` and ran `A1440` forward and
  reverse at `F40000`; both directions reportedly returned exactly to the
  reference mark. At `$123=300`, this move is too short to establish a true
  `40000 deg/min` cruise, so it is a triangular acceleration-profile result.
- M-05, the full 12:1 bed-ratio check, remains open.

## Struggles and rejected approaches

The earlier `$103 = 250.000` value was a stale or incorrect installed setting,
not the calibration to use for the A-axis. The short high-F moves are not a
final plotting-acceleration test because most of their motion is spent in the
configured acceleration profile.

## Risks and follow-up

Do not raise the limits further until current, temperature, exact travel, and
return position are recorded. Repeat the selected acceleration under the
eventual pen-load condition before adopting a production value, and complete
M-05 before using bed-rotation speed as a validated machine value.

## Files

- `docs/report/lab-notes/2026-09-05-m-02-a-axis-rate-ramp.md`: records the
  corrected calibration and ramp observation.
- `docs/testing/TEST_PLAN.md`: updates M-02 and M-04 evidence.
- `docs/integration/INTERFACES.md`: records the installed A-axis unit contract.
- `docs/project/ENGINEERING_LOG.md`: records the decision and follow-up.
