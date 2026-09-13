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

## Difficulties and corrective actions

- The existing documentation said `ULT` was sleep and `EEP` was fault. The
  owner-confirmed board image showed the opposite.
- Moving wires was rejected to avoid unnecessary toolhead disassembly.
- Firmware was changed to treat GP6/EEP as sleep and GP7/ULT as fault. The
  next retest must use the reflashed E07B sketch.

## Interpretation

The no-motion observation cannot yet qualify or reject the 1000 RPM motor.
The enable pin was driven on the wrong physical endpoint, so a corrected
driver-enable/fault mapping must be verified first.

## Decisions and next action

Reflash E07B once, with the pen clear and supply current limited to 0.20 A.
Run one guarded manual pulse, record movement/current/fault output, and update
E-14C before using automatic pressure/force tests. Related change:
[`HW-20260913-001`](../../changes/hardware/2026/2026-09-13-correct-drv8833-sleep-fault-mapping.md).
