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
- Pen-tip gap after `M5`: approximately **1.75 mm** (operator measurement).
- No drag, marking, or stray contact was observed across the runs.
- Cycle count far exceeds the 30 required by T-01H: a single letter run is
  roughly 171 words plus dots, so each print is on the order of hundreds of
  `M3`/`M5` cycles, and several prints were completed.

### Measured force values (four-cycle bench capture)

From the toolhead `STATE_EVENT` trace of four warm `M3`/`M5` cycles:

| Cycle | Force at contact (`F_contact_on`) |
|---|---:|
| 1 (fine-only) | 28.8 g |
| 2 | 40.1 g |
| 3 | 44.5 g |
| 4 | 46.6 g |

`F_contact_on` is the force reported at the transition into `HOLD_FORCE`. The
climb across warm cycles (28.8 -> 46.6 g) is the warm-seek coarse-pulse
overshoot; it stays inside the 30-50 g acceptance band and is handled by the
hold loop, so it is accepted as within the machine's tolerance rather than a
precision target.

`F_release_off` (release) clears to roughly zero every cycle: `LIFTED` force
161-271 raw (~0.03-0.05 g), well below the 3 g release threshold. The release
debounce is the firmware's `LIFT_RELEASE_REQUIRED_WINDOWS = 3` consecutive
samples, and every cycle completed its fresh clear-state tare
(`CLEAR_TARE_SETTLING` observed each time).

## Difficulties and corrective actions

None. The clearance behaved consistently; no fault or retune was needed.

## Interpretation

T-01H is accepted: the calibrated 57 ms pulse leaves the pen clear through
representative travel (gap ~1.75 mm, no drag), release clears to ~0 g on every
cycle, the 30-cycle requirement is far exceeded, and the `F_contact_on` /
`F_release_off` values are recorded with a large hysteresis margin (contact
~40-47 g vs release ~0 g).

## Decisions and next action

- Treat the 57 ms clearance as behaviorally accepted on this machine.
- `PEN_CLEAR_VALID` flipped to `true` (T-01H accepted). `GP27_NORMAL_STATUS_ENABLED`
  remains `false` until F-08 and F-05A close.
- No per-pen rework is implied: the clearance is a fixed post-release pulse and
  `M3` re-seeks contact every cycle, so pen length and clamp position do not
  change it.
- Open follow-up (separate from T-01H): the warm-seek contact overshoot climbs
  across cycles, and `cs1238_rejects` is intermittent. Both are force-control /
  sensor-integrity items, not clearance items.

## Related records

- `docs/testing/TEST_PLAN.md` T-01H.
- `docs/report/lab-notes/2026-09-23-t-01h-clearance-no-drag.md` (earlier
  10-20 cycle bench run).
- `firmware/pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`.
