# Lab Note: 2026-08-19 - E-01 Stepper Coil-Pair Test

## Objective

Identify the two coil pairs on each STEPPERONLINE 17HS15-1504S-X1 and record
the special Y shielded-cable conductor mapping before driver connection.

## Configuration

- Hardware revisions: X, Y, and A STEPPERONLINE 17HS15-1504S-X1 motors; Y has
  an installed shielded 4-conductor cable (Amazon ASIN B0DL9QCH1B).
- Wiring/pin map: motor black/green coil continues through cable black/green;
  motor red/blue coil continues through cable red/white. Cable white is spliced
  to motor blue.
- Firmware commit/build: none; motor and driver were unpowered.
- grblHAL settings: none.
- Converter settings/sample: none.
- Instruments: owner-reported hand-turn generated-voltage test; meter model and
  voltage readings were not recorded.

## Code, commands, and configuration used

```text
No firmware, command, or controller configuration was used.
```

## Procedure

1. With each motor unpowered and disconnected from its driver, the owner turned
   it by hand while checking which lead pairs generated voltage.
2. The resulting lead groups were recorded; for Y, the already-installed
   shielded-cable color pairs were recorded too.

## Results

- On X, Y, and A, motor black and green generated voltage together, identifying
  one coil; motor red and blue generated voltage together, identifying the
  other coil.
- The Y shielded cable preserves those groups as black/green and red/white:
  cable white is the splice continuation of motor blue.

This is a partial E-01 pass for coil grouping only. No winding resistance,
individual generated voltage, driver terminal, or rotation-direction result was
recorded.

## Difficulties and corrective actions

None encountered. The initially generic all-axis cable record was insufficient
for this motor because its installed shielded cable uses white rather than blue
for the second coil's cable-side lead. The master wiring table now records that
specific splice.

## Interpretation

The Y motor can be connected only with each identified pair kept on its own
TB6600 phase: cable black/green on Phase A and cable red/white on Phase B. The
polarity selected in the wiring table retains the motor's manufacturer order;
swap one entire phase pair only if later low-speed motion tests show the desired
Y direction is reversed.

## Decisions and next action

Use the recorded Y cable-to-motor splice mapping in
[`../../hardware/WIRING_TABLE.md`](../../hardware/WIRING_TABLE.md) rows
`YPH-001` through `YPH-004`. Measure winding resistance, then set the TB6600
current/microstep switches unpowered before M-01.

Related change note: `HW-20260819-001`.
