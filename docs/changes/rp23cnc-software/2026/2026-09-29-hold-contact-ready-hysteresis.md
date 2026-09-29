---
id: RPSW-20260929-001
date: 2026-09-29
category: rp23cnc-software
affected_categories:
  - rp23cnc-software
status: implemented
components:
  - firmware/pen_pressure/pro_micro_rp2350_toolhead
tags:
  - toolhead
  - gp27
  - contact-ready
  - handshake
  - p115
  - f-05a
related:
  - RPSW-20260925-007
  - ADR-007
---

# Hold the published contact-ready level through hold corrections

## Summary

The toolhead now releases its published contact-ready level only after the
filtered force has stayed outside the urgent-relief bound for 500 ms. A single
out-of-band conversion or a normal hold correction can no longer drop the
level. GP27/`PRB` therefore stays asserted for the whole `HOLD_FORCE` period,
which is the contract `P115 Q1` depends on.

## Reason

On 2026-09-29 the controller's status stream showed `Pn:P` toggling in
`HOLD_FORCE` while an M3-held pen sat stationary at `MPos:0,0,0,0`. `P` is the
probe input, driven by GP27 through U3, so the pen-transition line was
alternating between asserted and released even though the toolhead was in a
stable state. The same trace showed `Pn:P` steady after `M5`.

The cause is structural. `STATUS_CONTACT_READY` is published from
`contact_ready_windows_`, which asserted after three filtered conversions -
about 4.7 ms at 640 SPS with the 16-sample average - but reset to zero on any
single conversion outside the ±15 g ready band. The hold loop that corrects an
excursion moves on a 250 ms cadence, roughly 50x slower than the flag's
release path, so any excursion near the band edge made the published level
chatter. The interface contract is explicit that the only LOW is the
seek/lift transition.

## Implementation

- `toolhead_config.h`: added `CONTACT_READY_RELEASE_TOLERANCE_RAW` (the
  existing `HOLD_URGENT_RELIEF_RAW`, 20 g) and `CONTACT_READY_LOST_MS`
  (500 ms, two hold-correction cadences) as an explicitly supervised bench
  value tied to F-05A.
- `pressure_controller.cpp` / `pressure_controller.h`:
  `updateReadyState()` now keeps an established ready state while the force
  stays inside the wider release band and releases it only after a sustained
  excursion beyond that band. The assert side is unchanged. Leaving
  `HOLD_FORCE`, faults, driver faults, and sensor loss still clear the state
  immediately, and the hard-force guard is untouched.

## Verification

- `arduino-cli compile --fqbn rp2040:rp2040:sparkfun_promicrorp2350
  firmware\pen_pressure\pro_micro_rp2350_toolhead` builds cleanly (82,600
  bytes flash, 16,236 bytes RAM).

**Not verified:** nothing has run on the toolhead. The bench must repeat the
`M3` + `Pn:` observation and confirm a steady `Pn:P` and
`ready=[contact:1 ...]` through `HOLD_FORCE`.

## Struggles and rejected approaches

- Making `CONTACT_READY` purely state-based (assert whenever `HOLD_FORCE` and
  force was ever acquired) was rejected: the interface describes the bit as
  "contact force is stable", so it has to keep tracking the force rather than
  only the state machine.
- Widening the assert band again was rejected. It was already widened from
  ±5 g to ±10 g to ±15 g for friction drift; the defect is the single-sample
  release, not the band width.
- Blaming the GP29 command input was rejected: Core 0 reads the same pin, so a
  dithering command would have been visible as seek/lift cycling, not a
  stationary hold.

## Risks and follow-up

- If the bench still shows `Pn:P` toggling with `ready=[contact:1 ...]`
  steady, the remaining cause is the GP27 -> PC817C U3 -> `PRB` electrical
  path (for example a marginal opto drive or motor-noise coupling) and is not
  firmware-fixable.
- `CONTACT_READY_LOST_MS = 500` is a supervised bench value, not an accepted
  tuning result. F-05A must confirm that a genuinely lost hold still releases
  the level and that a normal correction cycle never does.

## Files

- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`: release
  band and release window constants.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.cpp`:
  hysteretic `updateReadyState()`.
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/pressure_controller.h`:
  release timestamp state.
- `firmware/pen_pressure/README.md`,
  `firmware/pen_pressure/CONTROL_STRATEGY.md`, `firmware/README.md`,
  `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`: current-state
  and contract documentation.
