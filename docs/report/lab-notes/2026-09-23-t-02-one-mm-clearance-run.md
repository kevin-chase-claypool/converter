# Lab Note: 2026-09-23 - T-02 one-millimetre clearance run

## Objective

Confirm that reducing the M5 clearance air gap from about 1.75 mm to about 1 mm
shortens the warm seek, and that the travel learning re-measures the smaller
gap.

## Configuration

- Hardware: SparkFun Pro Micro RP2350 toolhead, installed N20/DRV8833, CS1238
  channel A at 640 SPS, GP2 `LIFT_HOME` switch, installed pen over paper.
- Firmware: integrated `pro_micro_rp2350_toolhead` at commit `dd0ef18`
  ("Reduce the M5 clearance air gap to about 1 mm").
- Interface: service UART1 GP20/GP21 at 115200 baud; repeated `e` / `p` / `l`.

## Procedure

Cold start at GP2, then repeated `e` / `p` / `l` cycles.

## Results

Eight M3/M5 cycles completed with **no faults**. The capture also carries the
stale buffer from the previous session; the fresh run starts at the final
service-ready line.

| Cycle | Seek pulses | `warm_ema` after | Snapshot force | Rejects |
|---:|---:|---:|---:|---:|
| 1 (cold from GP2) | 34/100 | 0 | 151,791 | 0 |
| 2 (first warm) | 22/100 | 22 | 167,862 | 2 |
| 3 | 10/100 | 20 | 163,015 | 2 |
| 4 | 9/100 | 18 | 184,762 | 2 |
| 5 | 7/100 | 16 | 185,930 | 2 |
| 6 | 7/100 | 14 | 171,970 | 2 |
| 7 | 8/100 | 13 | 159,745 | 2 |
| 8 | 9/100 | 13 | 185,683 | 2 |

`cs1238_rejects` rose to 2 and stayed there, so the earlier reseat is holding
with only isolated glitches.

## Interpretation

The air-gap reduction is a clear win. Steady-state warm seek dropped from
13-16 pulses to 7-9, and the learned travel settled from about 20-24
fine-pulse-equivalents to about 13. At roughly 310 ms per pulse that is a warm
M3 of about 2.2-2.8 seconds instead of 4.0-5.0.

The first warm cycle re-measured at 22 pulses as designed, and `warm_ema`
converged to 13 rather than staying at the old value, confirming the moving
average tracks the new clearance rather than being anchored to the old one.

Held force still wanders across the run (159,745 to 185,930 raw, about 5.2 g),
unchanged by this parameter and still the open consistency question.

## Decisions and next action

Keep the 1 mm clearance. The remaining path to the under-2-second target is the
split settle and/or an open-loop transit, since the seek is now down to a
handful of pulses and the per-pulse 300 ms settle dominates what is left.

## References

- [T-02 in the test plan](../../testing/TEST_PLAN.md)
- [Reduce the M5 clearance air gap to about 1 mm](../../changes/rp23cnc-software/2026/2026-09-23-reduce-m5-clearance-air-gap.md)
