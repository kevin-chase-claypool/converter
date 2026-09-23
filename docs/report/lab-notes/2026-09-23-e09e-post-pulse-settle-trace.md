# Lab Note: 2026-09-23 - E-09E post-pulse settle trace

## Objective

Measure how long the installed toolhead's CS1238 filtered force signal actually
takes to settle after one 5 ms actuator pulse, so the integrated controller's
500 ms sensing settle can be replaced with a measured value.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A, gain 128, 640 SPS, internal reference off, installed pen clear of
  paper.
- Firmware: `e09e_cs1238_pen_scale_pulse` at commit `bf165f0`, using the
  `s` / `SETTLE` trace added in that commit.
- Interface: service UART1 GP20/GP21 at 115200 baud through the 3.3 V
  USB-to-TTL adapter with adapter VCC disconnected.

## Procedure

With the pen clear of paper, one `t` (64-sample clear tare), one `a` (arm), then
three consecutive `s` traces. Each trace issues exactly one bounded 5 ms DOWN
pulse and then streams the 16-sample filtered CS1238 value for 2500 ms at the
filter's natural ~25 ms cadence.

```text
TARE_MEAN_RAW,267126
SETTLE_REJECTED,reason=arm_required
TARE_MEAN_RAW,265824
ARMED,down_pulse_budget=30
```

The first `SETTLE_REJECTED,reason=arm_required` is expected: taking a tare
disarms the down-pulse budget, so `a` must follow every `t`.

All three traces reported `SETTLE_START,pulse_ms=5,fault_during_drive=0`.

## Results

Filtered value at the start of each trace, and the plateau statistics taken over
the 1000-2500 ms tail:

| Trace | First sample (≈22 ms) | Plateau mean | Tail peak-to-peak |
|---|---:|---:|---:|
| 1 | 234,496 | 247,823 | 299 |
| 2 | 234,924 | 249,611 | 443 |
| 3 | 236,665 | 234,910 | 692 |

Settling time to a given band around each trace's own plateau, defined as the
first sample after which every later sample stays inside the band:

| Trace | ±2,000 | ±1,000 | ±500 |
|---|---:|---:|---:|
| 1 | 120 ms | 218 ms | 342 ms |
| 2 | 171 ms | 220 ms | 343 ms |
| 3 | 220 ms | 294 ms | 934 ms |

Deviation from plateau over the first 200 ms:

| Time | Trace 1 | Trace 2 | Trace 3 |
|---:|---:|---:|---:|
| ≈22 ms | -13,327 | -14,687 | +1,755 |
| ≈47 ms | -10,443 | -10,532 | +1,029 |
| ≈72 ms | -9,455 | -9,730 | -8,539 |
| ≈96 ms | -4,839 | -4,887 | -8,138 |
| ≈121 ms | -1,419 | -1,722 | -5,955 |
| ≈146 ms | -1,757 | -2,520 | -4,280 |
| ≈170 ms | -487 | +306 | -1,832 |
| ≈195 ms | -1,345 | -1,711 | -2,249 |

First 200 ms of trace 1, verbatim:

```text
SETTLE,21,234496
SETTLE,46,237380
SETTLE,71,238368
SETTLE,95,242984
SETTLE,120,246404
SETTLE,145,246066
SETTLE,169,247336
SETTLE,194,246478
```

## Interpretation

The mechanical transient is large and fast: within the first ~25 ms the reading
is 13,000-15,000 raw away from its eventual plateau, and most of that is gone by
120 ms. After that the value wanders within a few hundred raw of the plateau.

The ±500 column is not usable as a criterion. Traces 2 and 3 have tail
peak-to-peak noise of 443 and 692 raw, so ±500 lies inside the noise floor and
those traces only "settle" at 343 ms and 934 ms by chance, not because the
signal moved. Taking the tail noise as the reference, a band of about twice the
worst noise — ±1,000 raw, roughly 0.2 g — is reached at 218, 220, and 294 ms.

Trace 3 is visibly different in shape. It starts near its plateau, dips about
8,500 raw at 72 ms, then recovers over ~250 ms. That is the stiction release
behaviour seen elsewhere on this mechanism, and it is why the settle is set
from the worst of three rather than the mean.

Trace 3 also drifts slowly after recovering — about 2,200 raw between 300 ms
and 2500 ms — which no practical fixed settle removes and which is well inside
the controller's decision margins.

## Decisions and next action

Set the integrated controller's sensing settle to 300 ms, which covers the worst
measured trace at roughly 1.5x its tail noise. See
[`reduce-settle-to-measured-300ms`](../../changes/rp23cnc-software/2026/2026-09-23-reduce-settle-to-measured-300ms.md).

This measurement is clear-air. Settle just above the paper, with the spring
compressed and the tip touching, could differ, so the M3/M5 cycle set must be
re-run after the change to confirm the first-touch reference spread and fault
rate do not worsen.

## References

- [Add a one-pulse settle trace to E-09E](../../changes/rp23cnc-software/2026/2026-09-23-add-e09e-settle-trace.md)
- [T-02 hysteresis-relief nine-cycle run](2026-09-23-t-02-hysteresis-relief-nine-cycle-run.md)
