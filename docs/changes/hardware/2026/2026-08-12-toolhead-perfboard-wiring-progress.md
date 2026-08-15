---
id: HW-20260812-002
date: 2026-08-12
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - docs/hardware/WIRING_TABLE.md
  - docs/testing/TEST_PLAN.md
  - docs/testing/RECOMMENDED_TEST_SEQUENCE.md
tags:
  - toolhead
  - drv8833
  - rp2350
  - power
  - testing
related:
  - HW-20260810-005
---

# Record Toolhead Perfboard Wiring Progress

## Summary

The Pro Micro's intended toolhead connections and all four DRV8833 logic pins
are physically wired. The DRV8833 and Pololu S7V8F5 now share one toolhead
perfboard. A two-pin JST position between them is reserved for the incoming
6 V twisted pair.

`OUT1` and `OUT2` are intentionally not wired until the 22 AWG twisted motor
pair arrives and open-loop direction testing can assign the motor lead order.

## Reason

The physical assembly has advanced beyond the prior planned harness state.
The current wiring record and safe test order needed to distinguish completed
physical work from unpowered and unverified electrical behavior.

## Implementation

- Marked GP4/GP5/GP6/GP7 DRV8833 logic connections as physically installed.
- Documented the shared toolhead perfboard and its pending two-pin 6 V input.
- Added E-14B: an unpowered continuity, rail-short, motor-output isolation,
  and PC817-ground-isolation check before connecting the 6 V pair.
- Placed E-14B immediately before first toolhead power in the recommended
  test sequence.

## Verification

Power-wire continuity and continuity of every currently wired Pro Micro logic
conductor passed. A 6 V bench supply at the toolhead JST delivered the correct
voltage to the DRV8833 and, through the S7V8F5, to the Pro Micro.
This is a local toolhead-power result, not a verification of the upstream
D36V50F6 or of motor behavior. E-14B and E-15A are partial; E-14, E-05, E-06,
E-15, and T-01 remain open.

## Struggles and rejected approaches

None. Motor wiring is deliberately deferred so its polarity is assigned from
the first safe direction test rather than guessed during assembly.

## Risks and follow-up

Confirm the actual JST pin order, 6 V wire polarity, DRV8833 silkscreen labels,
and all Pro Micro endpoint connections during E-14B. Do not attach the N20 or
apply 6 V until that inspection passes. The supplied Amazon link subsequently
identified the exact ACEIRMC module: `ULT` is its low-true sleep input and
`EEP` is its protection/fault output. The installed GP7→`ULT` and GP6→`EEP`
connections are correct; the firmware was corrected to match them. Inspect the
`J2` bridge and pass E-14C before attaching the motor.

## Files

- `docs/hardware/WIRING_TABLE.md`: current physical wiring status.
- `docs/hardware/BOM.md`: received/mounted toolhead part status.
- `docs/testing/TEST_PLAN.md`: new E-14B pre-power test.
- `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`: revised dependency order.
- `docs/project/ROADMAP.md`: phase-one test checklist.
