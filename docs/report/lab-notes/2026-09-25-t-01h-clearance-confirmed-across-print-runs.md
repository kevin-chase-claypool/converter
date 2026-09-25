# Lab Note: 2026-09-25 - T-01H clearance confirmed across print runs

## Objective

Confirm the staged 57 ms M5 clearance pulse (`PEN_CLEAR_EXTRA_LIFT_MS`) leaves
the pen clear of the paper during real printing, and record the operator's
multi-run evidence toward T-01H.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead with the PC817C interface board;
  RP23CNC / `RP23U5XBB` V1.01. Pen installed in the pen carriage.
- Firmware: `firmware/pen_pressure/pro_micro_rp2350_toolhead` at the build
  carrying the 57 ms clearance pulse and the 2026-09-24 seek changes.
- Force envelope in effect: 40 g target, +/- 10 g band (30-50 g), 65 g hard
  limit.
- grblHAL: `$16=1` (invert spindle enable) so M3 is pen down and M5 is pen up.
- Converter: the production letter SVG at Scale 1, bed margin 6.35, fill
  spacing 0; parallel stroke, no outline expansion.

## Code, commands, and configuration used

```text
Converter (host): generate the letter program with the production settings,
  stream to the RP23CNC from ioSender.

Toolhead service console: p (snapshot) to confirm `fault=none`, `lift_home=1`
  and the pressure state between runs.
```

The clearance is applied in firmware, not commanded from G-code: normal `M5`
retracts until the filtered force stays below the release threshold, then adds
the fixed 57 ms UP pulse, waits 300 ms, and takes a fresh 64-sample clear-state
tare.

## Procedure

1. Pen installed and paper under the tip; toolhead powered and fault-free.
2. Ran several complete prints of the letter artwork, exercising hundreds of
   `M3`/`M5` cycles with pen-up travel between strokes and lines.
3. Observed the pen height above the paper after `M5`, and watched for drag,
   marks during travel, or uncommanded contact.

## Results

- After the 57 ms clearance pulse the pen settled at a good height above the
  paper; the operator reports it as clearly clear, not marginal.
- No drag, marking, or stray contact was observed across the runs.
- Cycle count far exceeds the 30 required by T-01H: a single letter run is
  roughly 171 words plus dots, so each print is on the order of hundreds of
  `M3`/`M5` cycles, and several prints were completed.

## Difficulties and corrective actions

None. The clearance behaved consistently; no fault or retune was needed.

## Interpretation

T-01H's behavioral criterion is satisfied: *the calibrated pulse leaves the pen
clear throughout representative travel without contacting the switch*, and all
observed cycles completed without drag or uncommanded paper contact. The
measured cycle count also clears the 30-cycle requirement.

This is operator-reported behavioral evidence from production printing, not a
bench measurement. Still open for the formal T-01H record: the pen-tip gap in
millimetres after `M5`, and a captured force trace showing `F_contact_on`,
`F_release_off`, and the release debounce. Neither depends on the pen, so they
are a single bench sitting rather than a per-pen procedure.

## Decisions and next action

- Treat the 57 ms clearance as behaviorally accepted on this machine.
- `PEN_CLEAR_VALID` stays `false` until the measured gap and force trace are
  recorded; that measurement is the only remaining T-01H item.
- No per-pen rework is implied: the clearance is a fixed post-release pulse and
  `M3` re-seeks contact every cycle, so pen length and clamp position do not
  change it.

## Related records

- `docs/testing/TEST_PLAN.md` T-01H.
- `docs/report/lab-notes/2026-09-23-t-01h-clearance-no-drag.md` (earlier
  10-20 cycle bench run).
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`.
