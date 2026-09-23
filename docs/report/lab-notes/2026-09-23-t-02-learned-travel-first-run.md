# Lab Note: 2026-09-23 - T-02 learned-travel first run

## Objective

First bench run of the warm-seek travel learning: confirm the measuring pass
seeds the moving average and that later warm M3s traverse the learned distance
with coarse pulses.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper.
- Firmware: integrated `pro_micro_rp2350_toolhead` at commit `ceed019`
  ("Learn warm-seek travel to traverse it with coarse pulses").
- Interface: service UART1 GP20/GP21 at 115200 baud; `?` then `p`, then
  repeated `e` / `p` / `l`.

## Procedure

Cold start at GP2, `p` snapshot, then `e` for the first M3. Each further cycle
was one `l` and one `e`, with a `p` snapshot at `HOLD_FORCE`.

## Results

Six M3/M5 cycles completed with **no faults**.

| Cycle | M3 entry force | Seek pulses | `warm_ema` after | Snapshot force | Relief |
|---:|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | — | 76/100 | 0 | 164,589 | 0 / 0 ms |
| 2 (first warm) | 5,316 | 24/100 | 24 | 189,946 | 1 / 25 ms |
| 3 | 4,877 | **13/100** | 22 | 161,953 | 1 / 25 ms |
| 4 | 6,516 | **27/100** | 23 | 167,318 | 8 / 181 ms |
| 5 | 4,639 | **14/100** | 21 | 151,320 | 13 / 285 ms |
| 6 | 4,340 | **14/100** | 20 | 152,283 | 16 / 345 ms |

`cs1238_rejects` reached 1 and stayed there. M5 clear returned within 604 to
1,770 raw of the clear tare on every cycle.

## Difficulties and corrective actions

The learning works: cycle 2 measured 24 fine pulses, and cycles 3, 5 and 6 then
completed in 13-14 pulses by using the learned coarse travel. That is roughly a
45% reduction in warm-seek pulses.

Cycle 4 is the exception at 27 pulses, and the entry-force column explains it.
The M5 clear residual varied from 4,340 to 6,516 raw across the run, and the
coarse phase was gated on the shared 1 g threshold of 5,039 raw. Cycles 3, 5
and 6 entered below that gate and used coarse travel; cycle 4 entered at 6,516,
above it, so the coarse phase was skipped entirely and the seek reverted to
fine-only.

Corrective action: give the warm coarse phase its own 3 g force gate, clear of
the observed residual band. See
[`widen-warm-coarse-force-gate`](../../changes/rp23cnc-software/2026/2026-09-23-widen-warm-coarse-force-gate.md).

## Interpretation

The measured-then-learn approach behaves as designed. `warm_ema` seeds at the
measured 24 fine-pulse-equivalents and settles into the low 20s as later cycles
fold in their own travel, which is the expected small drift correction.

The residual risk this run did not exercise is the coarse pulse landing on
paper. The 8-pulse reserve and the budget cap held every cycle, and no cycle
approached the 60 g guard.

Held force still shows the downward drift seen in the previous single-descend
run (189,946 down to 152,283 raw), with the relief count climbing to 16
activations. That behaviour is unchanged by this feature and remains open.

## Decisions and next action

Reflash with the wider warm coarse gate and repeat the cycle set. Expected:
every warm cycle uses the coarse phase, so the pulse count stays near 13-14
regardless of the residual, and only the first warm cycle after boot is slow.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [Learn warm-seek travel to traverse it with coarse pulses](../../changes/rp23cnc-software/2026/2026-09-23-learn-warm-seek-travel.md)
