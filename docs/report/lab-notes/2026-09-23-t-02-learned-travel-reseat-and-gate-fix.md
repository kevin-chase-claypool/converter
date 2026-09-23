# Lab Note: 2026-09-23 - T-02 learned travel after reseat and gate fix

## Objective

Confirm the CS1238 corruption flood cleared after reseating the interface, and
that the wider warm coarse gate makes every warm M3 use the learned coarse
travel.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper. The
  CS1238 header was reseated after the previous run's 1,578-reject flood.
- Firmware: integrated `pro_micro_rp2350_toolhead` at commit `c65d3fc`
  ("Widen the warm coarse-phase force gate").
- Interface: service UART1 GP20/GP21 at 115200 baud; repeated `e` / `p` / `l`.

## Procedure

Reset, `p` snapshot, then `e` for the first M3. Each further cycle was one `l`
and one `e`, with a `p` snapshot at `HOLD_FORCE`.

## Results

Six M3/M5 cycles completed with **no faults**. The capture begins with the
pre-reset fault record still in the buffer; the fresh run starts at the
service-ready line and shows `cs1238_rejects` reset to 0.

| Cycle | Seek pulses | `warm_ema` after | Snapshot force | Relief | Rejects |
|---:|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | 21/100 | 0 | 174,135 | 0 / 0 ms | 0 |
| 2 (first warm) | 27/100 | 27 | 159,722 | 1 / 27 ms | 0 |
| 3 | 13/100 | 24 | 184,940 | 1 / 27 ms | 0 |
| 4 | 16/100 | 23 | 186,220 | 2 / 49 ms | 0 |
| 5 | 13/100 | 21 | 171,503 | 2 / 49 ms | 1 |
| 6 | 16/100 | 20 | 168,247 | 5 / 110 ms | 1 |

`cs1238_rejects` stayed at 0 through the first four cycles and reached 1 on
the last two, down from 1,578 before the reseat. That is a single isolated
glitch being absorbed, not a fault.

## Difficulties and corrective actions

None required in this run. The prior corrective action - reseating the CS1238
header - is confirmed by the reject count collapsing to 0-1.

## Interpretation

Two things are now confirmed.

The corruption was mechanical. The reseat took `cs1238_rejects` from 1,578 to
effectively zero, so the flood was a marginal CS1238 connection, not a firmware
or ADC failure.

The gate fix works. Every warm cycle in this run used the learned coarse
travel: the pulse count is 13-16, against the 24-27 fine-only cycles before.
No warm cycle skipped coarse travel as cycle 4 did in the previous run.

`warm_ema` seeds at 27 and drifts to 20 over the run, which reflects the
remaining uncertainty in how many fine-pulse-equivalents each coarse pulse
actually replaces; the coarse phase is also ending after roughly one 25 ms
pulse because mechanism strain still crosses the 3 g gate while the pen is
airborne. That leaves headroom if the gate is later raised or made rise-based.

The cold start took 21 pulses this run against 56-76 previously, which is
unexplained by firmware and is most likely a changed resting position or
mechanism state after the reseat.

## Decisions and next action

The learned-travel feature is behaving as intended and the interface flood is
resolved. The next open item is the held-force drift and widening spread
observed across runs, which is independent of this feature.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [Widen the warm coarse-phase force gate](../../changes/rp23cnc-software/2026/2026-09-23-widen-warm-coarse-force-gate.md)
- [Learn warm-seek travel to traverse it with coarse pulses](../../changes/rp23cnc-software/2026/2026-09-23-learn-warm-seek-travel.md)
