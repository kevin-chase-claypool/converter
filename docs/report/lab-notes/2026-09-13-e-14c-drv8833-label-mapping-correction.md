# Lab Note: 2026-09-13 - E-14C DRV8833 label-mapping correction

## Objective

Resolve the installed DRV8833 sleep/fault-label conflict without disassembling
or resoldering the toolhead, then prepare a guarded actuator retest.

## Configuration

- Hardware: installed ACEIRMC-style DRV8833 toolhead module and replacement
  1000 RPM N20.
- Wiring/pin map retained: GP4→IN1, GP5→IN2, GP6→EEP, ULT→GP7.
- Firmware to reflash: `e07b_hx711_actuator_steps` after this correction.
- Supply: 6 V toolhead rail; user observed 6 V at the driver.
- Instruments: Allosun multimeter and bench supply.

## Code, commands, and configuration used

```text
E07B prior service-UART commands: u, d, x, and a
Corrected electrical contract:
GP6 -> EEP / nSLEEP: HIGH enables; LOW sleeps
GP7 <- ULT / nFAULT: INPUT_PULLUP; LOW indicates fault
Pending safe logic-meter command after reflash: v
```

## Procedure

1. The owner confirmed the actual installed-module image: `SLEEP` is pin 1
   labelled `EEP`; `FAULT` is pin 6 labelled `ULT`.
2. Retained the existing GP6→EEP and ULT→GP7 wires.
3. Recorded the unsuccessful pre-correction E07B pulse observations and
   performed passive checks.
4. Corrected firmware mappings; powered retest is pending reflash.

## Results

- E07B reported valid HX711 telemetry and accepted actuator commands, but
  100 ms `u`/`d` pulses produced no observable N20 movement.
- Bench-supply display changed from about 0.024 A idle to 0.023 A during a
  pulse; that display is too slow to characterize a short pulse but did not
  show expected motor loading.
- The N20 ran when connected directly to 6 V. The driver rail measured 6 V.
- With power removed, OUT1-to-OUT2 measured about 31 ohm and continuity
  beeped. GP4→IN1, GP5→IN2, and GP7→ULT continuity were reported.
- The old firmware description was reversed relative to the owner-confirmed
  board labels. No E-14C pass is claimed until the corrected E07B build runs.
- After the corrected E07B reflash, non-motion `v` meter mode reported both
  stages and the owner measured GP4=3.3 V, GP5=0 V, and GP6/EEP=3.3 V, each
  relative to local DRV8833 ground. This passes the controller-side logic
  portion of E-14C; driver-output switching remains unverified.
- With both N20 leads disconnected, E07B `o` mode held each output polarity
  for 30 seconds. The owner reported all four expected readings: OUT1≈VM /
  OUT2≈0 V, then OUT1≈0 V / OUT2≈VM. The driver output stage passes.

## Difficulties and corrective actions

- The existing documentation said `ULT` was sleep and `EEP` was fault. The
  owner-confirmed board image showed the opposite.
- Moving wires was rejected to avoid unnecessary toolhead disassembly.
- Firmware was changed to treat GP6/EEP as sleep and GP7/ULT as fault. The
  next retest must use the reflashed E07B sketch.
- After the corrected E07B build still gave no audible motion from repeated
  100 ms UP pulses, a non-motion `v` meter mode was added. It holds GP4/GP5
  logic while asleep, then GP6/EEP enabled with both direction pins low.
- The isolated output test passed while the N20 previously ran direct from
  6 V. The remaining fault is therefore the physical N20 lead/OUT1/OUT2 path,
  which must be re-terminated or resoldered with power removed.

## Interpretation

The no-motion observation cannot yet qualify or reject the 1000 RPM motor.
The enable pin was driven on the wrong physical endpoint, so a corrected
driver-enable/fault mapping must be verified first.

## Decisions and next action

Temporarily isolate the motor from OUT1/OUT2, then measure a held driver-output
test. Do not hold a potentially stalled motor energized merely to accommodate a
slow multimeter. Related changes:
[`HW-20260913-001`](../../changes/hardware/2026/2026-09-13-correct-drv8833-sleep-fault-mapping.md).
and [`HW-20260913-002`](../../changes/hardware/2026/2026-09-13-add-nonmotion-drv8833-meter-mode.md).
With power removed, repair only the two N20 output connections, reconnect them,
and verify a single short `u` pulse before any automatic force test. The next
E07B build records ULT immediately after enable and during that short loaded
pulse, so retain the complete UART line.

Loaded repeat result: after the N20 was reconnected, a 100 ms UP pulse printed
`fault_during_drive=0 raw=1` and still produced no motion. Therefore ULT was
inactive throughout the actual command; E07B did not cancel the pulse and the
driver did not claim over-current/thermal protection. The next discriminator is
the supply/current capability required by the 1000 RPM motor, not another GPIO
or signal-wire change.

The 100 ms manual-pulse cap was then superseded for this replacement motor.
E07B now permits 100–1000 ms in 100 ms adjustments, while retaining a finite
one-second guard because LIFT_HOME remains report-only in this service sketch.

At the owner's request, a verbatim historical E-05 source copy from `03f6c00`
was prepared as an A/B reproduction. It must be treated as two automatic
500 ms motions, not as the guarded current E07B procedure.

To make that comparison controllable without changing the preserved source,
`e05_legacy_manual_steps` now uses the same historical roles with the 3.3 V
GP20/GP21 `Serial2` service adapter. It starts at 100 ms. Send `u` for the
historical first direction or `d` for reverse; send `]` before the next pulse
to increase by 100 ms, up to 1000 ms (`[` decreases). It never automatically
reverses. Clear travel in the selected direction remains mandatory because
LIFT_HOME is not used as a motion stop in this diagnostic. A movement result
still cannot prove GP7 is physical sleep: GP6 `INPUT_PULLUP` can itself leave
the confirmed EEP sleep input high.

## Final root cause and verified repair

The owner found a DRV8833 pin that was not soldered to the board. With power
removed, the joint was reflowed and inspected. No wire, connector, or GPIO
mapping was changed. After the repair, the corrected E07B sketch moved the
installed N20 in both `u` and `d` directions. This closes the loaded
OUT1/OUT2 delivery fault: the prior static-output test was a false assurance
because the bridge could present open-circuit voltage despite the defective
loaded output connection.
