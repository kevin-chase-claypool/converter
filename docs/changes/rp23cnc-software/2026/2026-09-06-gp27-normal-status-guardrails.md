---
id: RPSW-20260906-001
date: 2026-09-06
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
  - hardware
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
  - firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md
  - docs/integration/INTERFACES.md
tags:
  - gp27
  - contact-ready
  - p100
  - safety
related:
  - RPSW-20260822-003
---

# Add GP27 Normal-Status Guardrails

## Summary

Added disabled-by-default RP2350 firmware guardrails that reserve the existing
GP27/U3 return for a future normal-print completion status without compromising
the established GP28/GP27 P100 magnetic protocol.

## Reason

No additional toolhead GPIO or drag-chain conductor is available. GP27 is
already isolated through U3, but an ordinary ready-high level could be confused
with P100's first magnetic-readiness acknowledgement unless the firmware
arbitrates the two uses explicitly.

## Implementation

Core 0 publishes `CONTACT_READY` only after three filtered samples are within
the configured target-force band, and publishes `CLEAR_READY` only after the
separate T-01H clearance gate. Core 1 can drive GP27 from either status only
while the magnetic state is `DISARMED`, GP28 is inactive, both cores are alive,
and no fault is present. The external status gate is false by default.

Any GP28 assertion suppresses normal status immediately. Firmware then holds
GP27 inactive for an initial conservative 20 ms before publishing a fresh P100
readiness ACK. Magnetic readiness, re-arm, scan, boot, and fault states retain
exclusive/fail-safe GP27 ownership.

This revision does not change the U3 wiring, the installed `LIMA` endpoint,
P100 macro behavior, emitted G-code, or fixed M3/M5 `G4` dwells. It does not
enable a grblHAL wait.

## Verification

- `git diff --check`: passed.
- Arduino CLI compile for `rp2040:rp2040:sparkfun_promicrorp2350`: passed.
- `python tools\\docs_index.py --write` and `python tools\\docs_index.py --check`:
  passed.
- Hardware F-08, T-01H, and any controller-side wait/alarm test: not run;
  normal-status output remains disabled.

## Struggles and rejected approaches

Adding a GPIO, a new drag-chain conductor, a second toolhead controller, or a
DS2413 remote GPIO expander was rejected because none provides a return signal
to RP23CNC without new wiring and all add more hardware complexity. Reusing
GP27 without a forced inactive interval was rejected because a stale
normal-status high could masquerade as the first P100 acknowledgement.

## Risks and follow-up

The 20 ms interval is an initial conservative firmware value, not bench
evidence. F-08 must verify U3 polarity, the controller input, and the fresh
ACK transition before any endpoint move or output enable. T-01H must prove M5
clearance and calibrate the raw force constants. A future RP23CNC feature must
wait with a finite timeout and alarm rather than assume GP27 is ready.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/`: status qualification and
  magnetic-protocol output arbitration.
- `firmware/README.md`: current firmware synchronization contract.
- `firmware/pen_pressure/README.md`: toolhead status and enable prerequisites.
- `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`: P100 coexistence rule.
- `docs/integration/INTERFACES.md`: GP27 ownership/interface contract.
- `docs/testing/TEST_PLAN.md`: F-08 acknowledgement-transition evidence.
